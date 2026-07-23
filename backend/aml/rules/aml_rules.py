"""
AML Rule Engine
Implements configurable rules for detecting suspicious transactions
"""
import logging
import pytz
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncDay

from aml.models import Rule, Transaction, Customer, Device, Merchant

logger = logging.getLogger('aml')


class RuleEngine:
    """
    Main rule engine for evaluating AML rules against transactions
    """
    
    def __init__(self):
        self.active_rules = None
        self._load_rules()
    
    def _load_rules(self):
        """Load active rules from database"""
        self.active_rules = Rule.objects.filter(status='ACTIVE').order_by('priority')
        logger.info(f"Loaded {self.active_rules.count()} active rules")
    
    def evaluate_transaction(self, transaction: Transaction) -> Tuple[List[Rule], List[str], Decimal]:
        """
        Evaluate a transaction against all active rules
        
        Returns:
            Tuple of (triggered_rules, reasons, total_risk_score)
        """
        triggered_rules = []
        reasons = []
        total_risk_score = Decimal('0.0')
        
        if not self.active_rules.exists():
            logger.warning("No active rules found")
            return triggered_rules, reasons, total_risk_score
        
        for rule in self.active_rules:
            try:
                result = self._evaluate_rule(rule, transaction)
                if result['triggered']:
                    triggered_rules.append(rule)
                    reasons.append(result['reason'])
                    # Add weighted risk score
                    rule_risk = Decimal(str(result.get('risk_score', 0))) * rule.risk_weight
                    total_risk_score += rule_risk
                    logger.info(f"Rule '{rule.name}' triggered for transaction {transaction.transaction_id}")
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
                continue
        
        return triggered_rules, reasons, total_risk_score
    
    def _evaluate_rule(self, rule: Rule, transaction: Transaction) -> Dict:
        """
        Evaluate a single rule against a transaction
        
        Returns:
            Dict with 'triggered', 'reason', and 'risk_score'
        """
        rule_type = rule.rule_type
        config = rule.configuration
        
        if rule_type == 'THRESHOLD':
            return self._evaluate_threshold_rule(rule, transaction, config)
        elif rule_type == 'PATTERN':
            return self._evaluate_pattern_rule(rule, transaction, config)
        elif rule_type == 'BEHAVIORAL':
            return self._evaluate_behavioral_rule(rule, transaction, config)
        elif rule_type == 'GEOGRAPHIC':
            return self._evaluate_geographic_rule(rule, transaction, config)
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return {'triggered': False, 'reason': '', 'risk_score': 0}
    
    def _evaluate_threshold_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate threshold-based rules (amount, frequency, etc.)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        # Amount threshold
        if 'amount_threshold' in config:
            threshold = Decimal(str(config['amount_threshold']))
            if transaction.amount >= threshold:
                triggered = True
                reason = f"Transaction amount {transaction.amount} exceeds threshold {threshold}"
                risk_score = min(100, float(transaction.amount / threshold) * 50)
        
        # Daily transaction count threshold
        if 'daily_count_threshold' in config:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = Transaction.objects.filter(
                customer=transaction.customer,
                transaction_date__gte=today_start,
                status='COMPLETED'
            ).count()
            
            if today_count >= config['daily_count_threshold']:
                triggered = True
                reason = f"Daily transaction count {today_count} exceeds threshold {config['daily_count_threshold']}"
                risk_score = max(risk_score, min(100, (today_count / config['daily_count_threshold']) * 60))
        
        # Daily amount threshold
        if 'daily_amount_threshold' in config:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_total = Transaction.objects.filter(
                customer=transaction.customer,
                transaction_date__gte=today_start,
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            threshold = Decimal(str(config['daily_amount_threshold']))
            if today_total >= threshold:
                triggered = True
                reason = f"Daily transaction amount {today_total} exceeds threshold {threshold}"
                risk_score = max(risk_score, min(100, float(today_total / threshold) * 50))
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def _evaluate_pattern_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate pattern-based rules (structuring, layering, etc.)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        # Structuring detection (multiple transactions just below threshold)
        if 'structuring_threshold' in config:
            threshold = Decimal(str(config['structuring_threshold']))
            # Check if transaction is just below threshold
            if threshold * Decimal('0.9') <= transaction.amount < threshold:
                # Check for multiple similar transactions
                lookback_days = config.get('lookback_days', 7)
                lookback_date = timezone.now() - timedelta(days=lookback_days)
                
                similar_transactions = Transaction.objects.filter(
                    customer=transaction.customer,
                    transaction_date__gte=lookback_date,
                    amount__gte=threshold * Decimal('0.9'),
                    amount__lt=threshold,
                    status='COMPLETED'
                ).count()
                
                if similar_transactions >= config.get('structuring_count', 3):
                    triggered = True
                    reason = f"Potential structuring: {similar_transactions} transactions just below threshold"
                    risk_score = min(100, similar_transactions * 20)
        
        # Rapid successive transactions (layering)
        if 'rapid_transaction_threshold' in config:
            minutes_threshold = config.get('rapid_transaction_minutes', 10)
            count_threshold = config.get('rapid_transaction_count', 5)
            
            time_threshold = timezone.now() - timedelta(minutes=minutes_threshold)
            recent_count = Transaction.objects.filter(
                customer=transaction.customer,
                transaction_date__gte=time_threshold,
                status='COMPLETED'
            ).count()
            
            if recent_count >= count_threshold:
                triggered = True
                reason = f"Rapid transactions: {recent_count} transactions in {minutes_threshold} minutes"
                risk_score = min(100, recent_count * 15)
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def _evaluate_behavioral_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate behavioral rules (sudden behavior changes)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        customer = transaction.customer
        
        # Check for sudden increase in transaction amount
        if 'amount_increase_threshold' in config:
            # Get average transaction amount in last 30 days
            lookback_days = config.get('lookback_days', 30)
            lookback_date = timezone.now() - timedelta(days=lookback_days)
            
            avg_amount = Transaction.objects.filter(
                customer=customer,
                transaction_date__gte=lookback_date,
                transaction_date__lt=transaction.transaction_date,
                status='COMPLETED'
            ).aggregate(avg=Avg('amount'))['avg']
            
            if avg_amount:
                increase_ratio = float(transaction.amount / avg_amount)
                threshold_ratio = config.get('amount_increase_threshold', 3.0)
                
                if increase_ratio >= threshold_ratio:
                    triggered = True
                    reason = f"Sudden amount increase: {transaction.amount} vs avg {avg_amount:.2f} ({increase_ratio:.2f}x)"
                    risk_score = min(100, increase_ratio * 20)
        
        # Check for change in transaction pattern
        if 'pattern_change_detection' in config and config['pattern_change_detection']:
            # Compare last 7 days vs previous 7 days
            now = transaction.transaction_date
            recent_start = now - timedelta(days=7)
            previous_start = recent_start - timedelta(days=7)
            
            recent_count = Transaction.objects.filter(
                customer=customer,
                transaction_date__gte=recent_start,
                transaction_date__lt=now,
                status='COMPLETED'
            ).count()
            
            previous_count = Transaction.objects.filter(
                customer=customer,
                transaction_date__gte=previous_start,
                transaction_date__lt=recent_start,
                status='COMPLETED'
            ).count()
            
            if previous_count > 0:
                change_ratio = recent_count / previous_count
                if change_ratio >= config.get('pattern_change_threshold', 2.0):
                    triggered = True
                    reason = f"Transaction pattern change: {recent_count} vs {previous_count} transactions"
                    risk_score = max(risk_score, min(100, change_ratio * 25))
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def _evaluate_geographic_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Evaluate geographic-based rules (high-risk countries, etc.)
        """
        triggered = False
        reason = ""
        risk_score = 0
        
        # High-risk countries
        high_risk_countries = config.get('high_risk_countries', [])
        if transaction.receiver_country in high_risk_countries:
            triggered = True
            reason = f"Transaction to high-risk country: {transaction.receiver_country}"
            risk_score = 70
        
        # Cross-border transaction threshold
        if 'cross_border_threshold' in config and transaction.receiver_country:
            if transaction.customer.country != transaction.receiver_country:
                threshold = Decimal(str(config['cross_border_threshold']))
                if transaction.amount >= threshold:
                    triggered = True
                    reason = f"Large cross-border transaction: {transaction.amount} from {transaction.customer.country} to {transaction.receiver_country}"
                    risk_score = max(risk_score, min(100, float(transaction.amount / threshold) * 40))
        
        return {
            'triggered': triggered,
            'reason': reason,
            'risk_score': risk_score
        }
    
    def reload_rules(self):
        """Reload rules from database"""
        self._load_rules()
        logger.info("Rules reloaded")


# Singleton instance
_rule_engine_instance = None

def get_rule_engine() -> RuleEngine:
    """Get singleton instance of RuleEngine"""
    global _rule_engine_instance
    if _rule_engine_instance is None:
        _rule_engine_instance = RuleEngine()
    return _rule_engine_instance



# ─────────────────────────────────────────────────────────────────────────────
# Issues #22-27: Additional AML Detection Rules for Iranian Market
# ─────────────────────────────────────────────────────────────────────────────

IRAN_HIGH_RISK_COUNTRIES = [
    'KP', 'MM', 'AF', 'YE', 'SD', 'SS', 'SY', 'SO', 'LY', 'CD', 'CF', 'ML', 'HT', 'PK', 'VU',
]

# Countries under UN/FATF sanctions that Iran's FIU monitors for cross-border transactions
IRAN_SANCTIONED_COUNTRIES = ['KP', 'SD', 'SY', 'SO', 'LY']


class ExtendedRuleEngine(RuleEngine):
    """
    Extends the base RuleEngine with additional rules tailored for the Iranian market.
    Issues #22 (behavioral velocity), #23 (PEP), #24 (concentration), #25 (velocity),
    #26 (rapid movement), #27 (cross-border with sanctioned countries).
    """

    def _evaluate_rule(self, rule: Rule, transaction: Transaction) -> Dict:
        """Extended rule evaluation with extra rule types."""
        if rule.rule_type == 'PEP':
            return self._evaluate_pep_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'VELOCITY':
            return self._evaluate_velocity_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'CONCENTRATION':
            return self._evaluate_concentration_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'SANCTIONED':
            return self._evaluate_sanctioned_country_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'NIGHT_WEEKEND':
            return self._evaluate_night_weekend_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'ROUND_AMOUNT':
            return self._evaluate_round_amount_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'NEW_ACCOUNT':
            return self._evaluate_new_account_velocity_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'DEVICE_SHARING':
            return self._evaluate_device_sharing_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'MERCHANT_ABUSE':
            return self._evaluate_merchant_abuse_rule(rule, transaction, rule.configuration)
        elif rule.rule_type == 'BNPL_RISK':
            return self._evaluate_bnpl_risk_rule(rule, transaction, rule.configuration)
        return super()._evaluate_rule(rule, transaction)

    # ── Issue #23: PEP Rule ──────────────────────────────────────────────────
    def _evaluate_pep_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Flag transactions from/to Politically Exposed Persons (PEP).
        Iranian AML law requires enhanced due diligence for PEPs.
        """
        triggered = False
        reason = ""
        risk_score = 0

        customer = transaction.customer
        is_pep = getattr(customer, 'is_pep', False)

        if is_pep:
            amount_threshold = Decimal(str(config.get('pep_amount_threshold', 50_000_000)))
            if transaction.amount >= amount_threshold:
                triggered = True
                reason = (
                    f"PEP customer ({customer.customer_id}) with high-value transaction: "
                    f"{transaction.amount:,.0f} IRR"
                )
                risk_score = 85
            else:
                triggered = True
                reason = f"Transaction from PEP customer: {customer.customer_id}"
                risk_score = 60

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Issue #25: Velocity Rule ─────────────────────────────────────────────
    def _evaluate_velocity_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Detect velocity anomalies: unusually high number of transactions
        in a rolling window compared to the customer's historical baseline.
        """
        triggered = False
        reason = ""
        risk_score = 0

        window_hours = config.get('window_hours', 24)
        count_threshold = config.get('count_threshold', 15)
        amount_threshold = Decimal(str(config.get('amount_threshold', 0)))

        lookback = timezone.now() - timedelta(hours=window_hours)
        recent_txns = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=lookback,
            status='COMPLETED',
        )
        count = recent_txns.count()
        total_amount = recent_txns.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if count >= count_threshold:
            triggered = True
            reason = f"Velocity: {count} transactions in {window_hours}h window (threshold: {count_threshold})"
            risk_score = min(100, int(count / count_threshold * 60))

        if amount_threshold > 0 and total_amount >= amount_threshold:
            triggered = True
            reason = (reason + " | " if reason else "") + (
                f"Velocity amount: {total_amount:,.0f} IRR in {window_hours}h "
                f"(threshold: {amount_threshold:,.0f})"
            )
            risk_score = max(risk_score, min(100, int(float(total_amount / amount_threshold) * 55)))

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Issue #24: Concentration Rule ────────────────────────────────────────
    def _evaluate_concentration_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Detect fund concentration: a single counterparty receiving a large
        portion of a customer's total outflow — potential money mule pattern.
        """
        triggered = False
        reason = ""
        risk_score = 0

        lookback_days = config.get('lookback_days', 30)
        concentration_ratio = config.get('concentration_ratio', 0.7)  # 70%
        min_total_amount = Decimal(str(config.get('min_total_amount', 10_000_000)))

        lookback = timezone.now() - timedelta(days=lookback_days)
        customer_total = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=lookback,
            status='COMPLETED',
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if customer_total < min_total_amount:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        # Amount going to the same receiver account
        receiver = transaction.receiver_account
        if not receiver:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        receiver_total = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=lookback,
            receiver_account=receiver,
            status='COMPLETED',
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        receiver_total += transaction.amount

        if customer_total > 0:
            ratio = float(receiver_total / customer_total)
            if ratio >= concentration_ratio:
                triggered = True
                reason = (
                    f"Fund concentration: {ratio:.0%} of outflow "
                    f"({receiver_total:,.0f} / {customer_total:,.0f} IRR) "
                    f"to single account {receiver}"
                )
                risk_score = min(100, int(ratio * 90))

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Issue #27: Cross-border with Sanctioned Countries ────────────────────
    def _evaluate_sanctioned_country_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Flag any transaction — regardless of amount — where the receiving country
        is on the UN/FATF sanction list. Issue #27.
        """
        triggered = False
        reason = ""
        risk_score = 0

        sanctioned = config.get('sanctioned_countries', IRAN_SANCTIONED_COUNTRIES)
        if transaction.receiver_country in sanctioned:
            triggered = True
            reason = (
                f"Transaction to sanctioned country: {transaction.receiver_country} "
                f"(amount: {transaction.amount:,.0f} IRR)"
            )
            risk_score = 95  # Near-maximum — must escalate

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}


    # ── Issue #23: Night/Weekend Activity Detection ──────────────────────────
    def _evaluate_night_weekend_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Issue #23: Detect transactions during unusual hours (night) or weekends.
        In Iranian market context, transactions outside business hours (9:00–18:00
        Saturday–Wednesday) raise suspicion, especially for large amounts.
        Iran's weekend is Thursday–Friday.
        """
        triggered = False
        reason = ""
        risk_score = 0

        # Parse transaction time in Tehran timezone
        tehran_tz = pytz.timezone('Asia/Tehran')
        try:
            txn_dt = transaction.transaction_date
            if txn_dt.tzinfo is None:
                txn_dt = timezone.make_aware(txn_dt, tehran_tz)
            txn_local = txn_dt.astimezone(tehran_tz)
        except Exception:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        hour = txn_local.hour
        # Python weekday(): Monday=0, ..., Friday=4, Saturday=5, Sunday=6
        # Iran weekend: Thursday=3, Friday=4
        weekday = txn_local.weekday()
        is_weekend = weekday in (3, 4)  # Thursday, Friday

        night_start = config.get('night_start_hour', 22)
        night_end = config.get('night_end_hour', 7)
        night_amount_threshold = Decimal(str(config.get('night_amount_threshold', 50_000_000)))
        weekend_amount_threshold = Decimal(str(config.get('weekend_amount_threshold', 100_000_000)))

        is_night = hour >= night_start or hour < night_end

        if is_night and transaction.amount >= night_amount_threshold:
            triggered = True
            reason = (
                f"تراکنش در ساعت غیرعادی {txn_local.strftime('%H:%M')} "
                f"به مبلغ {transaction.amount:,.0f} ریال"
            )
            risk_score = 65

        if is_weekend and transaction.amount >= weekend_amount_threshold:
            triggered = True
            day_name = 'پنج‌شنبه' if weekday == 3 else 'جمعه'
            reason = (reason + ' | ' if reason else '') + (
                f"تراکنش در روز {day_name} "
                f"به مبلغ {transaction.amount:,.0f} ریال"
            )
            risk_score = max(risk_score, 60)

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Issue #24: Round-amount / Structuring Pattern ────────────────────────
    def _evaluate_round_amount_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Issue #24: Detect round-number transactions often used in structuring.
        Transactions with amounts that are exact multiples of large round numbers
        (e.g., 10M, 50M, 100M IRR) are a classic money-laundering indicator.
        """
        triggered = False
        reason = ""
        risk_score = 0

        # Thresholds for "round" amounts (in IRR)
        round_thresholds = config.get('round_thresholds', [
            10_000_000,   # 10M
            50_000_000,   # 50M
            100_000_000,  # 100M
            500_000_000,  # 500M
        ])
        min_amount = Decimal(str(config.get('min_amount', 10_000_000)))
        lookback_days = config.get('lookback_days', 30)
        min_round_count = config.get('min_round_count', 3)

        if transaction.amount < min_amount:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        # Check if current transaction is a round number
        amount_int = int(transaction.amount)
        is_round = any(amount_int % int(t) == 0 for t in round_thresholds)

        if not is_round:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        # Count recent round-amount transactions
        lookback = timezone.now() - timedelta(days=lookback_days)
        recent_txns = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=lookback,
            status='COMPLETED',
        )

        round_count = 0
        for t in recent_txns:
            t_int = int(t.amount)
            if any(t_int % int(thresh) == 0 for thresh in round_thresholds):
                round_count += 1

        # Include current transaction
        round_count += 1

        if round_count >= min_round_count:
            triggered = True
            reason = (
                f"الگوی تجزیه مبلغ گرد: {round_count} تراکنش با مبلغ گرد "
                f"در {lookback_days} روز اخیر (مبلغ فعلی: {transaction.amount:,.0f} ریال)"
            )
            risk_score = min(100, 50 + round_count * 10)

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Issue #26: New-account Velocity Rule ─────────────────────────────────
    def _evaluate_new_account_velocity_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Issue #26: Detect unusually high transaction velocity for new accounts.
        Accounts in the first 30 or 90 days are held to tighter limits as
        they are common targets for money mule setups in Iran.
        """
        triggered = False
        reason = ""
        risk_score = 0

        customer = transaction.customer
        account_age_days = (timezone.now() - customer.registration_date).days

        new_account_days_30 = config.get('new_account_days_30', 30)
        new_account_days_90 = config.get('new_account_days_90', 90)

        # Apply limits only for accounts within the window
        if account_age_days > new_account_days_90:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        # Tighter limits for very new accounts (0–30 days)
        if account_age_days <= new_account_days_30:
            max_daily_count = config.get('max_daily_count_30d', 5)
            max_daily_amount = Decimal(str(config.get('max_daily_amount_30d', 50_000_000)))
            window_label = '۳۰ روز اول'
        else:
            max_daily_count = config.get('max_daily_count_90d', 10)
            max_daily_amount = Decimal(str(config.get('max_daily_amount_90d', 200_000_000)))
            window_label = '۹۰ روز اول'

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_txns = Transaction.objects.filter(
            customer=customer,
            transaction_date__gte=today_start,
            status='COMPLETED',
        )
        today_count = today_txns.count()
        today_amount = today_txns.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Include current transaction
        today_count += 1
        today_amount += transaction.amount

        if today_count > max_daily_count:
            triggered = True
            reason = (
                f"حساب جدید ({window_label}، {account_age_days} روزه): "
                f"{today_count} تراکنش امروز (حداکثر مجاز: {max_daily_count})"
            )
            risk_score = min(100, 60 + (today_count - max_daily_count) * 5)

        if today_amount > max_daily_amount:
            triggered = True
            reason = (reason + ' | ' if reason else '') + (
                f"حساب جدید ({window_label}، {account_age_days} روزه): "
                f"مجموع امروز {today_amount:,.0f} ریال (حداکثر مجاز: {max_daily_amount:,.0f})"
            )
            risk_score = max(risk_score, min(100, int(float(today_amount / max_daily_amount) * 70)))

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Fraud Rule: Device Shared Across Accounts ────────────────────────────
    def _evaluate_device_sharing_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Detect a single device (fingerprint) transacting for an unusual number of
        distinct customers within a lookback window — a classic account-ring /
        farmed-account signal (fake accounts, referral abuse, credential stuffing).
        """
        triggered = False
        reason = ""
        risk_score = 0

        device = transaction.device
        if device is None:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        lookback_days = config.get('lookback_days', 30)
        max_distinct_customers = config.get('max_distinct_customers', 3)
        lookback = timezone.now() - timedelta(days=lookback_days)

        distinct_customers = Transaction.objects.filter(
            device=device,
            transaction_date__gte=lookback,
        ).values('customer').distinct().count()

        if distinct_customers >= max_distinct_customers:
            triggered = True
            reason = (
                f"دستگاه {device.device_id} در {lookback_days} روز اخیر برای "
                f"{distinct_customers} حساب متفاوت استفاده شده (آستانه: {max_distinct_customers})"
            )
            risk_score = min(100, 40 + distinct_customers * 12)

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Fraud Rule: Merchant Fake-purchase / Chargeback Abuse ────────────────
    def _evaluate_merchant_abuse_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Flag transactions at merchants whose historical refund/chargeback rate
        exceeds normal bounds, or that show a sudden volume spike — indicators
        of fake-purchase loops or merchant-side collusion.
        """
        triggered = False
        reason = ""
        risk_score = 0

        merchant = transaction.merchant
        if merchant is None:
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        chargeback_threshold = Decimal(str(config.get('chargeback_rate_threshold', 5.0)))
        refund_threshold = Decimal(str(config.get('refund_rate_threshold', 15.0)))

        if merchant.chargeback_rate >= chargeback_threshold:
            triggered = True
            reason = (
                f"مرچنت {merchant.name} نرخ چارجبک {merchant.chargeback_rate}% دارد "
                f"(آستانه: {chargeback_threshold}%)"
            )
            risk_score = min(100, int(float(merchant.chargeback_rate / chargeback_threshold) * 60))

        if merchant.refund_rate >= refund_threshold:
            triggered = True
            reason = (reason + ' | ' if reason else '') + (
                f"مرچنت {merchant.name} نرخ بازگشت وجه {merchant.refund_rate}% دارد "
                f"(آستانه: {refund_threshold}%)"
            )
            risk_score = max(risk_score, min(100, int(float(merchant.refund_rate / refund_threshold) * 50)))

        # Sudden volume spike: today's transaction count vs. 30-day daily average
        lookback_days = config.get('volume_lookback_days', 30)
        spike_multiplier = config.get('volume_spike_multiplier', 3.0)
        lookback = timezone.now() - timedelta(days=lookback_days)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        historical_count = Transaction.objects.filter(
            merchant=merchant, transaction_date__gte=lookback, transaction_date__lt=today_start,
        ).count()
        today_count = Transaction.objects.filter(
            merchant=merchant, transaction_date__gte=today_start,
        ).count() + 1

        avg_daily = historical_count / max(lookback_days, 1)
        if avg_daily > 0 and today_count >= avg_daily * spike_multiplier and today_count >= 5:
            triggered = True
            reason = (reason + ' | ' if reason else '') + (
                f"جهش حجم تراکنش مرچنت {merchant.name}: امروز {today_count} در برابر "
                f"میانگین روزانه {avg_daily:.1f}"
            )
            risk_score = max(risk_score, 70)

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}

    # ── Fraud Rule: BNPL Default Risk Pattern ────────────────────────────────
    def _evaluate_bnpl_risk_rule(self, rule: Rule, transaction: Transaction, config: Dict) -> Dict:
        """
        Flag BNPL (buy-now-pay-later) purchase patterns that historically precede
        default: many open BNPL purchases with few/no repayments, or a new
        customer taking a large BNPL exposure right away.
        """
        triggered = False
        reason = ""
        risk_score = 0

        if transaction.transaction_type != 'BNPL_PURCHASE':
            return {'triggered': False, 'reason': '', 'risk_score': 0}

        customer = transaction.customer
        lookback_days = config.get('lookback_days', 90)
        max_open_purchases = config.get('max_open_purchases', 3)
        min_repayment_ratio = config.get('min_repayment_ratio', 0.3)

        lookback = timezone.now() - timedelta(days=lookback_days)
        purchases = Transaction.objects.filter(
            customer=customer, transaction_type='BNPL_PURCHASE',
            transaction_date__gte=lookback,
        )
        purchase_count = purchases.count() + 1
        purchase_total = (purchases.aggregate(total=Sum('amount'))['total'] or Decimal('0')) + transaction.amount

        repayments = Transaction.objects.filter(
            customer=customer, transaction_type='BNPL_REPAYMENT',
            transaction_date__gte=lookback,
        )
        repayment_total = repayments.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if purchase_count > max_open_purchases:
            repayment_ratio = float(repayment_total / purchase_total) if purchase_total > 0 else 0
            if repayment_ratio < min_repayment_ratio:
                triggered = True
                reason = (
                    f"ریسک نکول BNPL: {purchase_count} خرید اعتباری در {lookback_days} روز "
                    f"با نسبت بازپرداخت {repayment_ratio:.0%} (حداقل مجاز: {min_repayment_ratio:.0%})"
                )
                risk_score = min(100, 50 + (purchase_count - max_open_purchases) * 10)

        return {'triggered': triggered, 'reason': reason, 'risk_score': risk_score}


# ─── Update singleton to use ExtendedRuleEngine ──────────────────────────────

def get_rule_engine() -> ExtendedRuleEngine:
    """Get singleton instance of ExtendedRuleEngine (replaces base get_rule_engine)."""
    global _rule_engine_instance
    if _rule_engine_instance is None:
        _rule_engine_instance = ExtendedRuleEngine()
    return _rule_engine_instance
