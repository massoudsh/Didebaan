# Alert

> هشدار تولیدشده برای یک تراکنش مشکوک — شامل توضیح تصمیم (explainable AI).

## مسئولیت‌ها
- نگهداری `severity`, `status` (workflow: `OPEN` → `UNDER_REVIEW` → `RESOLVED`/`FALSE_POSITIVE`/`ESCALATED`)، `risk_score`.
- لینک به قوانینی که آن را trigger کرده‌اند (`triggered_rules`, ManyToMany به [[entities/rule]]).
- فیلد `explanation` (JSON list): شکست قانون‌به‌قانون علت هشدار — به‌ازای هر قانون trigger‌شده یک آیتم `{rule_name, rule_type, reason, weight}` (به [[concepts/explainable-ai]] نگاه کنید).

## وابستگی‌ها
- [[entities/transaction]] و [[entities/customer]] — هر Alert به هر دو لینک است.
- [[entities/alert-generator]] — تولید، escalate، false-positive-mark و review.
- `Notification` مدل + `notification_service` (`backend/aml/services/notification_service.py`) — هشدارهای severity بالا نوتیفیکیشن (ایمیل/webhook) می‌فرستند.

## قراردادها / Edge cases
- `alert_id` یکتا و indexed؛ ایندکس ترکیبی `(status, severity)` برای فیلترهای داشبورد.
- خروجی export (CSV/XLSX) از `AlertViewSet.export` — پارامتر کوئری `export_format` (نه `format`، چون `format` رزرو DRF برای content negotiation است).

## منابع کد
- `backend/aml/models.py:263` — تعریف مدل
- `backend/aml/views.py` (`AlertViewSet`, action `export`) — `/api/alerts/export/?export_format=csv|xlsx`
- `backend/aml/serializers.py` — `AlertSerializer`
