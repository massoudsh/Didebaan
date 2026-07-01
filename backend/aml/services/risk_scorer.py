"""
Risk Scoring Service
Calculates risk scores for customers and transactions based on various factors
"""
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Optional
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Max, Q

from aml.models import Customer, Transaction, RiskScore

logger = logging.getLogger('aml')


class RiskScorer:
    """
    Service for calculating risk scores for customers and transactions
    """
    
    def __init__(self):
        self.weights = {
            'transaction_amount': 0.20,
            'transaction_frequency': 0.15,
            'geographic_risk': 0.15,
            'customer_history': 0.20,
            'behavioral_patterns': 0.15,
            'rule_violations': 0.15,
        }
    
    def calculate_transaction_risk_score(self, transaction: Transaction, 
                                         rule_risk_score: Decimal = Decimal('0')) -> Dict:
        """
        Calculate risk score for a specific transaction
        
        Returns:
            Dict with 'score', 'factors', and 'method'
        """
        factors = {}
        total_score = Decimal('0.0')
        
        # Factor 1: Transaction Amount (0-100)
        amount_score = self._calculate_amount_risk(transaction)
        factors['transaction_amount'] = {
            'score': float(amount_score),
            'weight': self.weights['transaction_amount'],
            'details': f"Amount: {transaction.amount} {transaction.currency}"
        }
        total_score += amount_score * Decimal(str(self.weights['transaction_amount']))
        
        # Factor 2: Transaction Frequency (0-100)
        frequency_score = self._calculate_frequency_risk(transaction)
        factors['transaction_frequency'] = {
            'score': float(frequency_score),
            'weight': self.weights['transaction_frequency'],
            'details': self._get_frequency_details(transaction)
        }
        total_score += frequency_score * Decimal(str(self.weights['transaction_frequency']))
        
        # Factor 3: Geographic Risk (0-100)
        geo_score = self._calculate_geographic_risk(transaction)
        factors['geographic_risk'] = {
            'score': float(geo_score),
            'weight': self.weights['geographic_risk'],
            'details': f"From: {transaction.customer.country}, To: {transaction.receiver_country or 'N/A'}"
        }
        total_score += geo_score * Decimal(str(self.weights['geographic_risk']))
        
        # Factor 4: Customer History (0-100)
        history_score = self._calculate_customer_history_risk(transaction.customer)
        factors['customer_history'] = {
            'score': float(history_score),
            'weight': self.weights['customer_history'],
            'details': f"Customer risk level: {transaction.customer.current_risk_level}"
        }
        total_score += history_score * Decimal(str(self.weights['customer_history']))
        
        # Factor 5: Behavioral Patterns (0-100)
        behavioral_score = self._calculate_behavioral_risk(transaction)
        factors['behavioral_patterns'] = {
            'score': float(behavioral_score),
            'weight': self.weights['behavioral_patterns'],
            'details': self._get_behavioral_details(transaction)
        }
        total_score += behavioral_score * Decimal(str(self.weights['behavioral_patterns']))
        
        # Factor 6: Rule Violations (0-100)
        rule_score = min(Decimal('100'), rule_risk_score)
        factors['rule_violations'] = {
            'score': float(rule_score),
            'weight': self.weights['rule_violations'],
            'details': f"Rule-based risk: {rule_score}"
        }
        total_score += rule_score * Decimal(str(self.weights['rule_violations']))
        
        # Ensure score is between 0 and 100
        final_score = max(Decimal('0'), min(Decimal('100'), total_score))
        
        return {
            'score': final_score,
            'factors': factors,
            'method': 'weighted_average'
        }
    
    def calculate_customer_risk_score(self, customer: Customer) -> Dict:
        """
        Calculate overall risk score for a customer
        
        Returns:
            Dict with 'score', 'factors', and 'method'
        """
        factors = {}
        total_score = Decimal('0.0')
        
        # Factor 1: Transaction History
        transaction_score = self._calculate_customer_transaction_risk(customer)
        factors['transaction_history'] = {
            'score': float(transaction_score),
            'weight': 0.30,
            'details': self._get_customer_transaction_details(customer)
        }
        total_score += transaction_score * Decimal('0.30')
        
        # Factor 2: Alert History
        alert_score = self._calculate_customer_alert_risk(customer)
        factors['alert_history'] = {
            'score': float(alert_score),
            'weight': 0.25,
            'details': self._get_customer_alert_details(customer)
        }
        total_score += alert_score * Decimal('0.25')
        
        # Factor 3: Account Age and Activity
        account_score = self._calculate_account_age_risk(customer)
        factors['account_age'] = {
            'score': float(account_score),
            'weight': 0.15,
            'details': f"Account age: {(timezone.now() - customer.registration_date).days} days"
        }
        total_score += account_score * Decimal('0.15')
        
        # Factor 4: Geographic Risk
        geo_score = self._calculate_customer_geographic_risk(customer)
        factors['geographic_risk'] = {
            'score': float(geo_score),
            'weight': 0.15,
            'details': f"Country: {customer.country}"
        }
        total_score += geo_score * Decimal('0.15')
        
        # Factor 5: KYC Completeness
        kyc_score = self._calculate_kyc_completeness_risk(customer)
        factors['kyc_completeness'] = {
            'score': float(kyc_score),
            'weight': 0.15,
            'details': self._get_kyc_completeness_details(customer)
        }
        total_score += kyc_score * Decimal('0.15')
        
        # Ensure score is between 0 and 100
        final_score = max(Decimal('0'), min(Decimal('100'), total_score))
        
        return {
            'score': final_score,
            'factors': factors,
            'method': 'weighted_average'
        }
    
    def _calculate_amount_risk(self, transaction: Transaction) -> Decimal:
        """Calculate risk based on transaction amount"""
        # Get customer's average transaction amount
        lookback_days = 30
        lookback_date = timezone.now() - timedelta(days=lookback_days)
        
        avg_amount = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=lookback_date,
            transaction_date__lt=transaction.transaction_date,
            status='COMPLETED'
        ).aggregate(avg=Avg('amount'))['avg']
        
        if not avg_amount or avg_amount == 0:
            # New customer or no history - moderate risk for large amounts
            if transaction.amount > Decimal('10000000'):  # 10M threshold
                return Decimal('60')
            return Decimal('30')
        
        # Calculate deviation from average
        ratio = float(transaction.amount / avg_amount)
        
        if ratio >= 5.0:
            return Decimal('100')
        elif ratio >= 3.0:
            return Decimal('80')
        elif ratio >= 2.0:
            return Decimal('60')
        elif ratio >= 1.5:
            return Decimal('40')
        else:
            return Decimal('20')
    
    def _calculate_frequency_risk(self, transaction: Transaction) -> Decimal:
        """Calculate risk based on transaction frequency"""
        # Check transactions in last 24 hours
        last_24h = transaction.transaction_date - timedelta(hours=24)
        count_24h = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=last_24h,
            transaction_date__lt=transaction.transaction_date,
            status='COMPLETED'
        ).count()
        
        # Check transactions in last hour
        last_hour = transaction.transaction_date - timedelta(hours=1)
        count_1h = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=last_hour,
            transaction_date__lt=transaction.transaction_date,
            status='COMPLETED'
        ).count()
        
        # High frequency = higher risk
        if count_1h >= 10:
            return Decimal('100')
        elif count_1h >= 5:
            return Decimal('80')
        elif count_24h >= 20:
            return Decimal('70')
        elif count_24h >= 10:
            return Decimal('50')
        else:
            return Decimal('20')
    
    def _calculate_geographic_risk(self, transaction: Transaction) -> Decimal:
        """Calculate risk based on geographic factors"""
        # High-risk countries list (example)
        high_risk_countries = [
            'KP',  # كره شمالي
            'MM',  # ميانمار
            'AF',  # افغانستان
            'YE',  # يمن
            'SD',  # سودان
            'SS',  # سودان جنوبي
            'SY',  # سوريه
            'SO',  # سومالي
            'LY',  # ليبي
            'CD',  # كنگو
            'CF',  # افريقاي مركزي
            'ML',  # مالي
            'HT',  # هائيتي
            'PK',  # پاكستان
            'VU',  # وانواتو
        ]
        
        if transaction.receiver_country in high_risk_countries:
            return Decimal('90')
        
        # Cross-border transactions
        if transaction.receiver_country and transaction.customer.country != transaction.receiver_country:
            return Decimal('40')
        
        # Domestic transactions
        return Decimal('10')
    
    def _calculate_customer_history_risk(self, customer: Customer) -> Decimal:
        """Calculate risk based on customer's historical risk level"""
        risk_levels = {
            'LOW': Decimal('20'),
            'MEDIUM': Decimal('50'),
            'HIGH': Decimal('80'),
            'CRITICAL': Decimal('100'),
        }
        return risk_levels.get(customer.current_risk_level, Decimal('50'))
    
    def _calculate_behavioral_risk(self, transaction: Transaction) -> Decimal:
        """Calculate risk based on behavioral patterns"""
        # Check for unusual transaction times (e.g., very late night)
        hour = transaction.transaction_date.hour
        if hour >= 2 and hour <= 5:  # 2 AM to 5 AM
            return Decimal('40')
        
        # Check for round number amounts (potential structuring)
        amount_str = str(transaction.amount)
        if amount_str.endswith('0000') or amount_str.endswith('00000'):
            return Decimal('30')
        
        return Decimal('15')
    
    def _calculate_customer_transaction_risk(self, customer: Customer) -> Decimal:
        """Calculate risk based on customer's transaction history"""
        lookback_days = 90
        lookback_date = timezone.now() - timedelta(days=lookback_days)
        
        transactions = Transaction.objects.filter(
            customer=customer,
            transaction_date__gte=lookback_date,
            status='COMPLETED'
        )
        
        if not transactions.exists():
            return Decimal('30')  # New customer
        
        total_amount = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        count = transactions.count()
        avg_amount = total_amount / count if count > 0 else Decimal('0')
        
        # High volume or high value = higher risk
        if total_amount > Decimal('100000000'):  # 100M threshold
            return Decimal('90')
        elif total_amount > Decimal('50000000'):
            return Decimal('70')
        elif count > 100:
            return Decimal('60')
        elif count > 50:
            return Decimal('40')
        else:
            return Decimal('25')
    
    def _calculate_customer_alert_risk(self, customer: Customer) -> Decimal:
        """Calculate risk based on customer's alert history"""
        lookback_days = 90
        lookback_date = timezone.now() - timedelta(days=lookback_days)
        
        alerts = customer.alerts.filter(created_at__gte=lookback_date)
        
        if not alerts.exists():
            return Decimal('10')
        
        critical_count = alerts.filter(severity='CRITICAL').count()
        high_count = alerts.filter(severity='HIGH').count()
        total_count = alerts.count()
        
        if critical_count > 0:
            return Decimal('100')
        elif high_count >= 3:
            return Decimal('90')
        elif high_count > 0:
            return Decimal('70')
        elif total_count >= 5:
            return Decimal('50')
        else:
            return Decimal('30')
    
    def _calculate_account_age_risk(self, customer: Customer) -> Decimal:
        """Calculate risk based on account age"""
        age_days = (timezone.now() - customer.registration_date).days
        
        # Very new accounts are higher risk
        if age_days < 7:
            return Decimal('70')
        elif age_days < 30:
            return Decimal('50')
        elif age_days < 90:
            return Decimal('30')
        else:
            return Decimal('15')
    
    def _calculate_customer_geographic_risk(self, customer: Customer) -> Decimal:
        """Calculate risk based on customer's geographic location"""
        # High-risk countries (example)
        high_risk_countries = ['KP','MM','AF','YE','SD','SS','SY','SO','LY','CD','CF','ML','HT','PK','VU']
        
        if customer.country in high_risk_countries:
            return Decimal('80')
        
        return Decimal('20')
    
    def _calculate_kyc_completeness_risk(self, customer: Customer) -> Decimal:
        """Calculate risk based on KYC data completeness"""
        missing_fields = 0
        
        if not customer.date_of_birth:
            missing_fields += 1
        if not customer.national_id:
            missing_fields += 1
        if not customer.address:
            missing_fields += 1
        if not customer.phone:
            missing_fields += 1
        
        # More missing fields = higher risk
        if missing_fields >= 3:
            return Decimal('80')
        elif missing_fields == 2:
            return Decimal('60')
        elif missing_fields == 1:
            return Decimal('40')
        else:
            return Decimal('15')
    
    def _get_frequency_details(self, transaction: Transaction) -> str:
        """Get details about transaction frequency"""
        last_24h = transaction.transaction_date - timedelta(hours=24)
        count_24h = Transaction.objects.filter(
            customer=transaction.customer,
            transaction_date__gte=last_24h,
            transaction_date__lt=transaction.transaction_date,
            status='COMPLETED'
        ).count()
        return f"{count_24h} transactions in last 24 hours"
    
    def _get_behavioral_details(self, transaction: Transaction) -> str:
        """Get details about behavioral patterns"""
        hour = transaction.transaction_date.hour
        return f"Transaction time: {hour}:00"
    
    def _get_customer_transaction_details(self, customer: Customer) -> str:
        """Get details about customer transactions"""
        lookback_days = 90
        lookback_date = timezone.now() - timedelta(days=lookback_days)
        count = Transaction.objects.filter(
            customer=customer,
            transaction_date__gte=lookback_date,
            status='COMPLETED'
        ).count()
        return f"{count} transactions in last 90 days"
    
    def _get_customer_alert_details(self, customer: Customer) -> str:
        """Get details about customer alerts"""
        lookback_days = 90
        lookback_date = timezone.now() - timedelta(days=lookback_days)
        count = customer.alerts.filter(created_at__gte=lookback_date).count()
        return f"{count} alerts in last 90 days"
    
    def _get_kyc_completeness_details(self, customer: Customer) -> str:
        """Get details about KYC completeness"""
        fields = ['date_of_birth', 'national_id', 'address', 'phone']
        missing = [f for f in fields if not getattr(customer, f)]
        return f"Missing: {', '.join(missing) if missing else 'None'}"


# Singleton instance
_risk_scorer_instance = None

def get_risk_scorer() -> RiskScorer:
    """Get singleton instance of RiskScorer"""
    global _risk_scorer_instance
    if _risk_scorer_instance is None:
        _risk_scorer_instance = RiskScorer()
    return _risk_scorer_instance

