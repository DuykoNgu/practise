# Backlog — CIC V1

Source of truth for story text: [05-invest-requirements.md](../docs/05-invest-requirements.md). Priority comes from the feature it belongs to in [02-features.md](../docs/02-features.md). Acceptance criteria: [08-acceptance-criteria.md](../docs/08-acceptance-criteria.md).

| ID | Story (short) | Feature | Priority | Screen | FE feature | BE modules | Acceptance | Milestone | Status |
|---|---|---|---|---|---|---|---|---|---|
| US01 | Log in | F01 | Must | SCR-01 | `auth` | `auth`, `users`, `audit` | AC-UC01 | M1 | ⬜ |
| US02 | Log out | F01 | Must | Shell → SCR-01 | `auth` | `auth`, `audit` | AC-UC02 | M1 | ⬜ |
| US18 | Maintain profile and password | F11 | Must | SCR-80 | `profile` | `users` | AC-UC19 | M1 | ⬜ |
| US17 | Manage users | F11 | Must | SCR-70 | `users` | `users` | AC-UC18 | M2 | ⬜ |
| US16 | Configure thresholds, window, weights, lookups | F09 | Should | SCR-60 | `settings` | `settings` | AC-UC17 | M2 | ⬜ |
| US06 | Filter and inspect changes | F02 | Must | SCR-20, SCR-22 | `changes` | `changes` | AC-UC04 | M3 | ⬜ |
| US04 | Create change with scope and rollback plan | F02 | Must | SCR-21 | `changes` | `changes` | AC-UC05 | M3 | ⬜ |
| US05 | Edit change and status (own records for Change Engineer) | F02 | Must | SCR-21 | `changes` | `changes` | AC-UC06 | M3 | ⬜ |
| US09 | Filter and inspect tickets | F03 | Must | SCR-30 | `tickets` | `tickets` | AC-UC07 | M3 | ⬜ |
| US07 | Add ticket manually | F03 | Must | SCR-30 | `tickets` | `tickets` | AC-UC08 | M3 | ⬜ |
| US08 | Preview and import CSV/Excel | F03 | Must | SCR-31 | `tickets` | `tickets`, `jobs` | AC-UC09 | M3 | ⬜ |
| US19 | ITSM pushes tickets and changes | F02, F03 | Must | — (API) | — | `integration` | AC-UC10 | M3 | ⬜ |
| US10 | View baseline vs actual | F04 | Must | SCR-40 | `baseline` | `baseline` | AC-UC11 | M4 | ⬜ |
| US11 | Recompute baseline | F04 | Must | SCR-40 | `baseline` | `baseline`, `jobs` | AC-UC12 | M4 | ⬜ |
| US12 | Anomaly with ranked, explained suspects | F05, F06 | Must | SCR-10, SCR-11 | `anomalies` | `anomalies`, `jobs` | AC-UC13, AC-UC14 | M4 | ⬜ |
| US13 | Rollback plan and implementer of a suspect | F07 | Must | SCR-11 | `anomalies` | `anomalies`, `changes` | AC-UC14 | M4 | ⬜ |
| US14 | Suspect feedback | F08 | Should | SCR-11 | `anomalies` | `anomalies` | AC-UC15 | M4 | ⬜ |
| US03 | Dashboard of open anomalies | F07 | Must | SCR-02 | `dashboard` | `dashboard` | AC-UC03 | M4 | ⬜ |
| US22 | Log source pushes error logs | F13 | Should | — (API) | — | `logs`, `integration`, `cic_ai` | AC-UC22 | A1–A2, M5 | ⬜ |
| US23 | Related error logs of an anomaly | F13 | Should | SCR-11 | `anomalies` | `anomalies`, `logs` | AC-UC23 | M5 | ⬜ |
| US20 | Suggested cause and resolution with evidence | F12 | Should | SCR-11 | `suggestions` | `suggestions`, `cic_ai` | AC-UC20 | A3–A4, M5 | ⬜ |
| US21 | Confirm or reject suggestion | F12 | Should | SCR-11 | `suggestions` | `suggestions` | AC-UC21 | M5 | ⬜ |
| US15 | Inspect audit events | F10 | Should | SCR-50 | `audit` | `audit` | AC-UC16 | M6 | ⬜ |

## Cross-cutting constraints

Apply to every story; checked in [definition-of-done.md](definition-of-done.md).

| Constraint | Source |
|---|---|
| Role and ownership enforced in the backend | BR-001, BR-002, NFR-SEC-004 |
| Audit event for every listed action | BR-021 |
| UTC storage, viewer time zone display, Vietnamese text supported | BR-020, NFR-I18N-001 |
| UI states: loading, empty, validation, API error, 401, 403, conflict, success | [04-information-architecture.md](../docs/04-information-architecture.md#uiux-state-contract) |
| Accessibility WCAG 2.1 AA | NFR-ACC-001 |
| No secrets or raw logs in application logs, audit, or LLM requests | NFR-SEC-005 |
