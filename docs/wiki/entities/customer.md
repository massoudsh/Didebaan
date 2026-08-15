# Customer

> مشتری/کاربر پلتفرم — داده KYC و وضعیت ریسک.

## مسئولیت‌ها
- نگهداری اطلاعات هویتی/KYC (نام، ایمیل، ملیت، تاریخ تولد، کد ملی، آدرس).
- نگهداری `current_risk_level` و `risk_score` (به‌روزرسانی‌شده توسط [[entities/transaction-monitor]] بعد از هر تراکنش).
- پرچم `is_pep` (Politically Exposed Person) — ورودی مستقیم به [[concepts/rule-evaluation-flow]] از طریق `PEP` rule type.

## وابستگی‌ها
- [[entities/transaction]] — یک مشتری چند تراکنش دارد (`related_name='transactions'`).
- [[entities/alert]] — هشدارها به مشتری لینک می‌شوند.
- `RiskScorer` (`backend/aml/services/risk_scorer.py`) — منبع محاسبه و به‌روزرسانی `risk_score`.

## قراردادها / Edge cases
- `customer_id` و `email` یکتا و indexed هستند.
- `is_pep` مستقیماً روی مدل است (نه فقط migration) — قبلاً باگی بود که این فیلد فقط در migration اضافه شده بود ولی روی مدل نبود و باعث کرش `NOT NULL` در هر بار ساخت مشتری می‌شد؛ رفع شد.
- `country` پیش‌فرض `'IR'`.

## منابع کد
- `backend/aml/models.py:10` — تعریف مدل
- `backend/aml/migrations/0003_iran_market_features.py` — افزودن `is_pep`
