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
- `templates/aml/dashboard.html` — داشبورد عملیاتی فارسی و RTL با شاخص‌های کلیدی، نمودارهای ریسک، دسترسی سریع و تم‌های گرافیت/فیروزه/زعفران/انار/لاجورد/کاغذ.
- `frontend/` (ریشهٔ ریپو) — SPA مستقل React + Vite، راست‌چین و فارسی: ورود با توکن (`/api/auth/token/`)، داشبورد ریسک، صف هشدارها (فیلتر، عملیات گروهی، خروجی) و کشوی پرونده (ارجاع، بازبینی، تاریخچهٔ یادداشت‌ها). اجرا: `npm install && npm run dev` (پورت ۳۰۰۰، پروکسی `/api` به `localhost:8000`).
- `middleware.py` — `AuditTrailMiddleware` برای لاگ کامل هر درخواست.
- `tasks.py` — پردازش async تراکنش و گزارش روزانه ریسک با Celery.
- `ml/model.py` — لایه‌ی اختیاری ML روی امتیاز ریسک قوانین.

## نقشه راه
جزئیات کامل در `ROADMAP.md` ریشه‌ی ریپو.

## وضعیت عملیاتی و محدودیت‌ها

- پنج ابزار `/api/intelligence/`: شبیه‌سازی قوانین، گراف ارتباطات، غربالگری فارسی، داشبورد SLA و بستهٔ شواهد JSON. محدودیت نمونه‌ها و snapshot فعلی قوانین در [راهنمای اصلی](../../README.md) آمده است؛ خروجی‌ها قالب رسمی ارسال به رگولاتور نیستند.
- پایش همگام همان هشدار تولیدشده در pipeline را برمی‌گرداند؛ `asynchronous: true` در endpoint پایش، task موجود Celery را dispatch می‌کند (۲۰۲ با شناسهٔ task، یا ۵۰۳ هنگام خطای صف). پذیرش task به معنی پایان پردازش نیست؛ اجرای مجدد پایش تضمین idempotency ندارد.
- خروجی CSV/XLSX هشدارها همان فیلتر و ترتیب صف را اعمال و متن ورودی را در برابر formula injection ایمن می‌کند. رابط بازبینی بررسی‌کننده فقط روی پرونده‌های خودش فعال است؛ توضیح هشدار از `rule_name` و `weight` استفاده می‌کند. تازه‌سازی صف هر ۶۰ ثانیه است.
- فرمان `seed_demo` دادهٔ ساختگی تکرارپذیر را فقط با DEBUG فعال می‌سازد و رمز پیش‌فرض ایجاد نمی‌کند. برخورد شناسه با ایمیل مشتری یا مالک تراکنش متفاوت باعث rollback می‌شود.
- اعتبارسنجی ۲۰۲۶-۱۰-۳۱: ۷۷ تست Django، ۱۳ تست React بدون مرورگر، بررسی سیستم و migration موفق. بررسی بصری، Redis/worker زنده، مدل ML آموزش‌دیده، انطباق حقوقی و load test جداگانه لازم است.
- منابع: `backend/aml/views.py:41` و `:272`، `backend/aml/serializers.py:149`، `backend/aml/management/commands/seed_demo.py:12`، `frontend/src/components/AlertQueue.jsx:34`، `frontend/src/components/AlertDetail.jsx:127`.

جزئیات هر بخش: [[index]]
