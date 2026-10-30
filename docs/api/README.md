# API documentation

> Design status: TARGET V1
>
> Contract: [`openapi.yaml`](openapi.yaml) (OpenAPI 3.0.3, 41 operations, validated with `openapi-spec-validator`)

The contract is derived from the use cases ([Actors, roles, use cases](../03-use-cases.md)) and the screens ([Information architecture](../04-information-architecture.md)). It will be adjusted when the data model is defined.

## Conventions

| Topic | Rule |
|---|---|
| Base path | `/api/v1` |
| Format | JSON (`application/json`); file upload uses `multipart/form-data` |
| Authentication | `Authorization: Bearer <JWT>` from `login`; the ITSM integration uses the `X-API-Key` header (also used by the log source) |
| Authorization | Each operation declares allowed roles in `x-roles`; the backend enforces them. A Change Engineer may update only changes they implemented |
| Time | ISO 8601 with time zone (`date-time`); the UI shows the viewer's time zone |
| Pagination | `page` (from 1) and `pageSize` (default 20, max 100); responses carry `page`, `pageSize`, `total`, `items` |
| Errors | `application/problem+json` with `title`, `status`, `traceId`, and field `errors`. `401` returns the client to Login; `403` shows the Forbidden screen |
| Idempotency | ITSM and log ingestion deduplicate by `externalId` |
| Import | CSV/Excel import is atomic: every row is accepted or none |

## Domain rules reflected in the contract

- A suspect has `score` 0–100 computed by rules and statistics, `level` (High / Medium / Low), and `factors` that explain each contribution. The LLM never computes the score.
- Error logs are pushed by a log source (`ingestLogs`), masked on receipt, and shown per anomaly grouped by signature (`listAnomalyLogs`). Logs are kept for `logRetentionDays`.
- A statement about the cause must cite at least one `evidence` item (log, ticket, change, past incident). A resolution step has a `basis`: `STANDARD` cites its source, `LLM_KNOWLEDGE` may have no evidence and is always a hypothesis.
- `label` is `CONFIRMED` only when every statement is `STANDARD` and a person confirmed it; otherwise `HYPOTHESIS`. A suspect with no supported cause returns `404` for `getSuggestedResolution`.
- Only IT Manager, Change Engineer, and Admin can call `confirmSuggestedResolution`. Agents can read suggestions and give suspect feedback.
- The system only suggests; it exposes no operation that executes a rollback or fix.

## Operations

| Tag | Method | Path | operationId | Purpose | Allowed roles |
|---|---|---|---|---|---|
| Auth | `POST` | `/auth/login` | `login` | Log in (UC01) | Public |
| Auth | `POST` | `/auth/logout` | `logout` | Log out (UC02) | All roles |
| Dashboard | `GET` | `/dashboard` | `getDashboard` | Incident dashboard (UC03) | All roles |
| Anomalies | `GET` | `/anomalies` | `listAnomalies` | List anomalies (UC14) | All roles |
| Anomalies | `GET` | `/anomalies/{anomalyId}` | `getAnomaly` | Anomaly detail (UC14) | All roles |
| Anomalies | `GET` | `/anomalies/{anomalyId}/suspects` | `listSuspects` | Ranked suspects with per-factor explanation (UC14) | All roles |
| Anomalies | `GET` | `/anomalies/{anomalyId}/tickets` | `listAnomalyTickets` | Tickets belonging to an anomaly (UC14) | All roles |
| Anomalies | `GET` | `/anomalies/{anomalyId}/logs` | `listAnomalyLogs` | Error logs related to an anomaly, grouped by signature (UC23) | All roles |
| Anomalies | `GET` | `/anomalies/{anomalyId}/timeline` | `getAnomalyTimeline` | Timeline of changes and tickets (UC14) | All roles |
| Anomalies | `POST` | `/suspects/{suspectId}/feedback` | `submitSuspectFeedback` | Mark a suspect as the cause or unrelated (UC15) | All roles |
| Suggestions | `GET` | `/suspects/{suspectId}/suggestion` | `getSuggestedResolution` | Suggested cause and resolution of a suspect (UC20) | All roles |
| Suggestions | `PUT` | `/suspects/{suspectId}/suggestion/confirmation` | `confirmSuggestedResolution` | Confirm or reject a suggested resolution (UC21) | Admin, IT Manager, Change Engineer |
| Changes | `GET` | `/changes` | `listChanges` | List changes (UC04) | All roles |
| Changes | `POST` | `/changes` | `createChange` | Create a change record (UC05) | Admin, IT Manager, Change Engineer |
| Changes | `GET` | `/changes/{changeId}` | `getChange` | Change detail (UC04) | All roles |
| Changes | `PUT` | `/changes/{changeId}` | `updateChange` | Update a change record (UC06) | Admin, IT Manager, Change Engineer |
| Changes | `PATCH` | `/changes/{changeId}/status` | `updateChangeStatus` | Update change status, including rolled back (UC06) | Admin, IT Manager, Change Engineer |
| Tickets | `GET` | `/tickets` | `listTickets` | List tickets (UC07) | All roles |
| Tickets | `POST` | `/tickets` | `createTicket` | Add a ticket manually (UC08) | Admin, IT Manager, Agent |
| Tickets | `GET` | `/tickets/{ticketId}` | `getTicket` | Ticket detail (UC07) | All roles |
| Ticket imports | `POST` | `/ticket-imports/preview` | `previewTicketImport` | Validate a CSV/Excel file and preview rows (UC09) | Admin, IT Manager, Agent |
| Ticket imports | `GET` | `/ticket-imports` | `listTicketImports` | Import history (UC09) | Admin, IT Manager, Agent |
| Ticket imports | `POST` | `/ticket-imports` | `createTicketImport` | Import tickets (UC09) | Admin, IT Manager, Agent |
| Ticket imports | `GET` | `/ticket-imports/{importId}` | `getTicketImport` | Import batch detail (UC09) | Admin, IT Manager, Agent |
| Baseline | `GET` | `/baselines` | `getBaseline` | Baseline versus actual (UC11) | All roles |
| Baseline | `POST` | `/baselines/recompute` | `recomputeBaseline` | Recompute baseline (UC12) | Admin, IT Manager |
| Audit | `GET` | `/audit-logs` | `listAuditLogs` | Activity log (UC16) | Admin, IT Manager |
| Settings | `GET` | `/settings` | `getSettings` | Read system configuration (UC17) | Admin |
| Settings | `PUT` | `/settings` | `updateSettings` | Update system configuration (UC17) | Admin |
| Users | `GET` | `/users` | `listUsers` | List users (UC18) | Admin |
| Users | `POST` | `/users` | `createUser` | Create a user (UC18) | Admin |
| Users | `GET` | `/users/{userId}` | `getUser` | User detail (UC18) | Admin |
| Users | `PUT` | `/users/{userId}` | `updateUser` | Update a user and role (UC18) | Admin |
| Users | `PATCH` | `/users/{userId}/status` | `updateUserStatus` | Enable or disable a user (UC18) | Admin |
| Profile | `GET` | `/profile` | `getProfile` | Own profile (UC19) | All roles |
| Profile | `PUT` | `/profile` | `updateProfile` | Update own profile; the role cannot be changed here (UC19) | All roles |
| Profile | `POST` | `/profile/password` | `changePassword` | Change own password (UC19) | All roles |
| Lookups | `GET` | `/lookups` | `getLookups` | Categories, departments, branches, software and device groups | All roles |
| Integration | `POST` | `/integration/tickets` | `ingestTickets` | ITSM pushes tickets (UC10) | ITSM (API key) |
| Integration | `POST` | `/integration/changes` | `ingestChanges` | ITSM pushes changes (UC10) | ITSM (API key) |
| Integration | `POST` | `/integration/logs` | `ingestLogs` | Log source pushes error logs (UC22) | Log source (API key) |

## Screen-to-API mapping

| Screen | API operations |
|---|---|
| Login | `login`, `logout` |
| Dashboard | `getDashboard` |
| Anomalies (list and detail) | `listAnomalies`, `getAnomaly`, `listSuspects`, `listAnomalyTickets`, `listAnomalyLogs`, `getAnomalyTimeline`, `submitSuspectFeedback`, `getSuggestedResolution`, `confirmSuggestedResolution` |
| Changes | `listChanges`, `getChange`, `createChange`, `updateChange`, `updateChangeStatus` |
| Tickets | `listTickets`, `getTicket`, `createTicket` |
| Ticket import | `previewTicketImport`, `createTicketImport`, `listTicketImports`, `getTicketImport` |
| Baseline | `getBaseline`, `recomputeBaseline` |
| Audit | `listAuditLogs` |
| Settings | `getSettings`, `updateSettings` |
| Users | `listUsers`, `getUser`, `createUser`, `updateUser`, `updateUserStatus` |
| Profile | `getProfile`, `updateProfile`, `changePassword` |
| ITSM and log source (no screen) | `ingestTickets`, `ingestChanges`, `ingestLogs` |

`getLookups` supplies choices (categories, departments, branches, software, device groups) to forms and filters; it has no screen of its own.

## Open items

- Field-level review against the data model once it is defined.
- Export of reports and rate limits are not specified in V1.
- Masking rules and the rule that links logs to an anomaly are defined in the algorithm design.
- Token lifetime and refresh behavior are decided in the architecture phase.
