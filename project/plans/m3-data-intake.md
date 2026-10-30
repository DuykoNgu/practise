# Plan — M3 Data intake

- **Goal:** changes and tickets enter CIC through the UI, file import, and the ITSM API.
- **Depends on:** M2 (lookups, users)
- **Docs:** [01-scope.md](../../docs/01-scope.md), [02-features.md F02, F03](../../docs/02-features.md), [business-rules.md](../../docs/requirements/business-rules.md), [class diagrams §2](../../docs/architecture/uml/01-class-diagrams.md), [sequence §2](../../docs/architecture/uml/02-sequence-diagrams.md#2-create-and-edit-a-change--post-changes-put-changeschangeid)

## M3-1 SCR-20–22 Changes

| Field | Value |
|---|---|
| Stories / AC | US06, US04, US05 · AC-UC04, AC-UC05, AC-UC06 |
| Rules / NFR | BR-001, BR-002, BR-003, BR-004, BR-020, BR-021 · NFR-PERF-001, NFR-PERF-002 |
| API | `GET /changes`, `POST /changes`, `GET /changes/{changeId}`, `PUT /changes/{changeId}`, `PATCH /changes/{changeId}/status` |
| Tables | `changes`, `change_departments`, `change_branches`, `change_software`, `change_device_groups`, `audit_logs` |
| Design | Sequence §2; class diagrams §2 Change Management |
| Backend modules | `changes` |
| Frontend | `(workspace)/changes`, `features/changes`; list (SCR-20), create/edit modal (SCR-21), detail modal (SCR-22) |

**Backend**
- [ ] List with filters (type, time, scope, status) and paging
- [ ] Create/edit with scope (≥ 1 item) and rollback plan rules
- [ ] Own-record rule for Change Engineers; status transitions including `ROLLED_BACK`
- [ ] Optimistic concurrency → `409`; audit events

**Frontend**
- [ ] Table with filters; add/edit modal; detail modal; status action
- [ ] Hidden actions for roles that cannot edit; conflict state keeps input

**Tests**
- [ ] Role × action matrix; own-record rule; scope and rollback validation; conflict; audit

**Done when:** AC-UC04, AC-UC05, AC-UC06 pass.

## M3-2 SCR-30 Tickets

| Field | Value |
|---|---|
| Stories / AC | US09, US07 · AC-UC07, AC-UC08 |
| Rules / NFR | BR-001, BR-020, BR-021 · NFR-PERF-001 |
| API | `GET /tickets`, `POST /tickets`, `GET /tickets/{ticketId}` |
| Tables | `tickets`, `audit_logs` |
| Backend modules | `tickets` |
| Frontend | `(workspace)/tickets`, `features/tickets`; list, add modal, detail |

**Backend**
- [ ] List with filters (time, category, department, branch, software) and paging
- [ ] Manual create (Agent, IT Manager, Admin); source `MANUAL`

**Frontend**
- [ ] Table with filters; add modal; detail view

**Tests**
- [ ] Filters; role checks; validation

**Done when:** AC-UC07 and AC-UC08 pass.

## M3-3 SCR-31 Ticket import

| Field | Value |
|---|---|
| Stories / AC | US08 · AC-UC09 |
| Rules / NFR | BR-005, BR-006, BR-021 · NFR-IMPORT-001 |
| API | `POST /ticket-imports/preview`, `GET /ticket-imports`, `POST /ticket-imports`, `GET /ticket-imports/{importId}` |
| Tables | `import_batches`, `tickets`, `audit_logs` |
| Backend modules | `tickets` |
| Frontend | `(workspace)/tickets/import`, `features/tickets`; preview, submit, history |

**Backend**
- [ ] Parse CSV and Excel (openpyxl/pandas); ≤ 10 MB and ≤ 5,000 rows checked before parsing completes
- [ ] Preview with per-row errors; submit stores all rows or none in one transaction
- [ ] File kept under `FILE_STORAGE_DIR`; audit event `IMPORT`

**Frontend**
- [ ] Upload, preview table with row errors, submit, history list
- [ ] Progress and duplicate-submit protection

**Tests**
- [ ] Size and row limits; invalid rows block submit; atomic rollback; history

**Done when:** AC-UC09 passes.

**Open:** I-05 (CLAUDE.md maps SCR-31 to `jobs`, but NFR-IMPORT-001 makes import synchronous).

## M3-4 ITSM integration (API only)

| Field | Value |
|---|---|
| Stories / AC | US19 · AC-UC10 |
| Rules / NFR | BR-007 · NFR-PERF-004, NFR-SEC-006 |
| API | `POST /integration/tickets`, `POST /integration/changes` (`X-API-Key`) |
| Tables | `api_clients`, `tickets`, `changes`, change scope tables |
| Backend modules | `integration` → `tickets.service`, `changes.service` |

**Backend**
- [ ] API-key auth for active `ITSM` clients; wrong or inactive key `401`
- [ ] Batches ≤ 1,000 items; idempotent by (client, `externalId`); response counts accepted/duplicate/rejected
- [ ] Source `API` on stored records

**Tests**
- [ ] Key checks; batch limit; duplicates; partial rejections; 1,000-item timing

**Done when:** AC-UC10 passes; records appear on SCR-20 and SCR-30.

**Open:** Q-03 (ITSM payload mapping), Q-12 (API client management).
