"""
Celery tasks for AML System — Issue #14: Async transaction monitoring.

Tasks run in the background via Celery workers so that API responses
remain fast; heavy monitoring logic executes out-of-band.

Usage:
    # Fire-and-forget (preferred from API views)
    monitor_transaction_async.delay(transaction_id)

    # Schedule batch run
    monitor_pending_transactions.delay()
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('aml')


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def monitor_transaction_async(self, transaction_id: str) -> dict:
    """
    Issue #14: Async transaction monitoring task.

    Runs the full AML monitoring pipeline (rule evaluation, risk scoring,
    alert generation) for a single transaction asynchronously.

    Args:
        transaction_id: The unique transaction_id (CharField) of the transaction.

    Returns:
        dict with monitoring result keys: risk_score, is_suspicious, should_alert.
    """
    from aml.models import Transaction
    from aml.services.transaction_monitor import get_transaction_monitor

    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
    except Transaction.DoesNotExist:
        logger.error(f"[task] Transaction {transaction_id} not found — aborting")
        return {'error': f'Transaction {transaction_id} not found'}

    try:
        monitor = get_transaction_monitor()
        result = monitor.monitor_transaction(transaction)
        logger.info(
            f"[task] Async monitoring done for {transaction_id}: "
            f"risk={result['risk_score']}, suspicious={result['is_suspicious']}"
        )
        return result
    except Exception as exc:
        logger.error(f"[task] Error monitoring {transaction_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def monitor_pending_transactions() -> dict:
    """
    Issue #14: Batch async monitoring task.

    Finds all PENDING or newly COMPLETED transactions that haven't been
    risk-scored yet and enqueues individual monitoring tasks for each.
    Designed to be run periodically (e.g., every 5 minutes via Celery Beat).

    Returns:
        dict with counts of enqueued and skipped transactions.
    """
    from aml.models import Transaction

    # Transactions created in the last 24h with no risk score
    cutoff = timezone.now() - timedelta(hours=24)
    unscored = Transaction.objects.filter(
        risk_score__isnull=True,
        status__in=['PENDING', 'COMPLETED'],
        created_at__gte=cutoff,
    ).values_list('transaction_id', flat=True)

    enqueued = 0
    for txn_id in unscored:
        monitor_transaction_async.delay(txn_id)
        enqueued += 1

    logger.info(f"[task] Batch monitor: enqueued {enqueued} transactions")
    return {'enqueued': enqueued}


@shared_task
def generate_daily_risk_report() -> dict:
    """
    Issue #14 (extended): Generate a daily summary of risk activity.

    Runs daily (Celery Beat) to produce stats on alerts triggered,
    high-risk customers, and suspicious transactions.

    Returns:
        dict with daily report summary.
    """
    from aml.models import Alert, Customer, Transaction
    from django.db.models import Count, Q

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    alerts_today = Alert.objects.filter(created_at__gte=today_start)
    severity_breakdown = dict(
        alerts_today.values('severity')
        .annotate(count=Count('id'))
        .values_list('severity', 'count')
    )

    suspicious_today = Transaction.objects.filter(
        created_at__gte=today_start, is_suspicious=True
    ).count()

    high_risk_customers = Customer.objects.filter(
        current_risk_level__in=['HIGH', 'CRITICAL']
    ).count()

    summary = {
        'date': today_start.strftime('%Y-%m-%d'),
        'alerts_total': alerts_today.count(),
        'alerts_by_severity': severity_breakdown,
        'suspicious_transactions': suspicious_today,
        'high_risk_customers': high_risk_customers,
    }

    logger.info(f"[task] Daily risk report: {summary}")
    return summary
