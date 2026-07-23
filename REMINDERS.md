# Didebaan — Reminders & Timeline

Use this with **ROADMAP.md** and **GitHub Issues/Milestones**. Set calendar or task reminders for the following.

---

## Phase 1 (Weeks 1–2)

- **End of Week 1:** Confirm settings split and run commands work (`make run`, `make migrate`). Production settings load with `DJANGO_ENV=production`.
- **End of Week 2:** Unit tests for core services (rules, risk scorer, transaction monitor) are green. Health/readiness endpoints implemented.

## Phase 2 (Weeks 3–4)

- **Week 3:** Token auth and list filtering/search on API done.
- **Week 4:** Celery task for async monitoring (optional) and audit log API done.

## Phase 3 (Weeks 5–7)

- **Week 5:** Django Admin customized for AML (filters, actions). Simple dashboard in Admin.
- **Week 7:** Standalone dashboard (or template dashboard) and RTL/theme decisions done.

## Phase 4 (Weeks 8–10)

- **Week 8:** ML risk model stub or first model in `aml/ml/`. Rule versioning (if planned).
- **Week 10:** Notifications (email/webhook) and SAR submission workflow done.

## Phase 5 (Ongoing)

- Before first production deploy: Docker + PostgreSQL + `DJANGO_ENV=production`. CI (test + lint) on push.

---

## Quick reminder commands

```bash
# Check roadmap
cat ROADMAP.md

# List open issues (after gh is configured)
gh issue list --repo massoudsh/Didebaan

# Run app (Django best practice)
make run
```

Set your own calendar reminders (e.g. “Didebaan Phase 1 review”) at the end of each phase.
