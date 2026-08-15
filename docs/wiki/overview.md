# Overview — Didebaan

دیده‌بان (**Didebaan**) یک موتور هوشمند تشخیص تقلب و سوءاستفاده (Fraud & Abuse Intelligence Engine) برای فین‌تک‌های ایرانی است. بک‌اند Django + Django REST Framework؛ روی پایه‌ی یک سیستم AML/CTR/SAR ساخته شده و بعداً برای fraud/abuse detection پیوت شده (پیوت از نام قبلی «Regalion»).

## دامنه‌ی کاری
- نظارت بر تراکنش‌ها و مشتریان در زمان واقعی، محاسبه امتیاز ریسک، تولید هشدار.
- ماژول‌های اصلی AML: PEP، velocity، concentration، sanctioned country، structuring/round-amount، night/weekend، new-account velocity.
- ماژول‌های fraud/abuse (پیوت Didebaan): **Device sharing** (حلقه‌های حساب مرتبط از طریق اشتراک دستگاه)، **Merchant abuse** (نرخ chargeback/refund غیرعادی)، **BNPL risk** (ریسک نکول در خرید اعتباری).
- **Explainable AI**: هر `Alert` یک `explanation` ساختاریافته دارد که شکست قانون‌به‌قانون علت هشدار را نشان می‌دهد.
- گزارش‌های رگولاتوری: SAR (Suspicious Activity Report) و CTR (Currency Transaction Report) + workflow کامنت/تایید.
- Audit trail کامل برای همه‌ی درخواست‌های API.

## پشته فناوری
Django 4.2 · DRF 3.14 · PostgreSQL (SQLite برای تست) · Celery + Redis (async، اختیاری) · pandas/openpyxl/reportlab برای export و گزارش.

## ساختار کد (`backend/aml/`)
- `models.py` — مدل‌های اصلی: `Customer`, `Device`, `Merchant`, `Transaction`, `Rule`, `Alert`, `RiskScore`, `Report`, `AuditLog`, `RuleVersion`, `ThresholdConfig`, `ReportComment`, `Notification`.
- `rules/aml_rules.py` — موتور قوانین (`RuleEngine` پایه + `ExtendedRuleEngine` با قوانین ایران/fraud). singleton سراسری از طریق `get_rule_engine()`.
- `services/` — منطق تجاری: `TransactionMonitor` (نظارت + محاسبه ریسک)، `AlertGenerator` (تولید/بررسی هشدار)، `RiskScorer`، `ReportGenerator` (SAR/CTR)، `notification_service` (ایمیل/webhook).
- `views.py` + `urls.py` — REST API روی همه‌ی مدل‌ها (`/api/customers/`, `/api/transactions/`, `/api/alerts/`, `/api/rules/`, `/api/devices/`, `/api/merchants/`, `/api/reports/`, `/api/audit-log/`) + endpointهای سفارشی مثل `alerts/export/` (CSV/XLSX) و `alerts/statistics/`.
- `middleware.py` — `AuditTrailMiddleware` برای لاگ کامل هر درخواست.
- `tasks.py` — پردازش async تراکنش و گزارش روزانه ریسک با Celery.
- `ml/model.py` — لایه‌ی اختیاری ML روی امتیاز ریسک قوانین.

## نقشه راه
جزئیات کامل در `ROADMAP.md` ریشه‌ی ریپو.

## چیزی که باید بدانید (شناخته‌شده، حل‌نشده)
- ندارد در حال حاضر — آخرین باگ‌های شناخته‌شده (export query-param collision با DRF، singleton queryset caching در rule engine) رفع شدند (به `log.md` نگاه کنید).

جزئیات هر بخش: [[index]]
