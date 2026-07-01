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
