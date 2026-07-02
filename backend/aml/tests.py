"""
Tests for AML System
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta

from .models import Customer, Transaction, Rule, Alert, RiskScore, Report
from .services.transaction_monitor import get_transaction_monitor
from .services.risk_scorer import get_risk_scorer
from .services.alert_generator import get_alert_generator
from .services.report_generator import get_report_generator
from .rules.aml_rules import get_rule_engine


class HealthReadyTest(TestCase):
    """Test health and readiness endpoints (no auth)."""

    def setUp(self):
        self.client = Client()

    def test_health_returns_ok(self):
        r = self.client.get('/api/health/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ok')
        self.assertIn('service', r.json())

    def test_ready_returns_ready_when_db_ok(self):
        r = self.client.get('/api/ready/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ready')
        self.assertEqual(r.json()['database'], 'ok')


class CustomerModelTest(TestCase):
    """Test Customer model"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
    
    def test_customer_creation(self):
        """Test customer creation"""
        self.assertEqual(self.customer.customer_id, 'CUST001')
        self.assertEqual(self.customer.first_name, 'John')
        self.assertEqual(self.customer.current_risk_level, 'MEDIUM')
        self.assertEqual(self.customer.risk_score, Decimal('50.0'))


class TransactionModelTest(TestCase):
    """Test Transaction model"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        self.transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('1000000'),
            currency='IRR',
            status='COMPLETED'
        )
    
    def test_transaction_creation(self):
        """Test transaction creation"""
        self.assertEqual(self.transaction.transaction_id, 'TXN001')
        self.assertEqual(self.transaction.customer, self.customer)
        self.assertEqual(self.transaction.amount, Decimal('1000000'))
        self.assertFalse(self.transaction.is_suspicious)


class RuleEngineTest(TestCase):
    """Test Rule Engine"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        # Create a threshold rule
        self.rule = Rule.objects.create(
            name='High Amount Threshold',
            description='Flag transactions above 10M',
            rule_type='THRESHOLD',
            status='ACTIVE',
            configuration={
                'amount_threshold': 10000000
            },
            priority=1
        )
    
    def test_threshold_rule(self):
        """Test threshold rule evaluation"""
        # Create a high amount transaction
        transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),  # Above threshold
            currency='IRR',
            status='COMPLETED'
        )
        
        rule_engine = get_rule_engine()
        triggered_rules, reasons, risk_score = rule_engine.evaluate_transaction(transaction)
        
        self.assertGreater(len(triggered_rules), 0)
        self.assertIn(self.rule, triggered_rules)
        self.assertGreater(risk_score, 0)


class RiskScorerTest(TestCase):
    """Test Risk Scorer"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
    
    def test_transaction_risk_scoring(self):
        """Test transaction risk score calculation"""
        transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('50000000'),  # High amount
            currency='IRR',
            status='COMPLETED'
        )
        
        risk_scorer = get_risk_scorer()
        result = risk_scorer.calculate_transaction_risk_score(transaction)
        
        self.assertIn('score', result)
        self.assertIn('factors', result)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
    
    def test_customer_risk_scoring(self):
        """Test customer risk score calculation"""
        risk_scorer = get_risk_scorer()
        result = risk_scorer.calculate_customer_risk_score(self.customer)
        
        self.assertIn('score', result)
        self.assertIn('factors', result)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)


class TransactionMonitorTest(TestCase):
    """Test Transaction Monitor"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        # Create a threshold rule
        Rule.objects.create(
            name='High Amount Threshold',
            description='Flag transactions above 10M',
            rule_type='THRESHOLD',
            status='ACTIVE',
            configuration={
                'amount_threshold': 10000000
            },
            priority=1
        )
    
    def test_transaction_monitoring(self):
        """Test transaction monitoring"""
        transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),  # Above threshold
            currency='IRR',
            status='COMPLETED'
        )
        
        monitor = get_transaction_monitor()
        result = monitor.monitor_transaction(transaction)
        
        self.assertIn('risk_score', result)
        self.assertIn('is_suspicious', result)
        self.assertIn('should_alert', result)
        
        # Refresh transaction from DB
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.risk_score)
        
        # Check if alert was created
        if result['should_alert']:
            alerts = Alert.objects.filter(transaction=transaction)
            self.assertGreater(alerts.count(), 0)


class AlertGeneratorTest(TestCase):
    """Test Alert Generator"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        self.transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),
            currency='IRR',
            status='COMPLETED'
        )
    
    def test_alert_generation(self):
        """Test alert generation"""
        alert_generator = get_alert_generator()
        
        alert = alert_generator.generate_alert(
            transaction=self.transaction,
            triggered_rules=[],
            risk_score=Decimal('85'),
            severity='HIGH',
            reasons=['High transaction amount']
        )
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.transaction, self.transaction)
        self.assertEqual(alert.customer, self.customer)
        self.assertEqual(alert.severity, 'HIGH')
        self.assertEqual(alert.status, 'OPEN')
    
    def test_alert_review(self):
        """Test alert review"""
        alert_generator = get_alert_generator()
        
        alert = alert_generator.generate_alert(
            transaction=self.transaction,
            triggered_rules=[],
            risk_score=Decimal('85'),
            severity='HIGH',
            reasons=['High transaction amount']
        )
        
        reviewed_alert = alert_generator.review_alert(
            alert=alert,
            reviewer='test_user',
            status='RESOLVED',
            notes='False positive - legitimate business transaction'
        )
        
        self.assertEqual(reviewed_alert.status, 'RESOLVED')
        self.assertEqual(reviewed_alert.reviewed_by, 'test_user')
        self.assertIsNotNone(reviewed_alert.reviewed_at)


class ReportGeneratorTest(TestCase):
    """Test Report Generator"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            country='IR'
        )
        
        self.transaction = Transaction.objects.create(
            transaction_id='TXN001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('15000000'),
            currency='IRR',
            status='COMPLETED'
        )
        
        self.alert = Alert.objects.create(
            alert_id='ALT001',
            transaction=self.transaction,
            customer=self.customer,
            severity='HIGH',
            status='OPEN',
            title='Test Alert',
            description='Test alert description',
            risk_score=Decimal('85')
        )
    
    def test_sar_generation(self):
        """Test SAR report generation"""
        report_generator = get_report_generator()
        
        period_start = timezone.now() - timedelta(days=30)
        period_end = timezone.now()
        
        report = report_generator.generate_sar(
            alerts=[self.alert],
            period_start=period_start,
            period_end=period_end,
            submitted_by='test_user'
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, 'SAR')
        self.assertEqual(report.status, 'DRAFT')
        self.assertIn('alerts', report.report_data)
        self.assertEqual(len(report.report_data['alerts']), 1)
    
    def test_ctr_generation(self):
        """Test CTR report generation"""
        report_generator = get_report_generator()
        
        period_start = timezone.now() - timedelta(days=30)
        period_end = timezone.now()
        
        report = report_generator.generate_ctr(
            transactions=[self.transaction],
            period_start=period_start,
            period_end=period_end,
            threshold=Decimal('10000000'),
            submitted_by='test_user'
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.report_type, 'CTR')
        self.assertEqual(report.status, 'DRAFT')
        self.assertIn('transactions', report.report_data)
        self.assertEqual(len(report.report_data['transactions']), 1)



# ─────────────────────────────────────────────────────────────────────────────
# Issue #28: End-to-end structuring test (documented flow)
# ─────────────────────────────────────────────────────────────────────────────

class StructuringScenarioTest(TestCase):
    """
    Issue #28: Scenario — Structuring (تجزیه وجه)
    A customer makes multiple transactions just below the CTR threshold
    within a 7-day window to avoid reporting.
    """

    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='STRUCT001',
            first_name='علی',
            last_name='رضایی',
            email='ali.rezaei@test.ir',
            country='IR',
        )
        Rule.objects.create(
            name='Structuring Detection',
            description='Detect potential structuring',
            rule_type='PATTERN',
            status='ACTIVE',
            configuration={
                'structuring_threshold': 500_000_000,   # 500M IRR CTR threshold
                'structuring_count': 3,
                'lookback_days': 7,
            },
            priority=1,
        )

    def test_structuring_below_ctr_threshold(self):
        """
        Three transactions each at 480M IRR (just below 500M CTR threshold)
        should trigger the structuring detection rule.
        """
        for i in range(3):
            Transaction.objects.create(
                transaction_id=f'STRUCT_TXN_{i:03d}',
                customer=self.customer,
                transaction_type='TRANSFER',
                amount=Decimal('480000000'),  # 480M — 96% of 500M threshold
                currency='IRR',
                status='COMPLETED',
            )

        last_txn = Transaction.objects.create(
            transaction_id='STRUCT_TXN_003',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('480000000'),
            currency='IRR',
            status='COMPLETED',
        )

        rule_engine = get_rule_engine()
        triggered_rules, reasons, risk_score = rule_engine.evaluate_transaction(last_txn)

        self.assertGreater(len(triggered_rules), 0, "Structuring rule should trigger")
        self.assertGreater(risk_score, 0, "Risk score should be > 0 for structuring")
        structuring_reasons = [r for r in reasons if 'structuring' in r.lower()]
        self.assertTrue(len(structuring_reasons) > 0, "Should mention structuring in reasons")


# ─────────────────────────────────────────────────────────────────────────────
# Issue #29: Layering / Rapid movement test
# ─────────────────────────────────────────────────────────────────────────────

class LayeringScenarioTest(TestCase):
    """
    Issue #29: Scenario — Layering (لایه‌گذاری)
    A customer makes many rapid transactions in a short window (< 10 min)
    to obscure the origin of funds.
    """

    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='LAYER001',
            first_name='مریم',
            last_name='احمدی',
            email='maryam.ahmadi@test.ir',
            country='IR',
        )
        Rule.objects.create(
            name='Rapid Transaction Detection',
            description='Detect layering via rapid transactions',
            rule_type='PATTERN',
            status='ACTIVE',
            configuration={
                'rapid_transaction_threshold': True,
                'rapid_transaction_minutes': 10,
                'rapid_transaction_count': 5,
            },
            priority=1,
        )

    def test_rapid_transactions_trigger_layering_rule(self):
        """
        5 or more completed transactions within 10 minutes should
        trigger the rapid transaction / layering detection rule.
        """
        base_time = timezone.now() - timedelta(minutes=5)
        for i in range(5):
            Transaction.objects.create(
                transaction_id=f'LAYER_TXN_{i:03d}',
                customer=self.customer,
                transaction_type='TRANSFER',
                amount=Decimal('5000000'),  # 5M IRR each
                currency='IRR',
                status='COMPLETED',
                transaction_date=base_time + timedelta(seconds=i * 60),
            )

        last_txn = Transaction.objects.create(
            transaction_id='LAYER_TXN_005',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('5000000'),
            currency='IRR',
            status='COMPLETED',
            transaction_date=timezone.now(),
        )

        rule_engine = get_rule_engine()
        triggered_rules, reasons, risk_score = rule_engine.evaluate_transaction(last_txn)

        self.assertGreater(len(triggered_rules), 0, "Layering rule should trigger")
        self.assertGreater(risk_score, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Issue #23: PEP Detection Test
# ─────────────────────────────────────────────────────────────────────────────

class PEPRuleTest(TestCase):
    """
    Issue #23: PEP (Politically Exposed Person) rule.
    Transactions from a PEP customer above the PEP threshold should trigger.
    """

    def setUp(self):
        self.pep_customer = Customer.objects.create(
            customer_id='PEP001',
            first_name='محمد',
            last_name='کریمی',
            email='m.karimi@test.ir',
            country='IR',
            is_pep=True,
        )
        self.normal_customer = Customer.objects.create(
            customer_id='NORM001',
            first_name='سارا',
            last_name='موسوی',
            email='s.mousavi@test.ir',
            country='IR',
            is_pep=False,
        )
        Rule.objects.create(
            name='PEP Transaction Detection',
            description='Flag PEP transactions',
            rule_type='PEP',
            status='ACTIVE',
            configuration={'pep_amount_threshold': 50_000_000},
            priority=1,
            risk_weight=2.5,
        )

    def test_pep_high_value_transaction_triggers(self):
        """PEP customer with 100M IRR transaction must trigger."""
        txn = Transaction.objects.create(
            transaction_id='PEP_TXN_001',
            customer=self.pep_customer,
            transaction_type='TRANSFER',
            amount=Decimal('100000000'),  # 100M IRR
            currency='IRR',
            status='COMPLETED',
        )
        rule_engine = get_rule_engine()
        triggered_rules, reasons, risk_score = rule_engine.evaluate_transaction(txn)
        self.assertGreater(len(triggered_rules), 0, "PEP rule should trigger for PEP customer")
        self.assertGreaterEqual(float(risk_score), 50)

    def test_non_pep_does_not_trigger_pep_rule(self):
        """Normal (non-PEP) customer must NOT trigger the PEP rule."""
        txn = Transaction.objects.create(
            transaction_id='NORM_TXN_001',
            customer=self.normal_customer,
            transaction_type='TRANSFER',
            amount=Decimal('100000000'),
            currency='IRR',
            status='COMPLETED',
        )
        rule_engine = get_rule_engine()
        triggered_rules, _, _ = rule_engine.evaluate_transaction(txn)
        pep_triggered = any(r.rule_type == 'PEP' for r in triggered_rules)
        self.assertFalse(pep_triggered, "PEP rule must NOT trigger for normal customer")


# ─────────────────────────────────────────────────────────────────────────────
# Issue #32: ThresholdConfig Model Test
# ─────────────────────────────────────────────────────────────────────────────

class ThresholdConfigTest(TestCase):
    """Issue #32: ThresholdConfig model can be created and queried."""

    def test_create_threshold_config(self):
        from .models import ThresholdConfig
        config = ThresholdConfig.objects.create(
            name='CTR Main Threshold',
            threshold_type='CTR_THRESHOLD',
            value=Decimal('500000000'),
            description='آستانه گزارش تراکنش کلان — ۵۰۰ میلیون ریال',
            is_active=True,
        )
        self.assertEqual(config.value, Decimal('500000000'))
        self.assertTrue(config.is_active)

    def test_active_threshold_filter(self):
        from .models import ThresholdConfig
        ThresholdConfig.objects.create(
            name='Active CTR', threshold_type='CTR_THRESHOLD',
            value=Decimal('500000000'), is_active=True,
        )
        ThresholdConfig.objects.create(
            name='Inactive SAR', threshold_type='SAR_RISK_SCORE',
            value=Decimal('70'), is_active=False,
        )
        active = ThresholdConfig.objects.filter(is_active=True)
        self.assertEqual(active.count(), 1)


# ─────────────────────────────────────────────────────────────────────────────
# Issue #23: Night/Weekend Activity Detection Rule Test
# ─────────────────────────────────────────────────────────────────────────────

class NightWeekendRuleTest(TestCase):
    """
    Issue #23: Transactions at night or on Iran's weekends (Thu/Fri)
    above the configured threshold should trigger the NIGHT_WEEKEND rule.
    """

    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='NW001',
            first_name='بهنام',
            last_name='نوری',
            email='behnam@test.ir',
            country='IR',
        )
        Rule.objects.create(
            name='Night/Weekend Activity',
            description='Detect suspicious night and weekend transactions',
            rule_type='NIGHT_WEEKEND',
            status='ACTIVE',
            configuration={
                'night_start_hour': 22,
                'night_end_hour': 7,
                'night_amount_threshold': 50_000_000,
                'weekend_amount_threshold': 100_000_000,
            },
            priority=2,
        )

    def test_night_transaction_triggers(self):
        """Large transaction at 23:00 Tehran time should trigger rule."""
        import pytz
        tehran = pytz.timezone('Asia/Tehran')
        # Build a naive datetime at 23:00 today and make it aware in Tehran tz
        now = timezone.now().astimezone(tehran)
        night_time = now.replace(hour=23, minute=0, second=0, microsecond=0)

        txn = Transaction.objects.create(
            transaction_id='NW_NIGHT_001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('80000000'),  # 80M IRR — above 50M threshold
            currency='IRR',
            status='COMPLETED',
            transaction_date=night_time,
        )
        rule_engine = get_rule_engine()
        triggered, _, _ = rule_engine.evaluate_transaction(txn)
        night_triggered = any(r.rule_type == 'NIGHT_WEEKEND' for r in triggered)
        self.assertTrue(night_triggered, "Night transaction rule should trigger at 23:00")

    def test_small_night_transaction_does_not_trigger(self):
        """Small transaction at night (below threshold) must NOT trigger."""
        import pytz
        tehran = pytz.timezone('Asia/Tehran')
        now = timezone.now().astimezone(tehran)
        night_time = now.replace(hour=23, minute=30, second=0, microsecond=0)

        txn = Transaction.objects.create(
            transaction_id='NW_SMALL_001',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('1000000'),  # 1M IRR — below threshold
            currency='IRR',
            status='COMPLETED',
            transaction_date=night_time,
        )
        rule_engine = get_rule_engine()
        triggered, _, _ = rule_engine.evaluate_transaction(txn)
        night_triggered = any(r.rule_type == 'NIGHT_WEEKEND' for r in triggered)
        self.assertFalse(night_triggered, "Small night transaction should NOT trigger")


# ─────────────────────────────────────────────────────────────────────────────
# Issue #24: Round-amount / Structuring Pattern Rule Test
# ─────────────────────────────────────────────────────────────────────────────

class RoundAmountRuleTest(TestCase):
    """
    Issue #24: Multiple round-number transactions in a short window
    indicate structuring and should trigger the ROUND_AMOUNT rule.
    """

    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='RA001',
            first_name='فرید',
            last_name='طاهری',
            email='farid@test.ir',
            country='IR',
        )
        Rule.objects.create(
            name='Round Amount Structuring',
            description='Detect round-number structuring transactions',
            rule_type='ROUND_AMOUNT',
            status='ACTIVE',
            configuration={
                'round_thresholds': [10_000_000, 50_000_000, 100_000_000],
                'min_amount': 10_000_000,
                'lookback_days': 30,
                'min_round_count': 3,
            },
            priority=2,
        )

    def test_repeated_round_amounts_trigger(self):
        """3 or more transactions with round amounts should trigger."""
        # Create 2 completed round-amount transactions
        base = timezone.now() - timedelta(days=2)
        for i in range(2):
            Transaction.objects.create(
                transaction_id=f'RA_PREV_{i:03d}',
                customer=self.customer,
                transaction_type='TRANSFER',
                amount=Decimal('50000000'),  # 50M (round)
                currency='IRR',
                status='COMPLETED',
                transaction_date=base - timedelta(days=i),
            )

        # Third round transaction — should trigger
        txn = Transaction.objects.create(
            transaction_id='RA_CURRENT',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('100000000'),  # 100M (round)
            currency='IRR',
            status='COMPLETED',
        )
        rule_engine = get_rule_engine()
        triggered, _, _ = rule_engine.evaluate_transaction(txn)
        round_triggered = any(r.rule_type == 'ROUND_AMOUNT' for r in triggered)
        self.assertTrue(round_triggered, "Round-amount rule should trigger after 3 round transactions")

    def test_non_round_amount_does_not_trigger(self):
        """Non-round amount must NOT trigger the round-amount rule."""
        txn = Transaction.objects.create(
            transaction_id='RA_NONROUND',
            customer=self.customer,
            transaction_type='TRANSFER',
            amount=Decimal('37500000'),  # 37.5M — not a round number
            currency='IRR',
            status='COMPLETED',
        )
        rule_engine = get_rule_engine()
        triggered, _, _ = rule_engine.evaluate_transaction(txn)
        round_triggered = any(r.rule_type == 'ROUND_AMOUNT' for r in triggered)
        self.assertFalse(round_triggered, "Non-round amount should NOT trigger the rule")


# ─────────────────────────────────────────────────────────────────────────────
# Issue #26: New-account Velocity Rule Test
# ─────────────────────────────────────────────────────────────────────────────

class NewAccountVelocityRuleTest(TestCase):
    """
    Issue #26: New accounts (first 30 or 90 days) with abnormally high
    daily transaction count or amount should trigger the NEW_ACCOUNT rule.
    """

    def setUp(self):
        # Account created 10 days ago (within 30-day window)
        self.new_customer = Customer.objects.create(
            customer_id='NEW001',
            first_name='نیلوفر',
            last_name='صادقی',
            email='nilufar@test.ir',
            country='IR',
            registration_date=timezone.now() - timedelta(days=10),
        )
        # Old account (over 90 days old — rule should not apply)
        self.old_customer = Customer.objects.create(
            customer_id='OLD001',
            first_name='رضا',
            last_name='منصوری',
            email='reza@test.ir',
            country='IR',
            registration_date=timezone.now() - timedelta(days=200),
        )
        Rule.objects.create(
            name='New Account Velocity',
            description='Detect velocity abuse on new accounts',
            rule_type='NEW_ACCOUNT',
            status='ACTIVE',
            configuration={
                'new_account_days_30': 30,
                'new_account_days_90': 90,
                'max_daily_count_30d': 5,
                'max_daily_amount_30d': 50_000_000,
                'max_daily_count_90d': 10,
                'max_daily_amount_90d': 200_000_000,
            },
            priority=2,
        )

    def test_new_account_over_daily_count_triggers(self):
        """6 transactions in a day on a new account (limit=5) should trigger."""
        today = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        for i in range(5):
            Transaction.objects.create(
                transaction_id=f'NA_PREV_{i:03d}',
                customer=self.new_customer,
                transaction_type='TRANSFER',
                amount=Decimal('5000000'),
                currency='IRR',
                status='COMPLETED',
                transaction_date=today - timedelta(hours=i),
            )

        txn = Transaction.objects.create(
            transaction_id='NA_OVER_COUNT',
            customer=self.new_customer,
            transaction_type='TRANSFER',
            amount=Decimal('5000000'),
            currency='IRR',
            status='COMPLETED',
            transaction_date=today,
        )
        rule_engine = get_rule_engine()
        triggered, _, _ = rule_engine.evaluate_transaction(txn)
        na_triggered = any(r.rule_type == 'NEW_ACCOUNT' for r in triggered)
        self.assertTrue(na_triggered, "New-account velocity rule should trigger (count exceeded)")

    def test_old_account_not_affected(self):
        """Old account (>90 days) must NOT trigger the new-account rule."""
        txn = Transaction.objects.create(
            transaction_id='OLD_ACCT_TXN',
            customer=self.old_customer,
            transaction_type='TRANSFER',
            amount=Decimal('200000000'),
            currency='IRR',
            status='COMPLETED',
        )
        rule_engine = get_rule_engine()
        triggered, _, _ = rule_engine.evaluate_transaction(txn)
        na_triggered = any(r.rule_type == 'NEW_ACCOUNT' for r in triggered)
        self.assertFalse(na_triggered, "Old account should NOT trigger new-account velocity rule")


# ─────────────────────────────────────────────────────────────────────────────
# Issue #15: Bulk Export Test
# ─────────────────────────────────────────────────────────────────────────────

class BulkExportTest(TestCase):
    """Issue #15: Bulk CSV/Excel export for alerts requires authentication."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user('exporter', password='testpass123')
        self.client = Client()
        self.client.login(username='exporter', password='testpass123')

    def test_csv_export_returns_200(self):
        r = self.client.get('/api/alerts/export/?format=csv')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])

    def test_xlsx_export_returns_200(self):
        r = self.client.get('/api/alerts/export/?format=xlsx')
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r['Content-Type'])
