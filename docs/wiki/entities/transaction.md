# Transaction

> رکورد یک تراکنش مالی — هسته‌ی نظارت و ارزیابی ریسک.

## مسئولیت‌ها
- نگهداری جزئیات تراکنش (مبلغ، نوع، وضعیت، طرفین، کشور دریافت‌کننده).
- لینک اختیاری به [[entities/device]] و [[entities/merchant]] برای سیگنال‌های fraud/abuse.
- نگهداری خروجی ارزیابی ریسک: `risk_score`, `is_suspicious`, `flagged_reasons`.

## وابستگی‌ها
- [[entities/customer]] — هر تراکنش به یک مشتری تعلق دارد (`CASCADE`).
- [[entities/rule-engine]] — ورودی اصلی `evaluate_transaction()`.
- [[entities/transaction-monitor]] — orchestration کامل: دریافت تراکنش → ارزیابی → آپدیت ریسک مشتری → تولید هشدار.
- [[entities/alert]] — اگر مشکوک تشخیص داده شود، Alert تولید می‌شود.

## انواع تراکنش
`DEPOSIT`, `WITHDRAWAL`, `TRANSFER`, `PAYMENT`, `REFUND`, `BNPL_PURCHASE`, `BNPL_REPAYMENT`.

## قراردادها / Edge cases
- `transaction_id` یکتا و indexed؛ `amount` نمی‌تواند منفی باشد.
- `currency` پیش‌فرض `'IRR'`.
- ایندکس ترکیبی `(customer, transaction_date)` برای کوئری‌های velocity/behavioral rules.

## منابع کد
- `backend/aml/models.py:133` — تعریف مدل
- `backend/aml/services/transaction_monitor.py` — orchestration نظارت
