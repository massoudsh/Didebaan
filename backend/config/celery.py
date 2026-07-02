"""
Celery application configuration for Regalion AML System.
Issue #14: Async transaction monitoring via Celery + Redis.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('regalion_aml')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# Optional: Celery Beat schedule for periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Run batch monitoring every 5 minutes
    'monitor-pending-transactions': {
        'task': 'aml.tasks.monitor_pending_transactions',
        'schedule': crontab(minute='*/5'),
    },
    # Daily risk report at 00:05
    'daily-risk-report': {
        'task': 'aml.tasks.generate_daily_risk_report',
        'schedule': crontab(hour=0, minute=5),
    },
}
