# Index

## Overview
- [[overview]] — یک‌نگاه کلی پروژه Didebaan

## Entities (۱۰ صفحه)

### مدل‌های دیتا
- [[entities/customer]] — مشتری/KYC + پرچم PEP
- [[entities/device]] — fingerprint دستگاه، سیگنال device-sharing
- [[entities/merchant]] — فروشنده، سیگنال chargeback/refund abuse
- [[entities/transaction]] — رکورد تراکنش مالی
- [[entities/rule]] — تعریف قانون + نسخه‌بندی (`RuleVersion`)
- [[entities/alert]] — هشدار + explainable AI

### سرویس‌ها / منطق تجاری
- [[entities/rule-engine]] — `RuleEngine` / `ExtendedRuleEngine`، singleton ارزیابی قوانین
- [[entities/transaction-monitor]] — orchestrator نظارت بر تراکنش
- [[entities/alert-generator]] — ساخت/بررسی/escalate هشدار
- [[entities/report-generator]] — تولید گزارش SAR/CTR

## Concepts (۲ صفحه)
- [[concepts/rule-evaluation-flow]] — مسیر کامل از ثبت تراکنش تا هشدار
- [[concepts/explainable-ai]] — ساختار فیلد `explanation` روی Alert

## به‌روزرسانی‌ها
- [[log]] — تاریخچه append-only تغییرات ویکی
