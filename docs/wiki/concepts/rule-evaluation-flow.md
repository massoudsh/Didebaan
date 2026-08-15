# مسیر ارزیابی یک تراکنش (Rule Evaluation Flow)

> مسیر کامل از ثبت یک تراکنش تا تولید هشدار.

## مراحل
1. یک `Transaction` ساخته/ثبت می‌شود (مستقیم از API یا sync/async).
2. [[entities/transaction-monitor]] فراخوانی می‌شود (`monitor_transaction` یا نسخه async در `tasks.py`).
3. `TransactionMonitor` از [[entities/rule-engine]] singleton (`get_rule_engine()`) می‌خواهد `evaluate_transaction(transaction)` را اجرا کند.
4. `RuleEngine.active_rules` (property، همیشه fresh از دیتابیس — نه cache شده) همه‌ی `Rule` هایی با `status='ACTIVE'` را برمی‌گرداند، مرتب بر اساس `priority`.
5. برای هر قانون، بسته به `rule_type` تابع `_evaluate_*_rule` مربوطه صدا زده می‌شود (`_evaluate_pep_rule`, `_evaluate_device_sharing_rule`, ...) و یک `{triggered, reason, risk_score}` برمی‌گرداند.
6. اگر `triggered=True`: قانون به `triggered_rules` اضافه می‌شود، `reason` جمع می‌شود، و `risk_score * rule.risk_weight` به `total_risk_score` اضافه می‌شود.
7. `TransactionMonitor` نتیجه را روی `Transaction` ذخیره می‌کند (`risk_score`, `is_suspicious`, `flagged_reasons`) و `Customer.risk_score` را به‌روز می‌کند.
8. اگر مشکوک باشد، [[entities/alert-generator]] یک `Alert` می‌سازد — شامل `explanation` (به [[concepts/explainable-ai]]) و `triggered_rules`.
9. اگر severity بالا باشد، `notification_service` ایمیل/webhook می‌فرستد.

## نکته‌ی مهم معماری
موتور قانون یک **process-wide singleton** است (`get_rule_engine()`). برای اینکه قوانین جدید/ویرایش‌شده همیشه دیده شوند، `active_rules` باید هر بار queryset تازه برگرداند — این یک باگ واقعی بود (queryset cache می‌شد و بعد از اولین ارزیابی منجمد می‌ماند) که رفع شده. جزئیات در [[entities/rule-engine]].

## منابع کد
- `backend/aml/services/transaction_monitor.py`
- `backend/aml/rules/aml_rules.py`
- `backend/aml/services/alert_generator.py`
