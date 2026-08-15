# Merchant

> فروشنده/کسب‌وکار دریافت‌کننده پرداخت — ردیابی الگوهای سوءاستفاده (خرید-برگشت جعلی، chargeback/refund غیرعادی).

## مسئولیت‌ها
- نگهداری `chargeback_rate` و `refund_rate` به‌همراه `risk_score` مستقل مرچنت.
- ورودی برای قانون `MERCHANT_ABUSE` و بخشی از `BNPL_RISK` در [[concepts/rule-evaluation-flow]] (برای دسته `BNPL_PARTNER`).

## وابستگی‌ها
- [[entities/transaction]] — هر تراکنش می‌تواند به یک `Merchant` لینک شود (`on_delete=SET_NULL`, nullable).
- [[entities/rule-engine]] — `_evaluate_merchant_abuse_rule` و `_evaluate_bnpl_risk_rule`.

## قراردادها / Edge cases
- `merchant_id` یکتا و indexed.
- `category` شامل `BNPL_PARTNER` برای شناسایی مرچنت‌های همکار BNPL.

## منابع کد
- `backend/aml/models.py:96` — تعریف مدل
- `backend/aml/rules/aml_rules.py:708` — `_evaluate_merchant_abuse_rule`
- `backend/aml/rules/aml_rules.py:766` — `_evaluate_bnpl_risk_rule`
- `backend/aml/views.py` — `MerchantViewSet` (`/api/merchants/`)
