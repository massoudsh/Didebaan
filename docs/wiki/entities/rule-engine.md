# RuleEngine / ExtendedRuleEngine

> موتور اصلی ارزیابی تراکنش در برابر همه‌ی قوانین فعال.

## مسئولیت‌ها
- `RuleEngine.evaluate_transaction(transaction)` → `(triggered_rules, reasons, total_risk_score)`.
- `RuleEngine` قوانین پایه را پیاده می‌کند (`THRESHOLD`, `PATTERN`, `BEHAVIORAL`, `GEOGRAPHIC`).
- `ExtendedRuleEngine(RuleEngine)` قوانین بازار ایران و fraud/abuse را اضافه می‌کند: `PEP`, `VELOCITY`, `CONCENTRATION`, `SANCTIONED`, `NIGHT_WEEKEND`, `ROUND_AMOUNT`, `NEW_ACCOUNT`, `DEVICE_SHARING`, `MERCHANT_ABUSE`, `BNPL_RISK`.
- Singleton سراسری از طریق `get_rule_engine()` — در پایین فایل `aml_rules.py` بار دوم override شده تا نمونه‌ی `ExtendedRuleEngine` برگرداند (نه `RuleEngine` پایه).

## وابستگی‌ها
- [[entities/rule]] — منبع قوانین فعال.
- [[entities/transaction-monitor]] — مصرف‌کننده اصلی (`self.rule_engine = get_rule_engine()`).
- [[concepts/rule-evaluation-flow]] — جزئیات کامل مسیر ارزیابی.

## قراردادها / Edge cases
- `active_rules` یک **property** است، نه attribute cache‌شده — هر بار queryset تازه از دیتابیس می‌گیرد. **این عمداً است**: چون موتور singleton سراسری است، اگر queryset یک‌بار در `__init__` cache می‌شد، همیشه به همان مجموعه‌ی قوانینِ لحظه‌ی اول ساخت پروسه منجمد می‌ماند (queryset پس از اولین iterate خودش را cache می‌کند) و قوانین جدید/ویرایش‌شده هرگز دیده نمی‌شدند. این باگ واقعی قبلاً وجود داشت و رفع شد.
- `reload_rules()` صرفاً یک لاگ می‌زند؛ چون هر فراخوانی `active_rules` خودش fresh است، نیازی به فراخوانی صریح این متد برای دیدن قوانین جدید نیست.
- خطای هر قانون در حلقه‌ی ارزیابی catch و log می‌شود؛ یک قانون خراب بقیه قوانین را متوقف نمی‌کند.

## منابع کد
- `backend/aml/rules/aml_rules.py:19` — `class RuleEngine`
- `backend/aml/rules/aml_rules.py:327` — `class ExtendedRuleEngine`
- `backend/aml/rules/aml_rules.py:813` — `get_rule_engine()` نهایی (override دوم)
