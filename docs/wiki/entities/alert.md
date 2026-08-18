# Alert

> هشدار تولیدشده برای یک تراکنش مشکوک — شامل توضیح تصمیم (explainable AI).

## مسئولیت‌ها
- نگهداری `severity`, `status` (workflow: `OPEN` → `UNDER_REVIEW` → `RESOLVED`/`FALSE_POSITIVE`/`ESCALATED`)، `risk_score`.
- لینک به قوانینی که آن را trigger کرده‌اند (`triggered_rules`, ManyToMany به [[entities/rule]]).
- فیلد `explanation` (JSON list): شکست قانون‌به‌قانون علت هشدار — به‌ازای هر قانون trigger‌شده یک آیتم `{rule_name, rule_type, reason, weight}` (به [[concepts/explainable-ai]] نگاه کنید).
- **Case management (#39):** `assigned_to`/`assigned_at` — بررسی‌کننده‌ی فعلی هشدار؛ `related_name='comments'` روی `AlertComment` برای تاریخچه‌ی کامل بررسی (COMMENT/ASSIGNMENT/STATUS_CHANGE).

## وابستگی‌ها
- [[entities/transaction]] و [[entities/customer]] — هر Alert به هر دو لینک است.
- [[entities/alert-generator]] — تولید، escalate، false-positive-mark، review، assign و ثبت comment.
- `Notification` مدل + `notification_service` (`backend/aml/services/notification_service.py`) — هشدارهای severity بالا نوتیفیکیشن (ایمیل/webhook) می‌فرستند.
- `AlertComment` (همان فایل `models.py`) — هر تغییر status یا assignment به‌صورت خودکار یک رکورد در این مدل ثبت می‌کند.

## قراردادها / Edge cases
- `alert_id` یکتا و indexed؛ ایندکس ترکیبی `(status, severity)` برای فیلترهای داشبورد.
- خروجی export (CSV/XLSX) از `AlertViewSet.export` — پارامتر کوئری `export_format` (نه `format`، چون `format` رزرو DRF برای content negotiation است).
- `assigned_to=''` یعنی بدون بررسی‌کننده (unassigned)؛ اکشن `assign` با ورودی خالی، unassign می‌کند و `assigned_at` را `None` می‌کند.

## منابع کد
- `backend/aml/models.py:263` — تعریف مدل `Alert`
- `backend/aml/models.py` (`AlertComment`, بعد از `Notification`) — تاریخچه‌ی بررسی/ارجاع
- `backend/aml/views.py` (`AlertViewSet`, actions `export`, `assign`, `comments`) — `/api/alerts/export/`, `/api/alerts/{alert_id}/assign/`, `/api/alerts/{alert_id}/comments/`
- `backend/aml/serializers.py` — `AlertSerializer`, `AlertCommentSerializer`, `AssignAlertSerializer`
