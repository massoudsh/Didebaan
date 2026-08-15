# TransactionMonitor

> orchestrator اصلی: یک تراکنش را می‌گیرد، ارزیابی می‌کند، ریسک مشتری را به‌روز می‌کند و در صورت لزوم Alert می‌سازد.

## مسئولیت‌ها
- دریافت `Transaction` → فراخوانی [[entities/rule-engine]] → ذخیره `risk_score`/`is_suspicious`/`flagged_reasons` روی تراکنش.
- به‌روزرسانی `risk_score` مشتری (رابطه با [[entities/customer]]).
- در صورت مشکوک بودن، فراخوانی [[entities/alert-generator]] برای ساخت Alert.
- singleton از طریق `get_transaction_monitor()`.

## وابستگی‌ها
- [[entities/rule-engine]] — منبع تشخیص trigger.
- [[entities/alert-generator]] — تولید هشدار در انتهای مسیر.
- `backend/aml/tasks.py` — نسخه‌ی async (`monitor_transaction_async`) همین سرویس را در Celery صدا می‌زند.

## منابع کد
- `backend/aml/services/transaction_monitor.py:19` — `class TransactionMonitor`
- `backend/aml/services/transaction_monitor.py:226` — `get_transaction_monitor()`
