"""
DRF Serializers for AML models
"""
from rest_framework import serializers
from .models import Customer, Transaction, Alert, RiskScore, Rule, Report, AuditLog, Device, Merchant


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    
    class Meta:
        model = Customer
        fields = [
            'id', 'customer_id', 'first_name', 'last_name', 'email', 'phone',
            'customer_type', 'date_of_birth', 'national_id', 'address',
            'city', 'province', 'country', 'registration_date', 'is_active',
            'current_risk_level', 'risk_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model (fraud/abuse device fingerprinting)"""

    class Meta:
        model = Device
        fields = [
            'id', 'device_id', 'fingerprint_hash', 'device_type', 'os',
            'browser', 'ip_address', 'is_emulator', 'is_rooted',
            'first_seen_at', 'last_seen_at'
        ]
        read_only_fields = ['id', 'first_seen_at', 'last_seen_at']


class MerchantSerializer(serializers.ModelSerializer):
    """Serializer for Merchant model (fraud/abuse merchant risk)"""

    class Meta:
        model = Merchant
        fields = [
            'id', 'merchant_id', 'name', 'category', 'risk_score',
            'chargeback_rate', 'refund_rate', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    device_detail = DeviceSerializer(source='device', read_only=True)
    merchant_detail = MerchantSerializer(source='merchant', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'customer', 'customer_detail',
            'transaction_type', 'amount', 'currency', 'status',
            'sender_account', 'receiver_account', 'receiver_name',
            'receiver_country', 'device', 'device_detail', 'merchant',
            'merchant_detail', 'description', 'transaction_date',
            'risk_score', 'is_suspicious', 'flagged_reasons',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'risk_score', 'is_suspicious',
                           'flagged_reasons', 'created_at', 'updated_at']


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for Rule model"""
    
    class Meta:
        model = Rule
        fields = [
            'id', 'name', 'description', 'rule_type', 'status',
            'configuration', 'priority', 'risk_weight',
            'created_by', 'created_at', 'updated_at', 'last_applied_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_applied_at']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model"""
    transaction_detail = TransactionSerializer(source='transaction', read_only=True)
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    triggered_rules_detail = RuleSerializer(source='triggered_rules', many=True, read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'alert_id', 'transaction', 'transaction_detail',
            'customer', 'customer_detail', 'severity', 'status',
            'title', 'description', 'triggered_rules', 'triggered_rules_detail',
            'risk_score', 'explanation', 'reviewed_by', 'reviewed_at', 'review_notes',
            'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'alert_id', 'created_at', 'updated_at']


class RiskScoreSerializer(serializers.ModelSerializer):
    """Serializer for RiskScore model"""
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    
    class Meta:
        model = RiskScore
        fields = [
            'id', 'customer', 'customer_detail', 'transaction',
            'score_type', 'score', 'factors', 'calculation_method',
            'calculated_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model"""
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_id', 'report_type', 'status', 'title', 'description',
            'report_data', 'related_alerts', 'related_transactions',
            'related_customers', 'file_path', 'file_format',
            'submitted_by', 'submitted_at', 'regulatory_body',
            'period_start', 'period_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'report_id', 'created_at', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log (compliance API)."""
    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'method', 'path', 'user', 'ip_address',
            'status_code', 'user_agent', 'request_body'
        ]
        read_only_fields = fields


class MonitorTransactionSerializer(serializers.Serializer):
    """Serializer for transaction monitoring endpoint"""
    transaction_id = serializers.CharField(required=True)


class ReviewAlertSerializer(serializers.Serializer):
    """Serializer for alert review endpoint"""
    status = serializers.ChoiceField(
        choices=['RESOLVED', 'FALSE_POSITIVE', 'ESCALATED', 'UNDER_REVIEW'],
        required=True
    )
    notes = serializers.CharField(required=True, allow_blank=True)


class GenerateReportSerializer(serializers.Serializer):
    """Serializer for report generation endpoint"""
    report_type = serializers.ChoiceField(
        choices=['SAR', 'CTR', 'CUSTOM'],
        required=True
    )
    period_start = serializers.DateTimeField(required=True)
    period_end = serializers.DateTimeField(required=True)
    format = serializers.ChoiceField(
        choices=['JSON', 'CSV', 'PDF'],
        default='JSON'
    )
    threshold = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        required=False,
        help_text="Required for CTR reports"
    )

