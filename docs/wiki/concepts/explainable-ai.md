# Explainable AI (فیلد explanation روی Alert)

> هر هشدار باید بتواند توضیح دهد «چرا» trigger شده — نه فقط این‌که trigger شده.

## چگونگی کار
فیلد `Alert.explanation` یک لیست JSON است که هر آیتم آن نتیجه‌ی یک قانون trigger‌شده در [[concepts/rule-evaluation-flow]] است (ساخته‌شده توسط `AlertGenerator._build_explanation`):
```json
[
  {"rule_name": "Device Sharing", "rule_type": "DEVICE_SHARING", "reason": "...", "weight": 1.5},
  {"rule_name": "PEP Transaction Detection", "rule_type": "PEP", "reason": "...", "weight": 1.0}
]
```
`weight` همان `Rule.risk_weight` است (ضریب وزنی قانون در `total_risk_score`، نه سهم عددی نهایی محاسبه‌شده).

## چرا مهم است
- برای بررسی‌کننده (reviewer) در workflow [[entities/alert]]: به‌جای یک عدد خام، دلیل دقیق هر بخش از ریسک را می‌بیند.
- برای گزارش‌های رگولاتوری ([[entities/report-generator]]): SAR باید مستندسازی قابل دفاع از دلیل هشدار داشته باشد.

## وابستگی‌ها
- [[entities/alert-generator]] — سازنده‌ی `explanation` هنگام ساخت Alert.
- [[entities/rule]] — منبع نام/وزن هر قانون در breakdown.

## منابع کد
- `backend/aml/models.py:300` — فیلد `explanation` روی `Alert`
- `backend/aml/services/alert_generator.py` — ساخت breakdown
