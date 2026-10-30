# Data model (PostgreSQL schema design)

> Design status: TARGET V1
>
> Runtime status: SCHEMA DESIGN ONLY; validated on PostgreSQL 16 with a smoke test, not connected to an application

Schema `cic`, 30 tables. Sources of truth: [cic.sql](../src/database/cic.sql), [DATABASE.md](DATABASE.md).

## Tables

| Group | Table | Purpose |
|---|---|---|
| Identity | `app_users` | Users, role, active status, password hash; e-mail is case-insensitive and unique |
| Identity | `api_clients` | ITSM system and log sources; only the hash of the API key is stored |
| Lookups | `departments`, `branches`, `software`, `device_groups`, `categories` | Scope dimensions shared by changes, tickets, logs, baselines, anomalies. `device_groups` maps a device to a department and branch; `categories.keywords` feeds the keyword match factor |
| Inputs | `changes` | Change record; the rollback plan is 1:1 and stored inline (`rollback_*` columns) |
| Inputs | `change_departments`, `change_branches`, `change_software`, `change_device_groups` | Change scope, one junction table per dimension so every scope value is a real foreign key |
| Inputs | `import_batches` | One CSV/Excel import; atomic (a failed batch has 0 imported rows) |
| Inputs | `tickets` | One ticket, from manual entry, import, or API |
| Inputs | `error_logs` | One error log pushed by a log source; only the masked message is stored |
| Detection | `baseline_runs`, `baseline_cells` | One recompute and its cells (mean and deviation per category × weekday × hour, optionally per department or branch) |
| Detection | `anomalies` | Abnormal spike for a group (category, department, branch, software) against a baseline run |
| Detection | `anomaly_tickets`, `anomaly_logs` | Tickets and logs that belong to an anomaly |
| Ranking | `suspects`, `suspect_factors` | Ranked change per anomaly, rule-based score, one explanation per factor |
| Ranking | `suspect_feedback` | One verdict per user per suspect |
| AI | `suggestions` | Suggested resolution of a suspect, versioned (regeneration adds a version); holds the label and the confirm/reject decision |
| AI | `suggestion_statements` | Cause and step statements, each with a basis (STANDARD or LLM_KNOWLEDGE) |
| AI | `statement_evidence` | What a statement cites: log, ticket, change, rollback plan, past confirmed incident, or guideline |
| AI | `guidelines` | Internal guidance used as a "standard" source |
| Operations | `jobs` | Job table between the Backend API and the Analysis Worker |
| Operations | `settings` | Exactly one row of configuration |
| Operations | `audit_logs` | Append-only business audit trail |

There are no dashboard tables: KPIs and charts are calculated from tickets, baselines, anomalies, and suspects.

## Rules enforced by the database

| Rule | How |
|---|---|
| A cause statement is always evidence-based | `suggestion_statements`: a `CAUSE` must have basis `STANDARD` |
| An evidence row cites exactly one thing of its type | `statement_evidence` CHECK on `type` and the typed foreign keys |
| `CONFIRMED` only after a person confirms | `suggestions`: label `CONFIRMED` requires decision `CONFIRMED`; decision, decider, and time are set together |
| Score is 0–100; one change per anomaly; unique rank | `suspects` CHECK and UNIQUE constraints |
| Import is atomic | `import_batches`: a `FAILED` batch has `imported_rows = 0` |
| Integration intake is idempotent | `UNIQUE (source_client_id, external_id)` on `changes`, `tickets`, `error_logs` |
| Source is consistent | API rows need a client and an external id; imported tickets need a batch |
| An anomaly names at least one group | `anomalies`: at least one of category, department, branch, software |
| A rollback plan has steps | `changes`: `rollback_available` requires `rollback_steps` |
| One settings row | `settings.id = 1` |
| Every foreign key is indexed | Checked against `pg_index` |

## Rules enforced by the application

- A cause statement must have at least one evidence row (a cross-row rule; checked by the Evidence Validator before insert).
- A `CONFIRMED` label also requires every statement to be `STANDARD` (cross-row; checked when the decision is saved).
- A change must name at least one scope value.
- A Change Engineer may update only changes where they are the implementer.
- Log messages are masked before insert; `audit_logs.details` never contains passwords, hashes, tokens, or API keys.

## Log retention

A scheduled job deletes `error_logs` older than `settings.log_retention_days`. Links in `anomaly_logs` are deleted with the log. Evidence keeps a masked `log_snapshot`, and its `error_log_id` becomes NULL, so a confirmed suggestion still shows what it was based on.

## Job table

The Backend API inserts a row into `jobs`; the Analysis Worker claims one with `SELECT … FOR UPDATE SKIP LOCKED`, so two workers never run the same job. Failed jobs are retried until `max_attempts`.

## Mapping to the API contract

| API | Database |
|---|---|
| `Change.scope` (lists of names) | Four junction tables with lookup ids; the API maps names/codes to ids |
| `Change.rollbackPlan` | `changes.rollback_*` columns |
| `Suspect.factors` | `suspect_factors` |
| `Suspect.feedback` | The current user's row in `suspect_feedback` |
| `SuggestedResolution` | Latest `suggestions` version + `suggestion_statements` + `statement_evidence` |
| `ErrorLogGroup` | `anomaly_logs` joined to `error_logs`, grouped by `signature` |
| `Settings.weights` | Five `weight_*` columns |
| `ingestTickets`, `ingestChanges`, `ingestLogs` | Rows with `source = 'API'` and `source_client_id` |

## Validation performed

The schema was loaded into PostgreSQL 16 and exercised with the printer example (a patch for Accounting, 14 "cannot print" tickets, 3 error logs, one anomaly, one suspect, a suggestion with evidence, a confirmation). Eleven invalid inserts were rejected as intended: an LLM-knowledge cause, evidence citing two things, a confirmed label without a decision, a failed import with rows, a score above 100, a duplicate log id, an API ticket without a client, an anomaly with no group, a second settings row, a duplicate e-mail in different case, and a rollback plan without steps.
