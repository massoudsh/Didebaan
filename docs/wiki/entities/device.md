# Device

> Fingerprint دستگاه دیده‌شده در پلتفرم — سیگنال اصلی برای تشخیص fraud rings (اشتراک یک دستگاه بین چند حساب).

## مسئولیت‌ها
- نگهداری fingerprint (`device_id`, `fingerprint_hash`)، مشخصات دستگاه (نوع، OS، مرورگر، IP) و پرچم‌های ریسک (`is_emulator`, `is_rooted`).
- ورودی برای قانون `DEVICE_SHARING` در [[concepts/rule-evaluation-flow]].

## وابستگی‌ها
- [[entities/transaction]] — هر تراکنش می‌تواند به یک `Device` لینک شود (`on_delete=SET_NULL`, nullable).
- [[entities/rule-engine]] — تابع `_evaluate_device_sharing_rule` روی این مدل کار می‌کند.

## قراردادها / Edge cases
- `device_id` یکتا و indexed.
- FK از `Transaction` قابل null است — تراکنش‌های قدیمی یا کانال‌هایی که device fingerprint ندارند مشکلی ندارند.

## منابع کد
- `backend/aml/models.py:71` — تعریف مدل
- `backend/aml/rules/aml_rules.py:674` — `_evaluate_device_sharing_rule`
- `backend/aml/views.py` — `DeviceViewSet` (`/api/devices/`)
