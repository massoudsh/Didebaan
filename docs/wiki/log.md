# Log

## [2026-08-15] init | راه‌اندازی اولیه ویکی دانش پروژه (docs/wiki/) طبق Vault Recipe؛ مستندسازی ۶ مدل اصلی، ۴ سرویس کلیدی و ۲ concept (rule evaluation flow, explainable AI) بر اساس کدبیس فعلی.
## [2026-08-15] update | رفع باگ singleton در RuleEngine.active_rules (property به‌جای cache شدن queryset) و رفع تصادم نام پارامتر export (`format` → `export_format`) — هر ۸ تست fail شده سبز شدند.
## [2026-08-18] update | فیچر جدید #39 Alert case management: `Alert.assigned_to/assigned_at` + مدل `AlertComment` (COMMENT/ASSIGNMENT/STATUS_CHANGE)، اکشن‌های `assign`/`comments` روی `AlertViewSet`، لاگ خودکار STATUS_CHANGE در review/escalate/false-positive. مایگریشن 0005. ۴ تست جدید (۲۹/۲۹ سبز). backlog فیچرهای آینده (#40–#46) در ROADMAP.md اضافه شد.
