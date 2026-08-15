# Schema — قوانین ویکی این پروژه

منبع اصلی قوانین: `/AGENTS.md` (ریشه‌ی ریپو). این فایل فقط جمع‌بندی سریع + نکات مخصوص Didebaan است.

## قوانین کلی
همان قوانین `AGENTS.md` (بخش Vault Recipe) — شروع مکالمه از `overview.md`/`index.md`، آپدیت ویکی یک‌بار در پایان مکالمه بعد از تغییر معنایی کد، لینک‌های Obsidian-style `[[entities/xxx]]`.

## گروه‌بندی entity های این پروژه
- **Data models** (`backend/aml/models.py`) → هرکدام یک صفحه در `entities/`.
- **Services** (`backend/aml/services/*.py`, `backend/aml/rules/aml_rules.py`) → منطق تجاری، هرکدام یک صفحه در `entities/`.
- **Concepts** (`concepts/`) → flowهای چندجزئی که چند entity را به هم وصل می‌کنند (مثل مسیر کامل یک تراکنش از ثبت تا هشدار).

## نام‌گذاری
- فایل مدل‌ها: همنام مدل، lowercase (`customer.md`, `rule.md`, `device.md`).
- فایل سرویس‌ها: همنام کلاس، kebab-case (`rule-engine.md`, `transaction-monitor.md`, `alert-generator.md`).

## منابع کد پایه (مسیرها نسبت به ریشه‌ی ریپو)
- `backend/aml/models.py` — همه مدل‌های دیتا
- `backend/aml/views.py` — ViewSetها و endpoint سفارشی (`export`, `statistics`, ...)
- `backend/aml/urls.py` — ثبت router و مسیرهای API
- `backend/aml/rules/aml_rules.py` — `RuleEngine` + `ExtendedRuleEngine` (موتور قوانین)
- `backend/aml/services/` — `alert_generator.py`, `transaction_monitor.py`, `risk_scorer.py`, `report_generator.py`, `notification_service.py`
- `backend/aml/ml/model.py` — `MLRiskModel` (لایه ML اختیاری روی امتیاز ریسک)
- `backend/aml/tasks.py` — تسک‌های Celery (پردازش async، گزارش روزانه)
- `backend/aml/middleware.py` — `AuditTrailMiddleware`
- `backend/aml/tests.py` — تست‌های backend (منبع رفتار مورد انتظار)
