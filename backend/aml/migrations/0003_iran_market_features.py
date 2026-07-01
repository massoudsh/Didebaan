"""
Migration 0003: Iranian market features
- Add is_pep (PEP flag) to Customer (#23)
- Add version_number to Rule (#31)
- Add RuleVersion model (#31)
- Add ThresholdConfig model (#32)
- Add ReportComment model (#33)
- Add Notification model (#30)
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aml', '0002_add_audit_log'),
    ]

    operations = [
        # Issue #23: PEP flag on Customer
        migrations.AddField(
            model_name='customer',
            name='is_pep',
            field=models.BooleanField(
                default=False,
                verbose_name='شخص در معرض خطر سیاسی (PEP)',
                help_text='Politically Exposed Person — وزرا، نمایندگان، مقامات ارشد و خانواده درجه اول آن‌ها',
            ),
        ),

        # Issue #31: version_number on Rule
        migrations.AddField(
            model_name='rule',
            name='version_number',
            field=models.PositiveIntegerField(default=1, verbose_name='شماره نسخه'),
        ),

        # Issue #31: RuleVersion model
        migrations.CreateModel(
            name='RuleVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField(default=1)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('configuration', models.JSONField(default=dict)),
                ('status', models.CharField(max_length=20)),
                ('priority', models.IntegerField(default=1)),
                ('risk_weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=5)),
                ('changed_by', models.CharField(blank=True, max_length=100)),
                ('change_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('rule', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='versions',
                    to='aml.rule',
                )),
            ],
            options={
                'ordering': ['-version_number'],
                'unique_together': {('rule', 'version_number')},
            },
        ),

        # Issue #32: ThresholdConfig model
        migrations.CreateModel(
            name='ThresholdConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='نام')),
                ('threshold_type', models.CharField(
                    choices=[
                        ('TRANSACTION_AMOUNT', 'حد مبلغ تراکنش'),
                        ('DAILY_AMOUNT', 'حد مبلغ روزانه'),
                        ('DAILY_COUNT', 'حد تعداد روزانه'),
                        ('CROSS_BORDER_AMOUNT', 'حد تراکنش بین‌المللی'),
                        ('STRUCTURING_AMOUNT', 'حد تشخیص تجزیه (Structuring)'),
                        ('CTR_THRESHOLD', 'آستانه گزارش تراکنش کلان (CTR)'),
                        ('SAR_RISK_SCORE', 'آستانه گزارش تراکنش مشکوک (SAR)'),
                    ],
                    max_length=50,
                    verbose_name='نوع آستانه',
                )),
                ('value', models.DecimalField(decimal_places=2, max_digits=20, verbose_name='مقدار (ریال)')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('updated_by', models.CharField(blank=True, max_length=100, verbose_name='ویرایش توسط')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'آستانه پیکربندی',
                'verbose_name_plural': 'آستانه‌های پیکربندی',
                'ordering': ['threshold_type', 'name'],
            },
        ),

        # Issue #33: ReportComment model
        migrations.CreateModel(
            name='ReportComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment_type', models.CharField(
                    choices=[
                        ('COMMENT', 'یادداشت'),
                        ('STATUS_CHANGE', 'تغییر وضعیت'),
                        ('SUBMISSION', 'ارسال به رگولاتور'),
                        ('APPROVAL', 'تایید'),
                        ('REJECTION', 'رد'),
                    ],
                    default='COMMENT',
                    max_length=20,
                    verbose_name='نوع',
                )),
                ('previous_status', models.CharField(blank=True, max_length=20, verbose_name='وضعیت قبلی')),
                ('new_status', models.CharField(blank=True, max_length=20, verbose_name='وضعیت جدید')),
                ('comment', models.TextField(verbose_name='متن یادداشت')),
                ('author', models.CharField(max_length=100, verbose_name='نویسنده')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('report', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='aml.report',
                    verbose_name='گزارش',
                )),
            ],
            options={
                'verbose_name': 'یادداشت گزارش',
                'verbose_name_plural': 'یادداشت‌های گزارش',
                'ordering': ['-created_at'],
            },
        ),

        # Issue #30: Notification model
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(
                    choices=[('EMAIL', 'ایمیل'), ('WEBHOOK', 'Webhook'), ('SMS', 'پیامک')],
                    max_length=20,
                    verbose_name='نوع اعلان',
                )),
                ('status', models.CharField(
                    choices=[('PENDING', 'در انتظار'), ('SENT', 'ارسال شد'), ('FAILED', 'ناموفق')],
                    default='PENDING',
                    max_length=20,
                    verbose_name='وضعیت',
                )),
                ('recipient', models.CharField(max_length=500, verbose_name='گیرنده')),
                ('subject', models.CharField(blank=True, max_length=500, verbose_name='موضوع')),
                ('message', models.TextField(verbose_name='متن')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='زمان ارسال')),
                ('error_message', models.TextField(blank=True, verbose_name='خطا')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('related_alert', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='aml.alert',
                    verbose_name='هشدار مرتبط',
                )),
            ],
            options={
                'verbose_name': 'اعلان',
                'verbose_name_plural': 'اعلان‌ها',
                'ordering': ['-created_at'],
            },
        ),
    ]
