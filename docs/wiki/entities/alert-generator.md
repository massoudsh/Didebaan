# AlertGenerator

> ساخت، بررسی (review)، escalate و false-positive-mark کردن هشدارها؛ + آمار هشدارها.

## مسئولیت‌ها
- ساخت [[entities/alert]] از نتیجه‌ی [[entities/rule-engine]] (شامل ساخت `explanation` — به [[concepts/explainable-ai]]).
- `escalate_alert`, `mark_false_positive`, `review_alert` — تغییر `status` و ثبت `reviewed_by`/`review_notes`.
- `get_alerts_statistics(days)` و `get_open_alerts_count()` — پشت endpointهای `/api/alerts/statistics/` و `/api/alerts/open_count/`.
- singleton از طریق `get_alert_generator()`.

## وابستگی‌ها
- [[entities/transaction-monitor]] — فراخواننده اصلی.
- `backend/aml/services/notification_service.py` — بعد از ساخت Alert با severity بالا، نوتیفیکیشن می‌فرستد.

## منابع کد
- `backend/aml/services/alert_generator.py:17` — `class AlertGenerator`
- `backend/aml/services/alert_generator.py:318` — `get_alert_generator()`
