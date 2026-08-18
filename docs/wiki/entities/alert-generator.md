# AlertGenerator

> ساخت، بررسی (review)، escalate و false-positive-mark کردن هشدارها؛ + آمار هشدارها.

## مسئولیت‌ها
- ساخت [[entities/alert]] از نتیجه‌ی [[entities/rule-engine]] (شامل ساخت `explanation` — به [[concepts/explainable-ai]]).
- `escalate_alert`, `mark_false_positive`, `review_alert` — تغییر `status` و ثبت `reviewed_by`/`review_notes`؛ هر تغییر status یک `AlertComment` نوع `STATUS_CHANGE` هم ثبت می‌کند (`_log_status_change`).
- `assign_alert(alert, assigned_to, assigned_by, notes)` (#39) — ارجاع/لغو ارجاع هشدار به بررسی‌کننده؛ `assigned_to=''` یعنی unassign. یک `AlertComment` نوع `ASSIGNMENT` ثبت می‌کند.
- `add_comment(alert, author, comment)` (#39) — یادداشت آزاد در تاریخچه‌ی بررسی (`AlertComment` نوع `COMMENT`).
- `get_alerts_statistics(days)` و `get_open_alerts_count()` — پشت endpointهای `/api/alerts/statistics/` و `/api/alerts/open_count/`.
- singleton از طریق `get_alert_generator()`.

## وابستگی‌ها
- [[entities/transaction-monitor]] — فراخواننده اصلی.
- `backend/aml/services/notification_service.py` — بعد از ساخت Alert با severity بالا، نوتیفیکیشن می‌فرستد.
- `AlertComment` — تاریخچه‌ی بررسی/ارجاع که این سرویس آن را می‌نویسد.

## منابع کد
- `backend/aml/services/alert_generator.py:17` — `class AlertGenerator`
- `backend/aml/services/alert_generator.py` — `assign_alert`, `add_comment`, `_log_status_change`
- `backend/aml/services/alert_generator.py:318` — `get_alert_generator()`
