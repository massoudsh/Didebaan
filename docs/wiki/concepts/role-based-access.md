# دسترسی نقش‌محور

> کنترل مجوزهای عملیاتی API با استفاده از گروه‌های Django.

## نقش‌ها
- `AUDITOR` — خواندن داده‌ها و خروجی‌ها، بدون تغییر.
- `INVESTIGATOR` — عملیات پرونده روی هشدار ارجاع‌شده به خود: یادداشت و بازبینی.
- `SUPERVISOR` — ارجاع و بازبینی گروهی هشدارها.
- `COMPLIANCE_OFFICER` — مدیریت قوانین، گزارش‌ها، watchlist، audit log و داده‌های حساس.
- superuser همهٔ نقش‌ها را دارد.

## قراردادها / Edge cases
- endpoint `GET /api/auth/me/` نام کاربری و نقش‌ها را برای SPA برمی‌گرداند.
- نقش‌ها با migration `0008_operational_roles` ساخته می‌شوند؛ مدیر سیستم باید کاربران موجود را به گروه مناسب اضافه کند.
- بررسی‌کننده برای `review` یا افزودن کامنت باید در `Alert.assigned_to` همان نام کاربری ثبت‌شده باشد؛ سرپرست و افسر انطباق این محدودیت را ندارند.

## منابع کد
- `backend/aml/permissions.py` — نقش‌ها و permission classها
- `backend/aml/views.py` — اعمال permission و endpoint `/api/auth/me/`
- `backend/aml/migrations/0008_operational_roles.py` — ایجاد گروه‌های نقش
- `frontend/src/api.js` — دریافت و نگهداری پروفایل نقش‌دار پس از ورود
