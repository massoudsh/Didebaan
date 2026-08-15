# ReportGenerator

> تولید گزارش‌های رگولاتوری SAR (Suspicious Activity Report) و CTR (Currency Transaction Report).

## مسئولیت‌ها
- ساخت رکورد `Report` (مدل `backend/aml/models.py:362`) از تراکنش‌ها/هشدارهای مرتبط (`report_data` JSON ساختاریافته).
- singleton از طریق `get_report_generator()`.

## وابستگی‌ها
- [[entities/alert]] و [[entities/transaction]] — منبع داده گزارش (`related_alerts`, `related_transactions`).
- `ReportComment` (روی مدل `Report`) — workflow کامنت/تایید/رد/ارسال به رگولاتور.

## منابع کد
- `backend/aml/services/report_generator.py:25` — `class ReportGenerator`
- `backend/aml/services/report_generator.py:397` — `get_report_generator()`
- `backend/aml/models.py:362` — مدل `Report`
- `backend/aml/models.py:519` — مدل `ReportComment`
