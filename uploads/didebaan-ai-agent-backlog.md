# Didebaan — AI Agent UI/UX Backlog

This document contains a ready-to-use backlog for improving **Didebaan** with a modern, glassy UI/UX style.

> **Product context:** Didebaan is described as an intelligent fraud-detection and abuse-prevention engine. This backlog focuses on the operator-facing console: monitoring, alerts, cases, rules, risk signals, investigations, auditability, and administration. Before implementation, an AI agent must audit the actual frontend stack, routes, components, data model, permissions, and backend capabilities.

## How to use

1. Copy each section into a separate GitHub Issue, or let an AI coding agent read this file directly.
2. Implement issues in the recommended order.
3. Keep each pull request small and focused.
4. Preserve existing detection logic, APIs, permissions, audit trails, and data privacy controls.
5. Do not weaken security controls, expose sensitive data, or bypass approval workflows.

## Recommended implementation order

1. Create a reusable glass UI design system
2. Redesign app shell and navigation
3. Define accessible glass surface recipes
4. Add a fraud operations dashboard
5. Improve alert triage and investigation workflow
6. Upgrade case management
7. Improve rules, signals, and model transparency
8. Add entity risk profiles
9. Upgrade investigation tables and filters
10. Improve forms, settings, and error handling
11. Improve Persian typography and RTL consistency
12. Add polished light and dark themes
13. Add restrained motion and interaction feedback
14. Meet WCAG AA across primary flows
15. Optimize frontend performance
16. Add security, privacy, audit, and quality gates

## Global rules for AI agents

- Preserve existing functionality, APIs, detection behavior, permissions, and audit trails.
- Prefer the project’s existing frontend framework, styling system, and component conventions.
- Use design tokens instead of hard-coded colors, spacing, radii, shadows, and blur values.
- Support both Persian/RTL and English/LTR where applicable.
- Maintain WCAG AA contrast and keyboard accessibility.
- Add loading, empty, error, offline, and permission-denied states to new UI.
- Avoid excessive backdrop blur; glassmorphism must not harm readability or performance.
- Never display raw secrets, credentials, tokens, full payment instruments, or unnecessary personal data.
- Use masking, redaction, role-based visibility, and explicit permission checks for sensitive fields.
- Include screenshots or short recordings in pull requests when UI changes are visible.

---

## 1. Create a reusable glass UI design system

**Labels:** `design-system`, `ui/ux`, `glassmorphism`, `frontend`

### Goal

Establish a consistent visual language before changing individual screens.

### Scope

- Add design tokens for:
  - Color
  - Surface and background
  - Blur
  - Border
  - Shadow
  - Radius
  - Spacing
  - Typography
  - Motion
  - Z-index
  - Risk/status colors
- Create reusable components:
  - `GlassCard`
  - `GlassPanel`
  - `GlassButton`
  - `GlassIconButton`
  - `GlassInput`
  - `GlassSelect`
  - `GlassDatePicker`
  - `GlassTable`
  - `GlassTabs`
  - `GlassModal`
  - `GlassDrawer`
  - `GlassPopover`
  - `GlassToast`
  - `GlassTooltip`
  - `GlassSidebar`
  - `GlassTopBar`
  - `RiskBadge`
  - `StatusBadge`
  - `SeverityIndicator`
- Support light and dark themes.
- Support RTL/Persian text.

### Acceptance criteria

- [ ] Tokens are defined in a central theme/configuration file.
- [ ] Components use tokens rather than hard-coded styles.
- [ ] Interactive components include hover, focus-visible, active, disabled, loading, and error states.
- [ ] Risk, severity, and status colors are consistent and accessible.
- [ ] Components work in RTL and LTR layouts.
- [ ] Existing screens do not regress.

### AI-agent prompt

```text
Audit Didebaan’s frontend stack, routing structure, component library, and styling approach. Create a token-based glass design system without breaking existing functionality. Include accessible risk, severity, and status color tokens. Prefer CSS variables or the project’s existing theme mechanism. Build only the primitives needed by current screens.
```

---

## 2. Redesign app shell and navigation

**Labels:** `ui/ux`, `frontend`, `glassmorphism`

### Goal

Make Didebaan’s operator console modern, organized, and efficient for high-pressure investigation work.

### Requirements

- Responsive application shell.
- Fixed glass sidebar on desktop.
- Collapsible drawer/sidebar on mobile.
- Sticky glass top bar.
- Global search for alerts, cases, entities, rules, and transactions where supported.
- Notifications for critical alerts.
- User/profile menu.
- Environment indicator, such as production, staging, or sandbox.
- Theme toggle.
- Clear active-route indication.
- Quick links to high-priority queues.

### Acceptance criteria

- [ ] Sidebar collapses on smaller viewports.
- [ ] Top bar remains usable while scrolling.
- [ ] Active navigation item is visually and programmatically indicated.
- [ ] All navigation is reachable by keyboard.
- [ ] Environment is clearly identifiable to reduce operational mistakes.
- [ ] Layout works correctly in RTL.
- [ ] No business logic is changed.

### AI-agent prompt

```text
Refactor Didebaan’s app layout into a responsive operator console with a glass sidebar, sticky top bar, and content area. Preserve existing routes and data behavior. Include a clear environment indicator and ensure navigation works with keyboard, screen readers, and RTL.
```

---

## 3. Define accessible glass surface recipes

**Labels:** `ui/ux`, `glassmorphism`, `accessibility`

### Goal

Avoid unreadable text, inconsistent blur, and inaccessible contrast.

### Surface variants

| Variant | Use case |
|---|---|
| `subtle` | Page background layers, quiet containers |
| `medium` | Cards, panels, filters, forms |
| `elevated` | Modals, drawers, dropdowns, command palette, toasts, popovers |

### Requirements

- Use restrained blur and semi-transparent fills.
- Add a subtle 1px light border for definition.
- Guarantee WCAG AA contrast for text, icons, and interactive controls.
- Provide fallbacks when `backdrop-filter` is unavailable.
- Respect `prefers-reduced-motion`.
- Do not reduce readability of alerts, evidence, logs, or dense tables.

### Acceptance criteria

- [ ] `GlassSurface` component exists with `subtle`, `medium`, and `elevated` variants.
- [ ] Contrast passes WCAG AA in light and dark themes.
- [ ] A no-backdrop-filter fallback is implemented.
- [ ] Focus states are visible on glass surfaces.
- [ ] Long text and data-heavy content remain readable.

### AI-agent prompt

```text
Create a GlassSurface primitive with subtle, medium, and elevated variants. Include hover, focus-visible, disabled, loading, and error states. Add reduced-motion and no-backdrop-filter fallbacks.
```

---

## 4. Add a fraud operations dashboard

**Labels:** `feature`, `ui/ux`, `frontend`

### Goal

Give fraud, risk, and operations teams an immediate view of system health and active risk.

### Dashboard content

- KPI cards:
  - Open alerts
  - Critical alerts
  - Alerts awaiting review
  - Cases in progress
  - Confirmed fraud
  - False-positive rate, where available
  - Detection latency, where available
- Charts:
  - Alert volume over time
  - Alerts by severity
  - Alerts by rule, signal, channel, or entity type
  - Case outcomes
  - Review-queue aging
- Filters:
  - Date range
  - Severity
  - Status
  - Rule
  - Entity
  - Channel
  - Assigned analyst

### Acceptance criteria

- [ ] KPI cards are clickable and navigate to filtered views.
- [ ] Charts have accessible labels, legends, and tooltips.
- [ ] Filters update the dashboard without a full-page reload where practical.
- [ ] Loading skeletons are shown during data fetches.
- [ ] Empty, error, and no-permission states are implemented.
- [ ] Sensitive metrics are visible only to authorized roles.

### AI-agent prompt

```text
Add a fraud operations dashboard to Didebaan using existing data sources and metrics. If an endpoint does not exist, create clearly typed mock services marked with TODOs. Use glass cards, charts, filters, and accessible empty/loading/error states.
```

---

## 5. Improve alert triage and investigation workflow

**Labels:** `feature`, `ux`, `frontend`

### Goal

Help analysts quickly understand why an alert fired, assess risk, and take action.

### Alert detail requirements

- Show alert summary, severity, status, detection time, assigned analyst, and related entity.
- Explain why the alert fired using human-readable rule and signal explanations.
- Display risk score, confidence, threshold, and contributing factors where available.
- Provide a timeline of related events.
- Show related alerts, cases, entities, transactions, devices, sessions, or accounts based on available data.
- Support actions such as acknowledge, assign, escalate, dismiss, mark as fraud, or create a case, according to permissions.
- Require confirmation and reason for consequential actions.
- Preserve an audit trail for every action.

### Acceptance criteria

- [ ] Analysts can understand the reason for an alert without reading raw logs.
- [ ] Risk factors and evidence are clearly presented.
- [ ] Alert status and ownership are always visible.
- [ ] Actions are permission-aware and confirmed where appropriate.
- [ ] Every action is recorded in the existing audit mechanism.
- [ ] Loading, empty, error, and unauthorized states are implemented.

### AI-agent prompt

```text
Improve Didebaan’s alert triage and investigation workflow. Create an alert detail experience that explains detection reasons, shows evidence and related context, and supports permission-aware actions. Preserve all detection and audit behavior.
```

---

## 6. Upgrade case management

**Labels:** `feature`, `ux`, `frontend`

### Goal

Make investigations traceable from alert to decision.

### Requirements

- Case list with status, priority, owner, entity, opened date, and last activity.
- Case detail with summary, linked alerts, evidence, notes, decisions, and outcome.
- Clear workflow states: new, in review, awaiting information, escalated, resolved, rejected, or equivalent existing states.
- Add internal notes with author and timestamp.
- Support linking and unlinking related alerts where supported.
- Show case history and decision rationale.
- Prevent ambiguous or untracked case closures.

### Acceptance criteria

- [ ] Users can see the full lifecycle of a case.
- [ ] Case ownership and status are clear.
- [ ] Linked alerts and evidence are easy to inspect.
- [ ] Case decisions require appropriate context or reason where configured.
- [ ] Case history is traceable.
- [ ] Existing case data and permissions are respected.

### AI-agent prompt

```text
Improve Didebaan’s case-management UX without changing backend contracts. Create clear case lists, case detail views, linked-alert context, notes, history, and decision states. Ensure all actions remain auditable.
```

---

## 7. Improve rules, signals, and model transparency

**Labels:** `feature`, `ux`, `frontend`, `trust`

### Goal

Make detection logic understandable to analysts and administrators.

### Requirements

- List rules and signals with name, description, status, owner, version, severity, and last-updated time.
- Show plain-language explanations of what each rule or signal detects.
- Display thresholds, parameters, and applicable channels or entity types where available.
- Show recent performance indicators where the backend provides them, such as trigger volume or alert outcome.
- Distinguish enabled, disabled, draft, experimental, and deprecated rules.
- Make changes to rules auditable and permission-controlled.
- Avoid exposing proprietary model internals or sensitive configuration unnecessarily.

### Acceptance criteria

- [ ] Analysts can understand what a rule or signal does.
- [ ] Rule status and ownership are clear.
- [ ] Configuration details are readable and permission-aware.
- [ ] Rule changes are traceable.
- [ ] No sensitive model or security information is exposed without authorization.

### AI-agent prompt

```text
Improve Didebaan’s rules and signals transparency. Create readable rule and signal views using existing metadata and configuration. Do not alter detection logic. Ensure sensitive configuration is protected by existing permissions.
```

---

## 8. Add entity risk profiles

**Labels:** `feature`, `ux`, `frontend`

### Goal

Give analysts a consolidated view of an account, user, device, merchant, or other monitored entity.

### Requirements

- Entity header with identifier, type, status, risk level, and key attributes.
- Risk score and trend where available.
- Related alerts, cases, transactions, sessions, devices, and notes.
- Timeline of important events.
- Clear data provenance and timestamps.
- Mask sensitive identifiers according to role and product policy.
- Provide quick navigation between related entities.

### Acceptance criteria

- [ ] Users can view an entity’s risk context in one place.
- [ ] Related alerts and cases are easy to access.
- [ ] Sensitive fields are masked or restricted according to permissions.
- [ ] Entity history is understandable and time-ordered.
- [ ] Empty, loading, error, and unauthorized states are implemented.

### AI-agent prompt

```text
Add or improve an entity risk-profile view in Didebaan. Consolidate existing alerts, cases, events, and risk indicators for an entity. Apply masking and role-based visibility to sensitive fields. Do not create new backend capabilities.
```

---

## 9. Upgrade investigation tables and filters

**Labels:** `ui/ux`, `performance`, `frontend`

### Goal

Make large volumes of alerts, cases, entities, and events fast to investigate.

### Requirements

- Sticky headers.
- Column sorting.
- Advanced filtering by date, status, severity, rule, entity, channel, assignee, and risk level.
- Saved filters or queue views where supported.
- Pagination or virtualization for large datasets.
- CSV export only when authorized and safe.
- Numeric alignment and localized number/date formatting.
- Bulk actions with confirmation and permission checks.
- Loading skeletons.
- Mobile-friendly behavior through responsive columns or a detail drawer.

### Acceptance criteria

- [ ] A reusable data-table component exists.
- [ ] Large datasets remain responsive.
- [ ] Filters and exports do not block the UI.
- [ ] Bulk actions are permission-aware and confirmed.
- [ ] Persian and English number/date formats are handled correctly.
- [ ] Empty and error states are implemented.

### AI-agent prompt

```text
Audit Didebaan’s investigation tables and implement a reusable high-performance data table. Add filtering, sorting, bulk actions, and export only where the backend and permissions support them. Use virtualization only if justified by dataset size or existing dependencies.
```

---

## 10. Make forms, settings, and errors actionable

**Labels:** `ux`, `frontend`, `accessibility`

### Goal

Help administrators configure the system confidently and recover from errors.

### Requirements

- Inline field-level validation.
- Summary of validation failures at the top of long forms.
- Links from summary items to the relevant fields.
- Distinct handling for validation errors, permission errors, network errors, and system failures.
- Preserve user input after an error.
- Clear save, saving, saved, unsaved-changes, and discard states.
- Group related settings and use progressive disclosure for advanced options.
- Require confirmation for high-impact configuration changes.

### Acceptance criteria

- [ ] A shared error-message catalog exists.
- [ ] Error messages are specific and actionable.
- [ ] Users can recover from failed submissions without losing input.
- [ ] High-impact settings changes are confirmed.
- [ ] Errors are announced accessibly.
- [ ] Persian and English messages are available.

### AI-agent prompt

```text
Standardize Didebaan’s form, settings, and API error handling. Create a shared error-message catalog and ensure validation failures are visible, specific, and recoverable. Add confirmation for high-impact configuration actions.
```

---

## 11. Improve Persian typography and RTL consistency

**Labels:** `i18n`, `ui/ux`, `accessibility`

### Goal

Make the Persian-first experience feel native and polished.

### Requirements

- Use a high-quality Persian font with sensible fallbacks.
- Set correct `dir`, alignment, punctuation, numerals, and mixed Persian/English handling.
- Test dashboards, alerts, cases, tables, forms, modals, toasts, and command/search UI in RTL.
- Avoid mirroring direction-sensitive icons.
- Prevent clipping or overflow with longer Persian labels.
- Handle IDs, emails, IPs, URLs, code, and technical values correctly in bidirectional text.

### Acceptance criteria

- [ ] All primary screens render correctly in RTL.
- [ ] Mixed Persian/English content is readable.
- [ ] Icons with directional meaning are not incorrectly mirrored.
- [ ] No major text overflow or clipping.
- [ ] Typography hierarchy is consistent.

### AI-agent prompt

```text
Audit every Didebaan screen for RTL and Persian typography issues. Fix layout mirroring, icon direction, number formatting, bidirectional text handling, and overflow. Add visual regression checks if the project has a testing setup.
```

---

## 12. Add polished light and dark themes

**Labels:** `ui/ux`, `glassmorphism`, `frontend`

### Goal

Provide a premium dark experience without losing readability during long investigation sessions.

### Requirements

- Theme toggle persisted in user preferences.
- Default to the operating-system preference.
- Use tokens rather than hard-coded colors.
- Tune glass opacity, blur, borders, and shadows separately per theme.
- Ensure charts, tables, badges, timelines, and risk indicators remain legible.

### Acceptance criteria

- [ ] Users can switch between light and dark themes.
- [ ] Theme preference persists across sessions.
- [ ] All major screens are verified in both themes.
- [ ] Hard-coded colors are replaced with tokens.
- [ ] Glass surfaces remain readable in dark mode.

### AI-agent prompt

```text
Implement theme tokens and a persisted light/dark toggle for Didebaan. Refactor hard-coded colors into tokens. Verify dashboards, alerts, cases, tables, and settings in both themes.
```

---

## 13. Add restrained motion and interaction feedback

**Labels:** `ui/ux`, `glassmorphism`, `accessibility`

### Goal

Make the interface feel responsive without distracting analysts.

### Requirements

- Subtle transitions for page changes, drawers, modals, toasts, popovers, and hover states.
- UI feedback animations should generally be 200–300ms or less.
- Loading skeletons.
- Success and error toasts.
- Optimistic updates only where safe.
- Respect `prefers-reduced-motion`.

### Acceptance criteria

- [ ] Motion tokens are centralized.
- [ ] Interactive components have consistent transitions.
- [ ] Reduced-motion users receive a non-animated equivalent.
- [ ] Animations do not delay comprehension of critical risk information.
- [ ] No excessive or decorative animation is added.

### AI-agent prompt

```text
Add a motion token set and apply consistent transitions to Didebaan’s interactive components. Ensure reduced-motion users get a non-animated equivalent.
```

---

## 14. Meet WCAG AA across primary flows

**Labels:** `accessibility`, `ui/ux`

### Goal

Ensure the redesigned console is usable by everyone.

### Requirements

- Visible focus rings on all interactive elements.
- Keyboard-only operation for navigation, tables, filters, forms, modals, drawers, and alert actions.
- Semantic HTML, landmarks, labels, and ARIA only where necessary.
- WCAG AA contrast, including text over glass surfaces.
- Screen-reader testing for alert triage and case management.
- Do not rely on color alone to communicate severity or risk.

### Acceptance criteria

- [ ] All interactive controls are keyboard accessible.
- [ ] Focus is visible and logically managed.
- [ ] Modals, drawers, and popovers manage focus appropriately.
- [ ] Severity and status are conveyed with text or icons as well as color.
- [ ] Primary flows pass WCAG AA checks.

### AI-agent prompt

```text
Run an accessibility review of Didebaan’s primary pages and flows. Fix issues without changing backend behavior. Prioritize keyboard navigation, focus management, contrast, semantic structure, and non-color-dependent risk indicators.
```

---

## 15. Optimize frontend performance

**Labels:** `performance`, `frontend`

### Goal

Keep the glass UI fast for data-heavy fraud operations.

### Requirements

- Avoid excessive nested backdrop filters and large blur radii.
- Lazy-load routes, charts, timelines, media previews, and heavy components.
- Virtualize long alert, event, or log lists only where justified.
- Memoize expensive table and chart calculations where appropriate.
- Add skeleton loaders and avoid layout shift.
- Measure Core Web Vitals before and after changes.

### Acceptance criteria

- [ ] Heavy routes and components are code-split or lazy-loaded where appropriate.
- [ ] Glass effects do not cause severe scroll or interaction jank.
- [ ] Large investigation tables remain responsive.
- [ ] Layout shift is minimized.
- [ ] Before/after performance metrics are documented.
- [ ] No functional regressions are introduced.

### AI-agent prompt

```text
Profile Didebaan’s heaviest pages and interaction flows. Identify render, bundle, chart, table, and blur-performance bottlenecks, then optimize without changing functionality. Document before/after metrics in the pull request.
```

---

## 16. Add security, privacy, audit, and quality gates

**Labels:** `security`, `privacy`, `testing`, `ui/ux`, `frontend`

### Goal

Ensure the redesigned console remains secure, private, auditable, and maintainable.

### Requirements

- Verify role-based access for every new screen, action, export, and sensitive field.
- Mask or redact sensitive identifiers, credentials, payment data, and personal information.
- Ensure all consequential operator actions remain auditable.
- Add or improve linting, type checking, formatting, and test checks.
- Add unit tests for reusable UI components where a test setup exists.
- Add visual regression coverage for light/dark and RTL/LTR states where practical.
- Test primary flows: dashboard, alert triage, case management, rules, entity profiles, and settings.
- Document how contributors run checks locally.

### Acceptance criteria

- [ ] New UI respects existing authentication and authorization rules.
- [ ] Sensitive data is not exposed in DOM, logs, exports, or client state.
- [ ] Consequential actions are auditable.
- [ ] Contributors can run quality checks with a documented command where practical.
- [ ] Core reusable components have tests or documented manual test steps.
- [ ] Visual checks cover RTL and dark mode where tooling exists.
- [ ] CI fails on meaningful security, UI, type, lint, or accessibility regressions.

### AI-agent prompt

```text
Audit Didebaan’s security, privacy, authorization, audit, test, and CI setup. Ensure the glass UI redesign does not expose sensitive data or bypass approvals. Add pragmatic quality gates without over-engineering the project.
```
