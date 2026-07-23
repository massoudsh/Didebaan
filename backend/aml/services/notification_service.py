"""
Notification Service — Issue #30
ارسال اعلان‌های ایمیل و Webhook برای هشدارهای با شدت بالا

پیکربندی در settings:
  AML_NOTIFY_EMAIL_RECIPIENTS: list of emails
  AML_NOTIFY_WEBHOOK_URL: URL for HTTP POST
  AML_NOTIFY_SEVERITY_THRESHOLD: minimum severity to trigger (default: HIGH)
"""
import json
import logging
from datetime import datetime
from typing import List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('aml')

# Default configuration (override in settings.py)
NOTIFY_EMAIL_RECIPIENTS: List[str] = getattr(settings, 'AML_NOTIFY_EMAIL_RECIPIENTS', [])
NOTIFY_WEBHOOK_URL: Optional[str] = getattr(settings, 'AML_NOTIFY_WEBHOOK_URL', None)
NOTIFY_SEVERITY_THRESHOLD: str = getattr(settings, 'AML_NOTIFY_SEVERITY_THRESHOLD', 'HIGH')

SEVERITY_ORDER = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']


def _severity_meets_threshold(severity: str, threshold: str) -> bool:
    try:
        return SEVERITY_ORDER.index(severity) >= SEVERITY_ORDER.index(threshold)
    except ValueError:
        return False


def notify_alert(alert) -> None:
    """
    Send notifications for a new high-severity alert.
    Called automatically by AlertGenerator after creating alerts.

    Args:
        alert: Alert model instance
    """
    from aml.models import Notification

    if not _severity_meets_threshold(alert.severity, NOTIFY_SEVERITY_THRESHOLD):
        return

    subject = f"[Didebaan AML] هشدار {alert.severity}: {alert.alert_id}"
    message = (
        f"هشدار جدید ثبت شد.\n\n"
        f"شناسه هشدار: {alert.alert_id}\n"
        f"مشتری: {alert.customer.customer_id}\n"
        f"شدت: {alert.severity}\n"
        f"امتیاز ریسک: {alert.risk_score}\n"
        f"تراکنش: {alert.transaction.transaction_id}\n"
        f"مبلغ: {alert.transaction.amount:,.0f} {alert.transaction.currency}\n"
        f"تاریخ: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"برای بررسی به پنل مدیریت مراجعه کنید."
    )

    # Email notifications
    for recipient in NOTIFY_EMAIL_RECIPIENTS:
        notif = Notification.objects.create(
            notification_type='EMAIL',
            recipient=recipient,
            subject=subject,
            message=message,
            related_alert=alert,
        )
        _send_email(notif)

    # Webhook notification
    if NOTIFY_WEBHOOK_URL:
        notif = Notification.objects.create(
            notification_type='WEBHOOK',
            recipient=NOTIFY_WEBHOOK_URL,
            subject=subject,
            message=message,
            related_alert=alert,
        )
        _send_webhook(notif)


def _send_email(notification) -> None:
    """Send email via Django's email backend."""
    try:
        from django.core.mail import send_mail
        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@didebaan-aml.ir'),
            recipient_list=[notification.recipient],
            fail_silently=False,
        )
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])
        logger.info(f"Email notification sent to {notification.recipient} for alert {notification.related_alert_id}")
    except Exception as exc:
        notification.status = 'FAILED'
        notification.error_message = str(exc)
        notification.save(update_fields=['status', 'error_message'])
        logger.error(f"Email notification failed: {exc}")


def _send_webhook(notification) -> None:
    """Send JSON POST to webhook URL."""
    try:
        payload = {
            'event': 'alert.created',
            'alert_id': str(notification.related_alert.alert_id) if notification.related_alert else None,
            'severity': notification.related_alert.severity if notification.related_alert else None,
            'risk_score': float(notification.related_alert.risk_score) if notification.related_alert else None,
            'customer_id': str(notification.related_alert.customer.customer_id) if notification.related_alert else None,
            'timestamp': timezone.now().isoformat(),
            'system': 'Didebaan AML',
        }
        data = json.dumps(payload).encode('utf-8')
        req = Request(
            notification.recipient,
            data=data,
            headers={'Content-Type': 'application/json', 'User-Agent': 'Didebaan-AML/1.0'},
            method='POST',
        )
        with urlopen(req, timeout=10) as resp:
            resp.read()
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])
        logger.info(f"Webhook notification sent to {notification.recipient}")
    except (URLError, Exception) as exc:
        notification.status = 'FAILED'
        notification.error_message = str(exc)
        notification.save(update_fields=['status', 'error_message'])
        logger.error(f"Webhook notification failed: {exc}")
