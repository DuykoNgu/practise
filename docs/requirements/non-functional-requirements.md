# Non-Functional Requirements — CIC V1

> Design status: PROPOSED V1 BASELINE
>
> Implementation status: TARGET; verification is PLANNED

These targets are a realistic baseline for an internal IT tool in a small-to-medium organization, not a contractual SLA. A requirement is complete only when its verification passes under the reference workload below.

## Performance and timeliness

| ID | Statement | Measurement | Verification |
|---|---|---|---|
| NFR-PERF-001 | Paginated read APIs have P95 latency ≤ 500 ms. | Server time under the reference workload | `PERF-READ-001` load test |
| NFR-PERF-002 | Create/update APIs have P95 latency ≤ 800 ms, including the audit write. | Server time | `PERF-WRITE-001` |
| NFR-PERF-003 | The dashboard and the anomaly detail (suspects, logs, suggestion) have P95 latency ≤ 2 s. | Server time per request | `PERF-DASH-001` |
| NFR-PERF-004 | Integration intake of a 1,000-item batch returns within 3 s (P95). | Server time including masking | `PERF-INGEST-001` |
| NFR-TIME-001 | An anomaly is detected within 2 detection intervals (default 30 min) after the bucket that crosses the threshold closes. | Bucket end time vs `anomalies.detected_at` | `INT-DETECT-001` with seeded data |
| NFR-TIME-002 | Suspects are stored within 1 minute after their anomaly is created. | `suspects.created_at − anomalies.detected_at` | `INT-RANK-001` |
| NFR-TIME-003 | A suggestion reaches a final status (`READY`, `NO_SUPPORT`, or `FAILED`) within 5 minutes after its suspect is stored, while the LLM provider is reachable. | `suggestions.generated_at − suspects.created_at` | `INT-AI-001` with a stub LLM |

## Capacity

| ID | Statement | Measurement | Verification |
|---|---|---|---|
| NFR-CAP-001 | The system supports 200,000 tickets, 20,000 changes, and 2,000,000 error logs within the retention period. | Seeded database size | `PERF-CAP-001` |
| NFR-CAP-002 | 50 concurrent users are supported while meeting NFR-PERF-001–003. | 50 virtual users, mixed read/write | `PERF-CONC-001` |
| NFR-CAP-003 | Intake sustains 100,000 error logs per day. | Logs accepted per day in a soak test | `PERF-INGEST-002` |
| NFR-IMPORT-001 | Import files are at most 10 MB and 5,000 rows; import is synchronous and atomic. | File size, rows, transaction state | `INT-IMPORT-001` |

## Security and privacy

| ID | Statement | Measurement | Verification |
|---|---|---|---|
| NFR-SEC-001 | JWT access tokens expire 30 minutes after issue; V1 has no refresh token. | `exp − iat = 30 min` | `INT-AUTH-001` |
| NFR-SEC-002 | Passwords have at least 8 characters and are stored only as a slow salted hash (bcrypt or Argon2). | Validation and stored format | `UNIT-AUTH-001` |
| NFR-SEC-003 | Login allows at most 5 failed attempts per account per 15 minutes, then returns `429`. | Rate-limit counter | `SEC-AUTH-001` |
| NFR-SEC-004 | Every protected operation checks role and ownership in the backend. | Endpoint × role test matrix | `INT-RBAC-*` |
| NFR-SEC-005 | Passwords, hashes, JWTs, API keys, `LLM_API_KEY`, and raw log messages never appear in application logs, audit entries, or LLM requests. | Inspection of sampled logs, audit rows, and captured LLM prompts | `SEC-LOG-001` |
| NFR-SEC-006 | API keys are stored only as hashes and can be deactivated without a redeploy. | Database inspection, deactivation test | `SEC-APIKEY-001` |
| NFR-PRIV-001 | Masking removes 100% of the seeded sensitive patterns (user names, e-mail, IPv4/IPv6, Windows and Unix paths) in a test corpus of at least 500 log lines. | Remaining matches after masking | `UNIT-MASK-001`, `cic-ai eval masking` |
| NFR-PRIV-002 | Only masked text is sent to the LLM provider. | Captured requests in integration tests | `INT-AI-002`, `cic-ai eval suggestion` |

## AI quality and safety

| ID | Statement | Measurement | Verification |
|---|---|---|---|
| NFR-AI-001 | 100% of stored cause statements have at least one valid evidence item. | Query over `suggestion_statements` and `statement_evidence` | `INT-AI-003`, `cic-ai eval suggestion` |
| NFR-AI-002 | No suggestion containing an `LLM_KNOWLEDGE` step is labeled `CONFIRMED`. | Query over suggestions | `INT-AI-004`, `cic-ai eval suggestion` |
| NFR-AI-003 | An LLM outage does not delay or change suspect ranking. | Ranking with the LLM stub failing | `INT-AI-005` |
| NFR-AI-004 | Target: the confirmed cause is in the top 3 suspects for ≥ 70% of anomalies that received a `CORRECT_CAUSE` verdict. | Monthly report from `suspect_feedback` | `OPS-QUALITY-001` (tracked, used to tune weights) |

## Reliability, operations, maintainability, usability

| ID | Statement | Measurement | Verification |
|---|---|---|---|
| NFR-REL-001 | Target availability is 99.5% per month, excluding planned maintenance. | Successful health-check minutes | `OPS-AVAIL-001` |
| NFR-REL-002 | A job that fails is retried up to 3 attempts; two workers never run the same job. | Job table state under concurrent workers | `INT-JOB-001` |
| NFR-BCP-001 | PostgreSQL is backed up daily and kept 30 days; RPO ≤ 24 h, RTO ≤ 4 h. | Backup timestamps, timed restore | `OPS-RESTORE-001` |
| NFR-RET-001 | Error logs are kept for the configured retention (default 30 days); audit entries are kept at least 1 year. | Row ages | `OPS-RET-001` |
| NFR-OBS-001 | API and worker emit structured JSON logs with a trace id and expose `/health`; the worker reports its last job time. | Log schema, health checks | `INT-OBS-001` |
| NFR-MAINT-001 | Unit coverage ≥ 80% for module services and `cic_ai`; ≥ 90% for `SuspectScorer`, `EvidenceValidator`, masking, and policies. | Coverage report | CI |
| NFR-MAINT-002 | Lint, type checks, tests, OpenAPI validation, migrations, and `cic-ai eval all` (stub mode) pass in CI with no errors. | CI exit status | CI |
| NFR-ACC-001 | Inputs have visible labels, status is never shown by color alone, and keyboard/focus behavior meets applicable WCAG 2.1 AA criteria. | Accessibility audit | `A11Y-001` |
| NFR-I18N-001 | Times are stored in UTC and displayed in the viewer's time zone; the UI supports Vietnamese text. | UI and API checks | `UI-TIME-001` |

## Reference workload

- The database is seeded to NFR-CAP-001 with realistic categories, departments, branches, and 8 weeks of ticket history.
- 50 virtual users run a mix of 80% reads and 20% writes; ingestion runs in parallel at the NFR-CAP-003 rate.
- The LLM provider is replaced by a stub with a fixed 3-second latency for performance tests; real-provider latency is outside the system's control and is not part of NFR-PERF.
