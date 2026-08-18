"""
Django Admin configuration for AML models.
Custom AdminSite with dashboard (counts, recent alerts); filters, actions, list display.
"""
from django.contrib import admin
from .models import Customer, Transaction, Alert, RiskScore, Rule, Report, Device, Merchant


# --- Custom AdminSite with dashboard (counts + recent alerts) ---

class AMLAdminSite(admin.AdminSite):
    site_header = 'Didebaan — موتور هوشمند تشخیص تقلب و سوءاستفاده'
    site_title = 'Didebaan'
    index_title = 'نمای کلی سامانه'

    index_template = 'admin/aml_index.html'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        from .models import Customer, Transaction, Alert, Rule
        extra_context['aml_customers_count'] = Customer.objects.count()
        extra_context['aml_transactions_count'] = Transaction.objects.count()
        extra_context['aml_alerts_open_count'] = Alert.objects.filter(status='OPEN').count()
        extra_context['aml_rules_count'] = Rule.objects.count()
        extra_context['aml_recent_alerts'] = Alert.objects.select_related(
            'customer', 'transaction'
        ).order_by('-created_at')[:10]
        return super().index(request, extra_context)


aml_admin_site = AMLAdminSite(name='aml_admin')


# --- Admin actions ---

def mark_alerts_resolved(modeladmin, request, queryset):
    updated = queryset.update(status='RESOLVED', reviewed_by=request.user.get_username())
    modeladmin.message_user(request, f'{updated} alert(s) marked as Resolved.')


mark_alerts_resolved.short_description = 'Mark selected as Resolved'


def mark_alerts_false_positive(modeladmin, request, queryset):
    updated = queryset.update(status='FALSE_POSITIVE', reviewed_by=request.user.get_username())
    modeladmin.message_user(request, f'{updated} alert(s) marked as False Positive.')


mark_alerts_false_positive.short_description = 'Mark selected as False Positive'


def escalate_alerts(modeladmin, request, queryset):
    updated = queryset.update(status='ESCALATED', reviewed_by=request.user.get_username())
    modeladmin.message_user(request, f'{updated} alert(s) escalated.')


escalate_alerts.short_description = 'Escalate selected alerts'


def set_customer_risk_high(modeladmin, request, queryset):
    updated = queryset.update(current_risk_level='HIGH')
    modeladmin.message_user(request, f'{updated} customer(s) set to High risk.')


set_customer_risk_high.short_description = 'Set risk level to High'


def set_customer_risk_critical(modeladmin, request, queryset):
    updated = queryset.update(current_risk_level='CRITICAL')
    modeladmin.message_user(request, f'{updated} customer(s) set to Critical risk.')


set_customer_risk_critical.short_description = 'Set risk level to Critical'


def activate_rules(modeladmin, request, queryset):
    updated = queryset.update(status='ACTIVE')
    modeladmin.message_user(request, f'{updated} rule(s) activated.')


activate_rules.short_description = 'Activate selected rules'


def deactivate_rules(modeladmin, request, queryset):
    updated = queryset.update(status='INACTIVE')
    modeladmin.message_user(request, f'{updated} rule(s) deactivated.')


deactivate_rules.short_description = 'Deactivate selected rules'


# --- ModelAdmins (registered on aml_admin_site) ---

class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'customer_id', 'first_name', 'last_name', 'email', 'current_risk_level',
        'risk_score', 'customer_type', 'registration_date', 'is_active'
    )
    list_filter = ('customer_type', 'current_risk_level', 'is_active', 'country')
    search_fields = ('customer_id', 'first_name', 'last_name', 'email', 'national_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    actions = [set_customer_risk_high, set_customer_risk_critical]


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'customer', 'transaction_type', 'amount', 'currency',
        'status', 'risk_score', 'is_suspicious', 'transaction_date'
    )
    list_filter = ('transaction_type', 'status', 'is_suspicious', 'currency')
    search_fields = ('transaction_id', 'customer__customer_id', 'sender_account', 'receiver_account')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-transaction_date',)
    date_hierarchy = 'transaction_date'
    list_per_page = 25
    list_select_related = ('customer',)


class RuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'status', 'priority', 'risk_weight', 'created_at')
    list_filter = ('rule_type', 'status')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_applied_at')
    ordering = ('priority', '-created_at')
    list_per_page = 25
    actions = [activate_rules, deactivate_rules]


class AlertAdmin(admin.ModelAdmin):
    list_display = (
        'alert_id', 'customer', 'transaction', 'severity', 'status',
        'risk_score', 'assigned_to', 'created_at', 'reviewed_by'
    )
    list_filter = ('severity', 'status', 'assigned_to', 'created_at')
    search_fields = ('alert_id', 'customer__customer_id', 'transaction__transaction_id', 'title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    filter_horizontal = ('triggered_rules',)
    list_per_page = 25
    list_select_related = ('customer', 'transaction')
    actions = [mark_alerts_resolved, mark_alerts_false_positive, escalate_alerts]


class RiskScoreAdmin(admin.ModelAdmin):
    list_display = ('customer', 'transaction', 'score_type', 'score', 'calculated_at')
    list_filter = ('score_type', 'calculated_at')
    search_fields = ('customer__customer_id', 'transaction__transaction_id')
    readonly_fields = ('id', 'created_at')
    ordering = ('-calculated_at',)
    date_hierarchy = 'calculated_at'
    list_per_page = 25
    list_select_related = ('customer', 'transaction')


class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'report_id', 'report_type', 'status', 'title', 'created_at',
        'submitted_at', 'submitted_by'
    )
    list_filter = ('report_type', 'status', 'file_format')
    search_fields = ('report_id', 'title', 'regulatory_body')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    filter_horizontal = ('related_alerts', 'related_transactions', 'related_customers')
    list_per_page = 25


# Register all models with the custom AML admin site
aml_admin_site.register(Customer, CustomerAdmin)
aml_admin_site.register(Transaction, TransactionAdmin)
aml_admin_site.register(Rule, RuleAdmin)
aml_admin_site.register(Alert, AlertAdmin)
aml_admin_site.register(RiskScore, RiskScoreAdmin)
aml_admin_site.register(Report, ReportAdmin)


# ─── New models for issues #30, #31, #32, #33, #39 ────────────────────────────

from .models import RuleVersion, ThresholdConfig, ReportComment, Notification, AlertComment


class ThresholdConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'threshold_type', 'value', 'is_active', 'updated_by', 'updated_at')
    list_filter = ('threshold_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)
    ordering = ('threshold_type', 'name')

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user.get_username()
        super().save_model(request, obj, form, change)


class RuleVersionAdmin(admin.ModelAdmin):
    list_display = ('rule', 'version_number', 'status', 'changed_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('rule__name', 'changed_by')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 25


class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ('report', 'comment_type', 'previous_status', 'new_status', 'author', 'created_at')
    list_filter = ('comment_type',)
    search_fields = ('report__report_id', 'author', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 25


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'recipient', 'subject', 'status', 'related_alert', 'created_at')
    list_filter = ('notification_type', 'status')
    search_fields = ('recipient', 'subject')
    readonly_fields = ('created_at', 'sent_at')
    ordering = ('-created_at',)
    list_per_page = 25


class AlertCommentAdmin(admin.ModelAdmin):
    list_display = ('alert', 'comment_type', 'author', 'created_at')
    list_filter = ('comment_type',)
    search_fields = ('alert__alert_id', 'author', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 25


aml_admin_site.register(ThresholdConfig, ThresholdConfigAdmin)
aml_admin_site.register(RuleVersion, RuleVersionAdmin)
aml_admin_site.register(ReportComment, ReportCommentAdmin)
aml_admin_site.register(Notification, NotificationAdmin)
aml_admin_site.register(AlertComment, AlertCommentAdmin)


# ─── Fraud & Abuse Intelligence models (Didebaan pivot) ──────────────────────

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'device_type', 'os', 'browser', 'is_emulator', 'is_rooted', 'last_seen_at')
    list_filter = ('device_type', 'is_emulator', 'is_rooted')
    search_fields = ('device_id', 'fingerprint_hash', 'ip_address')
    readonly_fields = ('first_seen_at', 'last_seen_at')
    ordering = ('-last_seen_at',)
    list_per_page = 25


class MerchantAdmin(admin.ModelAdmin):
    list_display = ('merchant_id', 'name', 'category', 'risk_score', 'chargeback_rate', 'refund_rate', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('merchant_id', 'name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-risk_score',)
    list_per_page = 25


aml_admin_site.register(Device, DeviceAdmin)
aml_admin_site.register(Merchant, MerchantAdmin)
