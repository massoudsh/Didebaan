# Didebaan — موتور هوشمند تشخیص تقلب و سوءاستفاده

دیده‌بان (Didebaan) یک موتور هوشمند تشخیص تقلب و سوءاستفاده (Fraud & Abuse Intelligence Engine) برای فین‌تک‌های ایرانی است: نظارت بر تراکنش‌ها و مشتریان، شناسایی حلقه‌های حساب مرتبط از طریق اشتراک دستگاه (device sharing)، تشخیص سوءاستفاده فروشندگان (merchant abuse) و ریسک نکول در BNPL، در کنار ماژول‌های اصلی AML/CTR/SAR.

## ویژگی‌ها

- ✅ نظارت بر تراکنش‌ها در زمان واقعی
- ✅ محاسبه امتیاز ریسک خودکار
- ✅ تولید هشدار برای تراکنش‌های مشکوک همراه با **توضیح تصمیم (explainable AI)** — شکست قانون‌به‌قانون علت هر هشدار
- ✅ ردیابی دستگاه (`Device`) برای شناسایی اشتراک دستگاه بین چند حساب (fraud rings)
- ✅ ردیابی فروشنده (`Merchant`) برای تشخیص نرخ chargeback/refund غیرعادی و الگوی خرید-برگشت جعلی
- ✅ تشخیص ریسک نکول در BNPL (Buy Now Pay Later)
- ✅ مدیریت هشدارها و workflow بررسی
- ✅ تولید گزارش‌های رگولاتوری (SAR, CTR)
- ✅ لاگ‌گیری کامل برای audit trail

## نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.9+
- PostgreSQL 12+
- Redis (برای Celery - اختیاری)

### راه‌اندازی

1. کلون کردن پروژه:
```bash
git clone <repository-url>
cd Didebaan
```

2. ایجاد محیط مجازی:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. نصب وابستگی‌ها:
```bash
cd backend
pip install -r requirements.txt
```

4. تنظیم فایل `.env` (از ریشه پروژه):
```bash
cp .env.example .env
# ویرایش .env و تنظیم مقادیر مناسب
```

5. اجرای migrations:
```bash
python manage.py migrate
```

6. ایجاد superuser:
```bash
python manage.py createsuperuser
```

7. ایجاد قوانین نمونه:
```bash
python manage.py create_sample_rules
```

8. اجرای سرور (به‌صورت پیش‌فرض با تنظیمات development):
```bash
# از ریشه پروژه با Make
make run

# یا از پوشه backend
cd backend && python manage.py runserver
```

برای محیط production از همان پوشه:
```bash
DJANGO_ENV=production python manage.py runserver
```
یا `make run-prod` (از ریشه پروژه).

## ساختار پروژه

```
Didebaan/
├── backend/
│   ├── aml/                    # Django app اصلی AML
│   │   ├── models.py           # Customer, Transaction, Alert, RiskScore
│   │   ├── serializers.py      # DRF serializers
│   │   ├── views.py            # API endpoints
│   │   ├── services/           # Business logic
│   │   ├── rules/              # Rule engine
│   │   └── ml/                 # ML models (optional)
│   ├── config/
│   │   ├── settings/           # Django settings (base, development, production)
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   └── urls.py
│   └── requirements.txt
├── Makefile                    # make run, make migrate, make test
├── ROADMAP.md                  # Development roadmap & timeline
└── README.md
```

### Django settings (best practice)

- **Development (default):** `DJANGO_ENV=development` یا مقدار ندادن — DEBUG=True، SQLite مجاز.
- **Production:** `DJANGO_ENV=production` — DEBUG=False، security headers، فقط JSON API.
- تنظیمات مشترک در `config/settings/base.py`؛ مخصوص محیط در `development.py` و `production.py`.

## API Endpoints

### API Authentication (Token)

API requests require authentication. Use **Token Authentication** (DRF):

1. **Obtain a token** (POST with a valid Django user):
   ```bash
   curl -X POST http://localhost:8000/api/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
   ```
   Response: `{"token": "abc123..."}`

2. **Call API** with the token:
   ```bash
   curl -H "Authorization: Token abc123..." http://localhost:8000/api/customers/
   ```

Create a user first via Django Admin or `python manage.py createsuperuser`. Token is also available in Django Admin: User → Auth token.

**Rate limiting:** Authenticated users 100 req/hour; anonymous 20 req/hour. Health/ready endpoints are not throttled.

**Filtering, search, ordering:** List endpoints support `?search=`, `?ordering=`, and filter fields (e.g. `?status=OPEN`, `?current_risk_level=HIGH`). See API schema at `/api/schema/`.

### Customers
- `GET /api/customers/` - لیست مشتریان
- `POST /api/customers/` - ایجاد مشتری جدید
- `GET /api/customers/{customer_id}/` - جزئیات مشتری
- `GET /api/customers/{customer_id}/risk_scores/` - امتیازهای ریسک مشتری
- `GET /api/customers/{customer_id}/alerts/` - هشدارهای مشتری
- `GET /api/customers/{customer_id}/transactions/` - تراکنش‌های مشتری

### Transactions
- `GET /api/transactions/` - لیست تراکنش‌ها
- `POST /api/transactions/` - ایجاد تراکنش جدید
- `GET /api/transactions/{transaction_id}/` - جزئیات تراکنش
- `POST /api/transactions/monitor/` - نظارت بر تراکنش (body: `{"transaction_id": "..."}`)

### Alerts
- `GET /api/alerts/` - لیست هشدارها
- `GET /api/alerts/{alert_id}/` - جزئیات هشدار
- `POST /api/alerts/{alert_id}/review/` - بررسی هشدار (body: `{"status": "...", "notes": "..."}`)
- `GET /api/alerts/statistics/` - آمار هشدارها
- `GET /api/alerts/open_count/` - تعداد هشدارهای باز

### Rules
- `GET /api/rules/` - لیست قوانین
- `POST /api/rules/` - ایجاد قانون جدید
- `GET /api/rules/{id}/` - جزئیات قانون
- `PUT /api/rules/{id}/` - به‌روزرسانی قانون

### Reports
- `GET /api/reports/` - لیست گزارش‌ها
- `GET /api/reports/{report_id}/` - جزئیات گزارش
- `POST /api/reports/generate/` - تولید گزارش جدید
- `GET /api/reports/{report_id}/download/` - دانلود فایل گزارش
- `POST /api/reports/{report_id}/submit/` - ارسال گزارش به رگولاتور

### Risk Scores
- `GET /api/risk-scores/` - لیست امتیازهای ریسک

### Audit Log (compliance)
- `GET /api/audit-log/` - لیست خواندنی و صفحه‌بندی‌شده رویدادهای audit (فقط خواندن)

### Devices (شناسایی حلقه‌های تقلب)
- `GET /api/devices/` - لیست دستگاه‌ها
- `GET /api/devices/{device_id}/` - جزئیات دستگاه
- `GET /api/devices/{device_id}/customers/` - مشتریان مشترک روی این دستگاه (device sharing / fraud rings)

### Merchants (سوءاستفاده فروشندگان)
- `GET /api/merchants/` - لیست فروشندگان
- `GET /api/merchants/{merchant_id}/` - جزئیات فروشنده (نرخ chargeback/refund، امتیاز ریسک)

## تست

```bash
python manage.py test
```

## ماژول‌های اصلی

### Rule Engine (`aml/rules/aml_rules.py`)
- ارزیابی قوانین AML و تقلب بر اساس تراکنش‌ها
- پشتیبانی از قوانین: Threshold, Pattern, Behavioral, Geographic
- قوانین تقلب: Device Sharing (اشتراک دستگاه بین چند حساب)، Merchant Abuse (سوءاستفاده فروشنده)، BNPL Risk (ریسک نکول BNPL)
- قوانین قابل تنظیم از طریق دیتابیس
- هر هشدار همراه با `explanation` — شکست قانون‌به‌قانون علت تصمیم (explainable AI)

### Risk Scorer (`aml/services/risk_scorer.py`)
- محاسبه امتیاز ریسک برای مشتریان و تراکنش‌ها
- در نظر گیری عوامل مختلف: مبلغ، فرکانس، جغرافیا، تاریخچه، الگوهای رفتاری

### Transaction Monitor (`aml/services/transaction_monitor.py`)
- نظارت بر تراکنش‌ها در زمان واقعی
- اعمال قوانین AML و محاسبه ریسک
- تولید خودکار هشدار برای تراکنش‌های مشکوک

### Alert Generator (`aml/services/alert_generator.py`)
- تولید و مدیریت هشدارها
- اولویت‌بندی و workflow بررسی
- آمار و گزارش‌گیری از هشدارها

### Report Generator (`aml/services/report_generator.py`)
- تولید گزارش‌های رگولاتوری (SAR, CTR)
- خروجی در فرمت‌های JSON, CSV, PDF
- مدیریت ارسال گزارش‌ها به رگولاتور

## لاگ‌گیری و Audit Trail

- تمام درخواست‌های API در فایل `logs/audit_trail.log` ثبت می‌شوند
- لاگ‌های سیستم در فایل `logs/aml_system.log` ذخیره می‌شوند
- Middleware برای ثبت خودکار تمام فعالیت‌ها

## مجوز

این پروژه برای چالش RegMeet طراحی شده است.


---

## تطبیق با بازار ایران

این سیستم بر اساس الزامات قانونی جمهوری اسلامی ایران و رهنمودهای بانک مرکزی طراحی شده است:

| ویژگی | مقدار |
|------|-------|
| پول رایج | ریال (IRR) |
| زبان رابط | فارسی (RTL) |
| منطقه زمانی | Asia/Tehran |
| آستانه CTR | ۵۰۰,۰۰۰,۰۰۰ ریال |
| نهاد نظارتی | بانک مرکزی جمهوری اسلامی ایران — واحد اطلاعات مالی (FIU) |
| انواع گزارش | SAR (گزارش تراکنش مشکوک)، CTR (گزارش تراکنش کلان) |

### کشورهای پرریسک (FATF-based)
KP (کره شمالی)، MM (میانمار)، AF (افغانستان)، YE (یمن)، SD (سودان)، SS (سودان جنوبی)، SY (سوریه)، SO (سومالی)، LY (لیبی)، CD (کنگو)، ML (مالی)، HT (هائیتی)، PK (پاکستان)، VU (وانواتو)

---

## API Examples (Issue #35)

### دریافت Token
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
# Response: {"token": "abc123..."}
```

### لیست مشتریان
```bash
curl -H "Authorization: Token abc123..." \
  "http://localhost:8000/api/customers/?current_risk_level=HIGH"
```

### ایجاد مشتری (با PEP flag)
```bash
curl -X POST http://localhost:8000/api/customers/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C-001",
    "first_name": "محمد",
    "last_name": "رضایی",
    "email": "m.rezaei@example.ir",
    "phone": "+989121234567",
    "customer_type": "INDIVIDUAL",
    "national_id": "0012345678",
    "country": "IR",
    "is_pep": false
  }'
```

### ایجاد تراکنش
```bash
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-2026-001",
    "customer": "C-001",
    "transaction_type": "TRANSFER",
    "amount": "500000000",
    "currency": "IRR",
    "status": "COMPLETED",
    "receiver_account": "IR12-0000-0000-0000-0000-0000",
    "receiver_country": "IR"
  }'
```

### نظارت بر تراکنش (AML monitoring)
```bash
curl -X POST http://localhost:8000/api/transactions/monitor/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "TXN-2026-001"}'
```

### تولید گزارش CTR
```bash
curl -X POST http://localhost:8000/api/reports/generate/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "CTR",
    "period_start": "2026-06-01T00:00:00Z",
    "period_end": "2026-06-30T23:59:59Z",
    "threshold": "500000000",
    "format": "JSON"
  }'
```

### بررسی هشدار
```bash
curl -X POST http://localhost:8000/api/alerts/ALT-001/review/ \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{"status": "RESOLVED", "notes": "تراکنش تجاری معتبر — مستندات تایید شد"}'
```

### آمار هشدارها
```bash
curl -H "Authorization: Token abc123..." \
  "http://localhost:8000/api/alerts/statistics/?days=30"
```

### وضعیت سرویس (بدون احراز هویت)
```bash
curl http://localhost:8000/api/health/
curl http://localhost:8000/api/ready/
```

---

## اجرا با Docker (Issue #37)

```bash
# کپی env
cp .env.example .env
# ویرایش .env و تنظیم SECRET_KEY و DB_PASSWORD

# ساخت و اجرا
docker-compose up -d

# مشاهده لاگ
docker-compose logs -f app
```

---

## مسائل حل‌شده (Resolved Issues)

| # | عنوان | وضعیت |
|---|-------|--------|
| #2 | Security hardening (CSRF, HSTS, secure cookies) | ✅ |
| #3 | Makefile (make run, migrate, test) | ✅ |
| #4 | API documentation (OpenAPI/Swagger) | ✅ |
| #5 | Health/readiness endpoints | ✅ |
| #6 | Unit tests for core services | ✅ |
| #7/#11 | Token authentication (JWT/DRF Token) | ✅ |
| #8/#12 | Filtering, search, ordering on list endpoints | ✅ |
| #9 | Django Admin customization | ✅ |
| #10 | Dashboard (alerts, risk distribution) | ✅ |
| #13 | Rate limiting (per user/IP) | ✅ |
| #23 | PEP rule + field | ✅ |
| #24 | Fund concentration rule | ✅ |
| #25 | Velocity detection rule | ✅ |
| #27 | Cross-border with sanctioned countries | ✅ |
| #28 | Structuring scenario test | ✅ |
| #29 | Layering scenario test | ✅ |
| #30 | Notifications (email/webhook) | ✅ |
| #31 | Rule versioning (draft→active, history) | ✅ |
| #32 | Configurable thresholds via Admin | ✅ |
| #33 | SAR/CTR submission workflow (comments, audit) | ✅ |
| #34 | ML risk model stub | ✅ |
| #35 | API examples (curl) in README | ✅ |
| #36 | Replace placeholder XX/YY with real FATF countries | ✅ |
| #37 | Dockerfile + docker-compose | ✅ |
| #38 | CI (GitHub Actions) — test, lint, migrate-check | ✅ |
