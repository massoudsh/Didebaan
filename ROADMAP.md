# Didebaan AML — Development Roadmap

Timeline and priorities for development, UI/UX, and enhancements. Use this with GitHub Issues and Milestones for tracking.

---

## Phase 1: Foundation & Django Best Practices (Weeks 1–2)

| Priority | Item | Timeline | Notes |
|----------|------|----------|--------|
| P0 | Settings split (base / development / production) | Week 1 | Use `DJANGO_SETTINGS_MODULE` |
| P0 | Security hardening (CSRF, HSTS, secure cookies in prod) | Week 1 | Production-only flags |
| P0 | Run scripts / Makefile for dev & prod | Week 1 | `make run`, `make migrate`, etc. |
| P1 | API documentation (OpenAPI/Swagger or DRF schema) | Week 2 | Browsable API or standalone docs |
| P1 | Health/readiness endpoints | Week 2 | `/api/health/`, `/api/ready/` |
| P1 | Unit tests for core services (rules, risk scorer, monitor) | Week 2 | pytest or Django TestCase |

**Reminder:** End of Week 1 — confirm settings split and run commands. End of Week 2 — tests green and health endpoints live.

**Done:** Settings split, security (prod), Makefile, health/ready endpoints, API schema (with uritemplate), unit tests for rules/risk_scorer/transaction_monitor + health/ready.

---

## Phase 2: API & Backend Enhancements (Weeks 3–4)

| Priority | Item | Timeline | Notes |
|----------|------|----------|--------|
| P0 | Token auth (JWT or DRF TokenAuthentication) for API | Week 3 | Optional session + token |
| P1 | Filtering, search, ordering on list endpoints | Week 3 | DRF FilterBackend, SearchFilter |
| P1 | Rate limiting (per user / IP) | Week 3 | django-ratelimit or DRF throttle |
| P1 | Async transaction monitoring (Celery task) | Week 4 | Optional queue for heavy checks |
| P2 | Export alerts/reports in bulk (CSV/Excel) | Week 4 | Same as report generator, batch |
| P2 | Audit log API (read-only) for compliance | Week 4 | Paginated list of audit events |

**Reminder:** Week 3 — auth and filters done. Week 4 — Celery task and audit API done.

**Done:** #11 Token auth, #12 Filtering/search/ordering (django-filter + SearchFilter + OrderingFilter), #13 Rate limiting (UserRateThrottle 100/h, AnonRateThrottle 20/h), #16 Audit log API (read-only paginated `GET /api/audit-log/`). **Open:** #14 Celery async monitor, #15 Bulk export.

**GitHub issues:** #11 Token auth, #12 Filtering/search/ordering, #13 Rate limiting, #14 Celery async monitor, #15 Bulk export, #16 Audit log API.

---

## Phase 3: UI/UX — Admin & Dashboards (Weeks 5–7)

| Priority | Item | Timeline | Notes |
|----------|------|----------|--------|
| P0 | Customize Django Admin for AML (list filters, actions, readonly) | Week 5 | Customers, Transactions, Alerts |
| P0 | Simple dashboard view in Admin (counts, recent alerts) | Week 5 | Custom admin index or app |
| P1 | Standalone frontend (React/Vue) or Django templates dashboard | Week 6–7 | Choose: SPA or server-rendered |
| P1 | Dashboards: Alerts overview, Risk distribution, Transaction trends | Week 6–7 | Charts (Chart.js, Plotly, or similar) |
| P2 | RTL and Persian locale for UI | Week 7 | django.utils.translation, RTL CSS |
| P2 | Dark/light theme toggle | Week 7 | CSS variables, minimal JS |

**Reminder:** Week 5 — admin customizations. Week 7 — dashboard and theme/locale decisions.

**GitHub issues:** #17 Admin customization, #18 Dashboard in Admin, #19 Charts, #20 RTL/Persian, #21 Theme toggle.

---

## Additional rules, scenarios & features (issues)

- **Rules:** #22 PEP/high-risk customer, #23 Night/weekend activity, #24 Round-amount structuring, #25 Same-beneficiary concentration, #26 New-account velocity, #27 Sanctioned countries.
- **Scenarios:** #28 Structuring E2E test, #29 Layering test.
- **Features:** #30 Notifications, #31 Rule versioning, #32 Configurable thresholds, #33 SAR/CTR workflow, #34 ML risk model; #35 API examples docs, #36 High-risk countries sample; #37 Docker, #38 CI.

---

## Phase 4: ML & Advanced Features (Weeks 8–10)

| Priority | Item | Timeline | Notes |
|----------|------|----------|--------|
| P1 | ML risk model in `aml/ml/` (train on historical alerts) | Week 8 | Optional; sklearn or light model |
| P1 | Rule versioning (draft → active, history) | Week 8 | Model or JSON snapshot |
| P2 | Configurable thresholds via Admin (no code deploy) | Week 9 | Already partly in Rule.configuration |
| P2 | Notifications (email/webhook on high-severity alert) | Week 9 | Django email or Celery task |
| P2 | SAR/CTR submission workflow (status, comments) | Week 10 | State machine, audit |

**Reminder:** Week 8 — ML stub or first model. Week 10 — notification and SAR workflow done.

---

## Phase 5: Production Readiness & DevOps (Ongoing)

| Priority | Item | Timeline | Notes |
|----------|------|----------|--------|
| P0 | Dockerfile + docker-compose (app, DB, Redis) | As needed | Django + gunicorn, nginx optional |
| P0 | PostgreSQL in production; migrations checked | As needed | No SQLite in prod |
| P1 | CI (GitHub Actions): test, lint, migrate check | As needed | On push to main |
| P1 | Structured logging (JSON) for production | As needed | For aggregators |
| P2 | Performance: DB indexes, query optimization, caching | As needed | After load testing |

---

## How to Use This Roadmap

- **GitHub Issues:** One issue per row (or per logical task). Label with `phase-1`, `phase-2`, … and `p0`, `p1`, `p2`.
- **Milestones:** Create milestones `Phase 1`, `Phase 2`, … with due dates (e.g. Phase 1 = 2 weeks from start).
- **Reminders:** Set calendar reminders for “Phase N review” at the end of each phase, or use GitHub Projects with a “Sprint” column and due dates.
- **Priorities:** P0 = must-have for next release, P1 = important, P2 = nice-to-have.

---

## Summary Timeline

| Phase | Focus | Weeks |
|-------|--------|--------|
| 1 | Foundation, Django best practices, tests | 1–2 |
| 2 | API auth, filters, Celery, audit API | 3–4 |
| 3 | Admin UX, dashboard, RTL/theme | 5–7 |
| 4 | ML, rule versioning, notifications, SAR workflow | 8–10 |
| 5 | Docker, CI, production hardening | Ongoing |

*Last updated: 2026-02-14*
