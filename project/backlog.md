# Backlog — CIC V1

Source of truth for story text: [05-invest-requirements.md](../docs/05-invest-requirements.md). Priority comes from the feature it belongs to in [02-features.md](../docs/02-features.md). Acceptance criteria: [08-acceptance-criteria.md](../docs/08-acceptance-criteria.md). Which work items deliver each story, and their status, is generated in [tracker.md § Stories](tracker.md#stories) from [screens/](screens/README.md).

| ID | Story (short) | Feature | Priority | Acceptance |
|---|---|---|---|---|
| US01 | Log in | F01 | Must | AC-UC01 |
| US02 | Log out | F01 | Must | AC-UC02 |
| US18 | Maintain profile and password | F11 | Must | AC-UC19 |
| US17 | Manage users | F11 | Must | AC-UC18 |
| US16 | Configure thresholds, window, weights, lookups | F09 | Should | AC-UC17 |
| US06 | Filter and inspect changes | F02 | Must | AC-UC04 |
| US04 | Create change with scope and rollback plan | F02 | Must | AC-UC05 |
| US05 | Edit change and status (own records for Change Engineer) | F02 | Must | AC-UC06 |
| US09 | Filter and inspect tickets | F03 | Must | AC-UC07 |
| US07 | Add ticket manually | F03 | Must | AC-UC08 |
| US08 | Preview and import CSV/Excel | F03 | Must | AC-UC09 |
| US19 | ITSM pushes tickets and changes | F02, F03 | Must | AC-UC10 |
| US10 | View baseline vs actual | F04 | Must | AC-UC11 |
| US11 | Recompute baseline | F04 | Must | AC-UC12 |
| US12 | Anomaly with ranked, explained suspects | F05, F06 | Must | AC-UC13, AC-UC14 |
| US13 | Rollback plan and implementer of a suspect | F07 | Must | AC-UC14 |
| US14 | Suspect feedback | F08 | Should | AC-UC15 |
| US03 | Dashboard of open anomalies | F07 | Must | AC-UC03 |
| US22 | Log source pushes error logs | F13 | Should | AC-UC22 |
| US23 | Related error logs of an anomaly | F13 | Should | AC-UC23 |
| US20 | Suggested cause and resolution with evidence | F12 | Should | AC-UC20 |
| US21 | Confirm or reject suggestion | F12 | Should | AC-UC21 |
| US15 | Inspect audit events | F10 | Should | AC-UC16 |

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
