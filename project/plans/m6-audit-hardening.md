# Plan — M6 Audit and hardening

- **Goal:** important actions are traceable on screen, and every NFR is verified under the reference workload.
- **Depends on:** M5
- **Docs:** [non-functional-requirements.md](../../docs/requirements/non-functional-requirements.md), [business-rules.md BR-021](../../docs/requirements/business-rules.md), [04-information-architecture.md](../../docs/04-information-architecture.md)

## M6-1 SCR-50 Audit log

| Field | Value |
|---|---|
| Stories / AC | US15 · AC-UC16 |
| Rules / NFR | BR-021 · NFR-RET-001 |
| API | `GET /audit-logs` |
| Tables | `audit_logs` |
| Backend modules | `audit` (read side; write side exists since M1-1) |
| Frontend | `(workspace)/audit`, `features/audit` |

**Tasks**
- [ ] Backend list with filters (user, action, object, time) and paging; Admin and IT Manager only
- [ ] Frontend table with filters; entries are read-only
- [ ] Tests: role checks; every BR-021 action appears

**Done when:** AC-UC16 passes.

## M6-2 NFR verification

| Group | Verifications |
|---|---|
| Performance | PERF-READ-001, PERF-WRITE-001, PERF-DASH-001, PERF-INGEST-001 |
| Capacity | PERF-CAP-001, PERF-CONC-001, PERF-INGEST-002, INT-IMPORT-001 |
| Timeliness | INT-DETECT-001, INT-RANK-001, INT-AI-001 |
| Security and privacy | INT-AUTH-001, UNIT-AUTH-001, SEC-AUTH-001, INT-RBAC-*, SEC-LOG-001, SEC-APIKEY-001, UNIT-MASK-001, INT-AI-002 |
| AI quality | INT-AI-003, INT-AI-004, INT-AI-005, OPS-QUALITY-001 report |
| Reliability and operations | OPS-AVAIL-001, INT-JOB-001, OPS-RESTORE-001, OPS-RET-001, INT-OBS-001 |
| Maintainability, usability | Coverage report, CI, A11Y-001 on every screen, UI-TIME-001 |

**Tasks**
- [ ] Seed the reference workload (NFR "Reference workload")
- [ ] Load tests with 50 virtual users and a 3-second LLM stub
- [ ] RBAC endpoint × role matrix test
- [ ] Accessibility audit of every screen; fix findings
- [ ] Backup and timed restore; retention jobs verified

**Done when:** every verification passes and results are recorded in [decisions.md](../decisions.md).

**Open:** Q-06 (deployment and backups).
