"""
Tests for AML System
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta

from .models import Customer, Transaction, Rule, Alert, AlertComment, RiskScore, Report
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

    def test_alert_review_logs_status_change_comment(self):
        """Issue #39: reviewing an alert should log a STATUS_CHANGE case-history comment"""
        alert_generator = get_alert_generator()

        alert = alert_generator.generate_alert(
            transaction=self.transaction,
            triggered_rules=[],
            risk_score=Decimal('85'),
            severity='HIGH',
            reasons=['High transaction amount']
        )

        alert_generator.review_alert(
            alert=alert,
            reviewer='test_user',
            status='RESOLVED',
            notes='Confirmed legitimate'
        )

        comments = alert.comments.filter(comment_type='STATUS_CHANGE')
        self.assertEqual(comments.count(), 1)
        self.assertEqual(comments.first().author, 'test_user')

    def test_alert_assignment(self):
        """Issue #39: assigning an alert to an investigator, and unassigning"""
        alert_generator = get_alert_generator()

        alert = alert_generator.generate_alert(
            transaction=self.transaction,
            triggered_rules=[],
            risk_score=Decimal('85'),
            severity='HIGH',
            reasons=['High transaction amount']
        )

        alert = alert_generator.assign_alert(alert, assigned_to='investigator1',
                                             assigned_by='supervisor', notes='Please review')

        self.assertEqual(alert.assigned_to, 'investigator1')
        self.assertIsNotNone(alert.assigned_at)
        self.assertEqual(alert.comments.filter(comment_type='ASSIGNMENT').count(), 1)

        alert = alert_generator.assign_alert(alert, assigned_to='', assigned_by='supervisor')

        self.assertEqual(alert.assigned_to, '')
        self.assertIsNone(alert.assigned_at)
        self.assertEqual(alert.comments.filter(comment_type='ASSIGNMENT').count(), 2)

    def test_alert_add_comment(self):
        """Issue #39: adding a free-form investigation note to an alert"""
        alert_generator = get_alert_generator()

        alert = alert_generator.generate_alert(
            transaction=self.transaction,
            triggered_rules=[],
            risk_score=Decimal('85'),
            severity='HIGH',
            reasons=['High transaction amount']
        )

        comment = alert_generator.add_comment(alert, author='investigator1',
                                              comment='Looks suspicious, escalating soon')

        self.assertIsInstance(comment, AlertComment)
        self.assertEqual(alert.comments.count(), 1)
        self.assertEqual(comment.comment_type, 'COMMENT')


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
        r = self.client.get('/api/alerts/export/?export_format=csv')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])

    def test_xlsx_export_returns_200(self):
        r = self.client.get('/api/alerts/export/?export_format=xlsx')
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r['Content-Type'])


# ─────────────────────────────────────────────────────────────────────────────
# Roadmap #40-#46: watchlist, SLA, bulk actions, comment export, JSON logging
# ─────────────────────────────────────────────────────────────────────────────

import csv
import io
import json
import logging

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .models import ThresholdConfig, WatchlistEntry


class RoadmapBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('officer', password='pw')
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.customer = Customer.objects.create(
            customer_id='RM001', first_name='A', last_name='B',
            email='a@b.ir', country='IR',
        )
        self.generator = get_alert_generator()

    def make_alert(self, n=1, severity='HIGH'):
        txn = Transaction.objects.create(
            transaction_id=f'RMTXN{n}', customer=self.customer, transaction_type='TRANSFER',
            amount=Decimal('1000'), currency='IRR', status='COMPLETED',
        )
        return self.generator.generate_alert(
            transaction=txn, triggered_rules=[], risk_score=Decimal('80'),
            severity=severity, reasons=['r'],
        )


class WatchlistTest(RoadmapBase):
    def test_seeded_countries_exist(self):
        codes = set(WatchlistEntry.objects.filter(entry_type='COUNTRY').values_list('country_code', flat=True))
        self.assertTrue({'KP', 'SD', 'SY', 'SO', 'LY'} <= codes)

    def test_api_create_normalises_and_validates(self):
        r = self.api.post('/api/watchlist/', {'entry_type': 'COUNTRY', 'country_code': 'ir '}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['country_code'], 'IR')
        self.assertEqual(r.json()['added_by'], 'officer')

        bad = self.api.post('/api/watchlist/', {'entry_type': 'COUNTRY', 'country_code': 'XYZ'}, format='json')
        self.assertEqual(bad.status_code, 400)
        bad = self.api.post('/api/watchlist/', {'entry_type': 'ENTITY'}, format='json')
        self.assertEqual(bad.status_code, 400)

    def test_sanctioned_rule_uses_watchlist(self):
        Rule.objects.create(
            name='Sanctioned', description='d', rule_type='SANCTIONED',
            status='ACTIVE', configuration={}, priority=1, risk_weight=3,
        )
        txn = Transaction.objects.create(
            transaction_id='SANC1', customer=self.customer, transaction_type='TRANSFER',
            amount=Decimal('1000'), currency='IRR', status='COMPLETED', receiver_country='DE',
        )
        engine = get_rule_engine()
        triggered, _, _ = engine.evaluate_transaction(txn)
        self.assertEqual(triggered, [])

        WatchlistEntry.objects.create(entry_type='COUNTRY', country_code='DE')
        triggered, _, _ = get_rule_engine().evaluate_transaction(txn)
        self.assertEqual(len(triggered), 1)

        WatchlistEntry.objects.filter(country_code='DE').update(is_active=False)
        triggered, _, _ = get_rule_engine().evaluate_transaction(txn)
        self.assertEqual(triggered, [])


class SlaEscalationTest(RoadmapBase):
    def test_overdue_assigned_alert_is_escalated_once(self):
        alert = self.make_alert()
        self.generator.assign_alert(alert, 'inv1', 'boss')
        Alert.objects.filter(pk=alert.pk).update(assigned_at=timezone.now() - timedelta(hours=30))

        escalated = self.generator.escalate_overdue_alerts()
        self.assertEqual([a.alert_id for a in escalated], [alert.alert_id])
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'ESCALATED')
        self.assertTrue(alert.comments.filter(comment_type='STATUS_CHANGE', author='system:sla').exists())

        self.assertEqual(self.generator.escalate_overdue_alerts(), [])

    def test_within_sla_or_unassigned_not_escalated(self):
        a1 = self.make_alert(1)
        self.generator.assign_alert(a1, 'inv1', 'boss')
        a2 = self.make_alert(2)
        Alert.objects.filter(pk=a2.pk).update(created_at=timezone.now() - timedelta(days=5))
        self.assertEqual(self.generator.escalate_overdue_alerts(), [])

    def test_threshold_config_overrides_default(self):
        ThresholdConfig.objects.create(name='sla', threshold_type='ALERT_SLA_HOURS', value=Decimal('2'))
        alert = self.make_alert()
        self.generator.assign_alert(alert, 'inv1', 'boss')
        Alert.objects.filter(pk=alert.pk).update(assigned_at=timezone.now() - timedelta(hours=3))
        self.assertEqual(len(self.generator.escalate_overdue_alerts()), 1)

    def test_celery_task(self):
        from .tasks import escalate_overdue_alerts
        alert = self.make_alert()
        self.generator.assign_alert(alert, 'inv1', 'boss')
        Alert.objects.filter(pk=alert.pk).update(assigned_at=timezone.now() - timedelta(hours=48))
        result = escalate_overdue_alerts()
        self.assertEqual(result['escalated'], 1)


class BulkAlertActionsTest(RoadmapBase):
    def test_bulk_assign(self):
        a1, a2 = self.make_alert(1), self.make_alert(2)
        r = self.api.post('/api/alerts/bulk-assign/', {
            'alert_ids': [a1.alert_id, a2.alert_id, 'NOPE'], 'assigned_to': 'inv1',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(sorted(r.json()['updated']), sorted([a1.alert_id, a2.alert_id]))
        self.assertEqual(r.json()['not_found'], ['NOPE'])
        a1.refresh_from_db()
        self.assertEqual(a1.assigned_to, 'inv1')
        self.assertEqual(a1.comments.filter(comment_type='ASSIGNMENT').count(), 1)

    def test_bulk_review(self):
        a1, a2 = self.make_alert(1), self.make_alert(2)
        r = self.api.post('/api/alerts/bulk-review/', {
            'alert_ids': [a1.alert_id, a2.alert_id], 'status': 'FALSE_POSITIVE', 'notes': 'ok',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        for a in (a1, a2):
            a.refresh_from_db()
            self.assertEqual(a.status, 'FALSE_POSITIVE')
            self.assertEqual(a.reviewed_by, 'officer')

    def test_bulk_validation(self):
        r = self.api.post('/api/alerts/bulk-review/', {'alert_ids': [], 'status': 'RESOLVED', 'notes': ''}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.api.post('/api/alerts/bulk-assign/', {'alert_ids': ['x']}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_single_review_still_works(self):
        a = self.make_alert()
        r = self.api.post(f'/api/alerts/{a.alert_id}/review/', {'status': 'ESCALATED', 'notes': 'n'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ESCALATED')


class AlertCommentExportTest(RoadmapBase):
    def test_csv_export_with_filters_and_formula_guard(self):
        a1, a2 = self.make_alert(1), self.make_alert(2)
        self.generator.add_comment(a1, 'inv1', '=HYPERLINK("http://x")')
        self.generator.add_comment(a2, 'inv2', 'plain')

        r = self.api.get('/api/alerts/comments-export/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])
        rows = list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
        self.assertEqual(rows[0][0], 'Alert ID')
        self.assertEqual(len(rows), 3)
        self.assertTrue(any(row[6].startswith("'=") for row in rows[1:]))

        r = self.api.get('/api/alerts/comments-export/', {'alert_id': a2.alert_id})
        rows = list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][5], 'inv2')

    def test_xlsx_and_bad_date(self):
        a = self.make_alert()
        self.generator.add_comment(a, 'inv1', 'x')
        r = self.api.get('/api/alerts/comments-export/', {'export_format': 'xlsx'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'PK'))
        r = self.api.get('/api/alerts/comments-export/', {'date_from': 'bad'})
        self.assertEqual(r.status_code, 400)

    def test_alert_export_still_works(self):
        self.make_alert()
        r = self.api.get('/api/alerts/export/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Alert ID', r.content.decode('utf-8-sig'))


class JsonLoggingTest(TestCase):
    def test_formatter_outputs_valid_json(self):
        from config.logging import JsonFormatter
        record = logging.LogRecord('aml', logging.INFO, __file__, 1, 'hello %s', ('وب',), None)
        record.alert_id = 'A1'
        data = json.loads(JsonFormatter().format(record))
        self.assertEqual(data['message'], 'hello وب')
        self.assertEqual(data['level'], 'INFO')
        self.assertEqual(data['alert_id'], 'A1')


class AlertQueueFilterTest(RoadmapBase):
    def test_assignee_and_unassigned_filters(self):
        a1, a2 = self.make_alert(1), self.make_alert(2)
        self.generator.assign_alert(a1, 'inv1', 'boss')

        r = self.api.get('/api/alerts/', {'assigned_to': 'inv1'})
        self.assertEqual([a['alert_id'] for a in r.json()['results']], [a1.alert_id])

        r = self.api.get('/api/alerts/', {'unassigned': '1'})
        self.assertEqual([a['alert_id'] for a in r.json()['results']], [a2.alert_id])
