# Plan — M2 Administration

- **Goal:** Administrators manage users and system settings; lookups are available to later screens.
- **Depends on:** M1
- **Docs:** [03-use-cases.md](../../docs/03-use-cases.md), [04-information-architecture.md](../../docs/04-information-architecture.md), [business-rules.md](../../docs/requirements/business-rules.md), [09-algorithms.md §1 Parameters](../../docs/09-algorithms.md#1-parameters)

## M2-1 SCR-70 Users

| Field | Value |
|---|---|
| Stories / AC | US17 · AC-UC18 |
| Rules / NFR | BR-001, BR-021 · NFR-SEC-002, NFR-SEC-004 |
| API | `GET /users`, `POST /users`, `GET /users/{userId}`, `PUT /users/{userId}`, `PATCH /users/{userId}/status` |
| Tables | `app_users`, `audit_logs` |
| Backend modules | `users` |
| Frontend | `(workspace)/users`, `features/users`; list page with create/edit modal |

**Backend**
- [ ] List with paging and filters per openapi.yaml; Admin only (others `403`)
- [ ] Create with role and initial password; unique email → conflict
- [ ] Edit and enable/disable; audit events

**Frontend**
- [ ] TanStack Table list, filters, paging; form modal with focus trap
- [ ] Empty, loading, error, conflict states

**Tests**
- [ ] Non-admin `403`; duplicate email; disable blocks login; audit written

**Done when:** AC-UC18 passes.

## M2-2 SCR-60 Settings

| Field | Value |
|---|---|
| Stories / AC | US16 · AC-UC17 |
| Rules / NFR | BR-019, BR-021 |
| API | `GET /settings`, `PUT /settings`, `GET /lookups` |
| Tables | `settings`, `categories`, `departments`, `branches`, `software`, `device_groups`, `audit_logs` |
| Backend modules | `settings` (settings + lookups) |
| Frontend | `(workspace)/settings`, `features/settings`; tabbed page |

**Backend**
- [ ] Read and update thresholds, tracing window, baseline window, detection interval, log retention, weights
- [ ] Range validation per BR-019 (`400`); Admin only
- [ ] `CONFIG_CHANGE` audit event; values read fresh by the next job (no redeploy)
- [ ] `GET /lookups` for all roles

**Frontend**
- [ ] Tabs for detection, ranking weights, retention
- [ ] Inline range errors; save disabled while submitting

**Tests**
- [ ] Every BR-019 boundary; non-admin `403`; audit written

**Done when:** AC-UC17 passes.

**Open:** Q-11 (F09 lists category and mapping management, but openapi.yaml only exposes `GET /lookups`).
