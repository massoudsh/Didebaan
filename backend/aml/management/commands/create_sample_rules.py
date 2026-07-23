"""
Management command to create sample AML rules
"""
from django.core.management.base import BaseCommand
from aml.models import Rule


class Command(BaseCommand):
    help = 'Create sample AML rules for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample AML rules...')
        
        # Rule 1: High Amount Threshold
        rule1, created = Rule.objects.get_or_create(
            name='High Amount Threshold',
            defaults={
                'description': 'Flag transactions exceeding 10,000,000 IRR',
                'rule_type': 'THRESHOLD',
                'status': 'ACTIVE',
                'configuration': {
                    'amount_threshold': 10000000
                },
                'priority': 1,
                'risk_weight': 1.5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule1.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule1.name}'))
        
        # Rule 2: Daily Transaction Count
        rule2, created = Rule.objects.get_or_create(
            name='Daily Transaction Count Threshold',
            defaults={
                'description': 'Flag customers with more than 20 transactions per day',
                'rule_type': 'THRESHOLD',
                'status': 'ACTIVE',
                'configuration': {
                    'daily_count_threshold': 20
                },
                'priority': 2,
                'risk_weight': 1.2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule2.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule2.name}'))
        
        # Rule 3: Structuring Detection
        rule3, created = Rule.objects.get_or_create(
            name='Structuring Detection',
            defaults={
                'description': 'Detect potential structuring (multiple transactions just below threshold)',
                'rule_type': 'PATTERN',
                'status': 'ACTIVE',
                'configuration': {
                    'structuring_threshold': 10000000,
                    'structuring_count': 3,
                    'lookback_days': 7
                },
                'priority': 3,
                'risk_weight': 2.0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule3.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule3.name}'))
        
        # Rule 4: Rapid Transactions
        rule4, created = Rule.objects.get_or_create(
            name='Rapid Transaction Detection',
            defaults={
                'description': 'Detect rapid successive transactions (potential layering)',
                'rule_type': 'PATTERN',
                'status': 'ACTIVE',
                'configuration': {
                    'rapid_transaction_threshold': True,
                    'rapid_transaction_minutes': 10,
                    'rapid_transaction_count': 5
                },
                'priority': 4,
                'risk_weight': 1.8,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule4.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule4.name}'))
        
        # Rule 5: Behavioral Change Detection
        rule5, created = Rule.objects.get_or_create(
            name='Behavioral Change Detection',
            defaults={
                'description': 'Detect sudden changes in transaction behavior',
                'rule_type': 'BEHAVIORAL',
                'status': 'ACTIVE',
                'configuration': {
                    'amount_increase_threshold': 3.0,
                    'lookback_days': 30,
                    'pattern_change_detection': True,
                    'pattern_change_threshold': 2.0
                },
                'priority': 5,
                'risk_weight': 1.5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule5.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule5.name}'))
        
        # Rule 6: High-Risk Country
        rule6, created = Rule.objects.get_or_create(
            name='High-Risk Country Detection',
            defaults={
                'description': 'Flag transactions to high-risk countries',
                'rule_type': 'GEOGRAPHIC',
                'status': 'ACTIVE',
                'configuration': {
                    'high_risk_countries': ['KP','MM','AF','YE','SD','SS','SY','SO','LY','CD','CF','ML','HT','PK','VU'],
                    'cross_border_threshold': 5000000
                },
                'priority': 6,
                'risk_weight': 1.3,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule6.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {rule6.name}'))
        
        self._create_iran_market_rules()
        self.stdout.write(self.style.SUCCESS('\nAll rules created successfully.'))


    def _create_iran_market_rules(self):
        """
        Create additional rules for the Iranian market (#22-27, #36).
        Call after the base rules are created.
        """

        # Rule 7: PEP Detection (Issue #23)
        rule7, created = Rule.objects.get_or_create(
            name='PEP Transaction Detection',
            defaults={
                'description': 'تشخیص تراکنش‌های اشخاص در معرض خطر سیاسی (PEP) — '
                               'الزامی طبق دستورالعمل بانک مرکزی',
                'rule_type': 'PEP',
                'status': 'ACTIVE',
                'configuration': {
                    'pep_amount_threshold': 50_000_000,  # 50M IRR
                },
                'priority': 1,
                'risk_weight': 2.5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule7.name}'))

        # Rule 8: Velocity Detection (Issue #25)
        rule8, created = Rule.objects.get_or_create(
            name='Transaction Velocity Detection',
            defaults={
                'description': 'تشخیص سرعت غیرعادی تراکنش‌ها در بازه زمانی',
                'rule_type': 'VELOCITY',
                'status': 'ACTIVE',
                'configuration': {
                    'window_hours': 24,
                    'count_threshold': 15,
                    'amount_threshold': 100_000_000,  # 100M IRR/day
                },
                'priority': 2,
                'risk_weight': 1.8,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule8.name}'))

        # Rule 9: Fund Concentration (Issue #24)
        rule9, created = Rule.objects.get_or_create(
            name='Fund Concentration Detection',
            defaults={
                'description': 'تشخیص تمرکز وجوه — بخش بزرگی از خروجی به یک حساب واحد',
                'rule_type': 'CONCENTRATION',
                'status': 'ACTIVE',
                'configuration': {
                    'lookback_days': 30,
                    'concentration_ratio': 0.70,
                    'min_total_amount': 10_000_000,  # 10M IRR minimum total
                },
                'priority': 3,
                'risk_weight': 1.7,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule9.name}'))

        # Rule 10: Sanctioned Countries Cross-Border (Issue #27)
        rule10, created = Rule.objects.get_or_create(
            name='Sanctioned Country Transfer',
            defaults={
                'description': 'تشخیص انتقال وجه به کشورهای تحت تحریم سازمان ملل/FATF',
                'rule_type': 'SANCTIONED',
                'status': 'ACTIVE',
                'configuration': {
                    'sanctioned_countries': ['KP', 'SD', 'SY', 'SO', 'LY'],
                },
                'priority': 1,
                'risk_weight': 3.0,  # Highest weight
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule10.name}'))

        # Rule 11: CTR Threshold — Bank Markazi standard (Issue #32)
        rule11, created = Rule.objects.get_or_create(
            name='CTR Threshold (Bank Markazi)',
            defaults={
                'description': 'آستانه گزارش تراکنش کلان — ۵۰۰ میلیون ریال (بر اساس دستورالعمل بانک مرکزی)',
                'rule_type': 'THRESHOLD',
                'status': 'ACTIVE',
                'configuration': {
                    'amount_threshold': 500_000_000,  # 500M IRR = ~50M Toman
                },
                'priority': 1,
                'risk_weight': 1.5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule11.name}'))

        # Rule 12: Night/Weekend Activity (Issue #23)
        rule12, created = Rule.objects.get_or_create(
            name='Night/Weekend Activity Detection',
            defaults={
                'description': 'تشخیص تراکنش‌های مشکوک در ساعات شبانه و روزهای تعطیل (پنج‌شنبه و جمعه)',
                'rule_type': 'NIGHT_WEEKEND',
                'status': 'ACTIVE',
                'configuration': {
                    'night_start_hour': 22,
                    'night_end_hour': 7,
                    'night_amount_threshold': 50_000_000,
                    'weekend_amount_threshold': 100_000_000,
                },
                'priority': 2,
                'risk_weight': 1.5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule12.name}'))

        # Rule 13: Round Amount / Structuring (Issue #24)
        rule13, created = Rule.objects.get_or_create(
            name='Round Amount Structuring',
            defaults={
                'description': 'تشخیص الگوی تجزیه وجه با مبالغ گرد (ساختاربندی)',
                'rule_type': 'ROUND_AMOUNT',
                'status': 'ACTIVE',
                'configuration': {
                    'round_thresholds': [10_000_000, 50_000_000, 100_000_000, 500_000_000],
                    'min_amount': 10_000_000,
                    'lookback_days': 30,
                    'min_round_count': 3,
                },
                'priority': 2,
                'risk_weight': 2.0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule13.name}'))

        # Rule 14: New Account Velocity (Issue #26)
        rule14, created = Rule.objects.get_or_create(
            name='New Account Velocity',
            defaults={
                'description': 'کنترل تعداد و حجم تراکنش‌های حساب‌های تازه‌تأسیس (۳۰ و ۹۰ روز اول)',
                'rule_type': 'NEW_ACCOUNT',
                'status': 'ACTIVE',
                'configuration': {
                    'new_account_days_30': 30,
                    'new_account_days_90': 90,
                    'max_daily_count_30d': 5,
                    'max_daily_amount_30d': 50_000_000,
                    'max_daily_count_90d': 10,
                    'max_daily_amount_90d': 200_000_000,
                },
                'priority': 2,
                'risk_weight': 2.0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule14.name}'))

        self.stdout.write(self.style.SUCCESS('Iranian market rules created successfully.'))
        self._create_fraud_rules()

    def _create_fraud_rules(self):
        """
        Create Didebaan Fraud & Abuse Intelligence rules: device sharing,
        merchant abuse, and BNPL default risk.
        """

        # Rule 15: Device Shared Across Accounts
        rule15, created = Rule.objects.get_or_create(
            name='Device Shared Across Accounts',
            defaults={
                'description': 'تشخیص استفاده از یک دستگاه برای چند حساب متفاوت — نشانه حلقه حساب‌های جعلی',
                'rule_type': 'DEVICE_SHARING',
                'status': 'ACTIVE',
                'configuration': {
                    'lookback_days': 30,
                    'max_distinct_customers': 3,
                },
                'priority': 2,
                'risk_weight': 2.0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule15.name}'))

        # Rule 16: Merchant Fake-purchase / Chargeback Abuse
        rule16, created = Rule.objects.get_or_create(
            name='Merchant Fake-purchase Abuse',
            defaults={
                'description': 'تشخیص مرچنت‌های با نرخ بالای چارجبک/بازگشت وجه یا جهش ناگهانی حجم تراکنش',
                'rule_type': 'MERCHANT_ABUSE',
                'status': 'ACTIVE',
                'configuration': {
                    'chargeback_rate_threshold': 5.0,
                    'refund_rate_threshold': 15.0,
                    'volume_lookback_days': 30,
                    'volume_spike_multiplier': 3.0,
                },
                'priority': 2,
                'risk_weight': 1.8,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule16.name}'))

        # Rule 17: BNPL Default Risk Pattern
        rule17, created = Rule.objects.get_or_create(
            name='BNPL Default Risk Pattern',
            defaults={
                'description': 'تشخیص الگوی ریسک نکول در خریدهای اعتباری (BNPL) — خرید زیاد، بازپرداخت کم',
                'rule_type': 'BNPL_RISK',
                'status': 'ACTIVE',
                'configuration': {
                    'lookback_days': 90,
                    'max_open_purchases': 3,
                    'min_repayment_ratio': 0.3,
                },
                'priority': 1,
                'risk_weight': 2.2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created rule: {rule17.name}'))

        self.stdout.write(self.style.SUCCESS('Didebaan fraud & abuse rules created successfully.'))
