# Rule

> تعریف قانون قابل‌پیکربندی AML/Fraud — پیکربندی به‌صورت JSON، بدون نیاز به دیپلوی کد.

## مسئولیت‌ها
- نگهداری `rule_type`، `configuration` (JSON آزاد)، `priority`، `risk_weight`، `status` (`ACTIVE`/`INACTIVE`/`DRAFT`).
- نسخه‌بندی: هر ذخیره یک اسنپ‌شات در `RuleVersion` (پایین همین صفحه) می‌سازد (audit trail کامل).

## انواع قانون (`rule_type`)
پایه: `THRESHOLD`, `PATTERN`, `BEHAVIORAL`, `GEOGRAPHIC`
بازار ایران: `PEP`, `VELOCITY`, `CONCENTRATION`, `SANCTIONED`, `NIGHT_WEEKEND`, `ROUND_AMOUNT`, `NEW_ACCOUNT`
Fraud/Abuse (پیوت Didebaan): `DEVICE_SHARING`, `MERCHANT_ABUSE`, `BNPL_RISK`

## وابستگی‌ها
- [[entities/rule-engine]] — مصرف‌کننده اصلی؛ برای هر نوع یک تابع `_evaluate_*_rule` دارد.
- [[entities/alert]] — از طریق `triggered_rules` (ManyToMany) به هشدارهای تولیدشده لینک می‌شود.

## RuleVersion
اسنپ‌شات immutable هر بار ذخیره‌ی Rule (`rule`, `version_number`, تمام فیلدهای وقتِ ذخیره، `changed_by`, `change_notes`). برای audit trail رگولاتوری.

## قراردادها / Edge cases
- فقط قوانین با `status='ACTIVE'` توسط موتور fetch می‌شوند (به‌صورت fresh query هر بار — نه cache شده؛ به [[concepts/rule-evaluation-flow]] نگاه کنید).
- `priority` بین ۱ تا ۱۰؛ `risk_weight` بین ۰ تا ۱۰ (ضریب روی امتیاز خام هر قانون).

## منابع کد
- `backend/aml/models.py:201` — تعریف مدل `Rule`
- `backend/aml/models.py:453` — `RuleVersion`
- `backend/aml/management/` — دستور `create_sample_rules`
