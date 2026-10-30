# Acceptance Criteria — CIC V1

> Design status: TARGET V1
>
> Implementation status: NOT STARTED — criteria are written to be turned into API and UI tests

Each criterion is observable through the API ([openapi.yaml](api/openapi.yaml)) or the UI. Authorization is always checked in the backend; hidden UI controls never count as enforcement. Rules referenced as `BR-xxx` are in [Business Rules](requirements/business-rules.md).

## AC-UC01 — Login

- Valid credentials for an active account return `200` with a Bearer token, its expiry (30 minutes), and the user profile without the password hash.
- Unknown e-mail, wrong password, and inactive account all return the same `401` message.
- After 5 failed attempts in 15 minutes for one account, further attempts return `429` until the window passes (NFR-SEC-003).
- Every successful login writes a `LOGIN` audit event.

## AC-UC02 — Logout

- Logout returns `204`; the client discards the token and returns to Login.
- A protected route requested after logout redirects to Login.

## AC-UC03 — View incident dashboard

- All roles receive open anomalies, tickets-versus-baseline points, and the top suspects for the selected time range.
- An invalid range (`from` after `to`) returns `400`.
- Times are returned in UTC and shown in the viewer's time zone (BR-020).

## AC-UC04 — View changes

- All roles can list, filter (type, status, time, department, branch, software), paginate, and open a change.
- A missing change returns `404`.
- Agents see no create or edit controls.

## AC-UC05 — Create change

- Admin, IT Manager, and Change Engineer receive `201`; an Agent receives `403`.
- A change without any scope value, with `endAt` before `startAt`, with a rollback plan marked available but no steps, or with an unknown scope name returns `400` with field errors (BR-003, BR-004).
- Success stores `source = MANUAL`, `createdBy`, and the scope rows, and writes a `CREATE` audit event.

## AC-UC06 — Edit change and update status

- Admin and IT Manager can edit any change; a Change Engineer can edit only changes where they are the implementer, otherwise `403` (BR-002).
- Setting status to `ROLLED_BACK` is accepted and audited as `STATUS_CHANGE`.
- Validation follows AC-UC05.

## AC-UC07 — View tickets

- All roles can list, filter (time, category, department, branch, software, status), paginate, and open a ticket.

## AC-UC08 — Add ticket

- Admin, IT Manager, and Agent receive `201`; a Change Engineer receives `403`.
- Category, department, branch, reported time, and description are required; unknown lookups return `400`.

## AC-UC09 — Import tickets

- Preview reports total rows, valid rows, and row-level errors without storing tickets.
- A file over 10 MB or 5,000 rows is rejected with `400` before parsing completes (BR-006).
- Import is atomic: if any row is invalid, `0` tickets are stored and the batch is `FAILED`; otherwise every row is stored with `source = IMPORT` (BR-005).
- The import history shows file name, status, imported rows, user, and time.

## AC-UC10 — Receive tickets and changes from ITSM

- A missing, wrong, or inactive API key returns `401`.
- A batch over 1,000 items returns `400`.
- Re-sending an item with the same `externalId` from the same client stores it once and counts it as a duplicate (BR-007).
- The response is `202` with accepted, duplicate, and rejected counts.

## AC-UC11 — View baseline

- All roles see mean and deviation per category × weekday × hour from the active baseline run, and actual counts for the selected range.
- When no successful run exists, the screen states that the baseline is not computed yet.

## AC-UC12 — Recompute baseline

- Admin and IT Manager receive `202` with a job id; other roles receive `403`.
- When the job succeeds, the new run becomes active; if it fails, the previous run stays active (BR-009).

## AC-UC13 — Detect anomalies and rank suspects (system)

- A group whose ticket count in a bucket exceeds `mean + threshold × std_dev` of the active baseline produces an anomaly with its tickets and related logs (BR-010).
- Every change whose start time is inside the tracing window before the anomaly, and whose status is not `SCHEDULED`, is scored (BR-011).
- Each suspect has a score 0–100, a level, and an explanation for each of the five factors; ranks are 1..n by descending score (BR-012).
- Re-ranking replaces the previous suspects of the anomaly in one transaction.
- Suspects are stored before any LLM call; an LLM outage never removes or changes suspects (BR-016).

## AC-UC14 — View anomaly and suspects

- All roles see the affected group, time range, actual versus expected count, severity, and suspects ordered by rank with score, level, and factor explanations.
- An anomaly without suspects shows "No suspect found" and suggests widening the tracing window.

## AC-UC15 — Give suspect feedback

- All roles can submit `CORRECT_CAUSE` or `UNRELATED` with an optional note (max 1,000 characters).
- Submitting again replaces the user's previous verdict (one per user per suspect) and writes a `FEEDBACK` audit event.

## AC-UC16 — View audit log

- Admin and IT Manager can filter by time, user, and action; other roles receive `403`.
- No audit entry contains a password, hash, token, or API key (NFR-SEC-005).

## AC-UC17 — Configure system

- Only Admin can read and update settings; others receive `403`.
- Values outside the allowed ranges return `400` (BR-019).
- A change takes effect on the next detection run without a redeploy and writes a `CONFIG_CHANGE` audit event.

## AC-UC18 — Manage users

- Only Admin can list, create, edit, enable, and disable users.
- A duplicate e-mail (case-insensitive) returns `409`.
- A disabled user cannot log in (AC-UC01).

## AC-UC19 — Manage profile and password

- Every user can update name, phone, and avatar but not their role.
- Changing the password requires the current password; a new password shorter than 8 characters returns `400`.

## AC-UC20 — View suggested resolution

- All roles can read the current suggestion of a suspect.
- Every cause statement shows at least one evidence item; every step shows its basis, **Standard** (with its source) or **Flexible** (LLM knowledge) (BR-013, BR-014).
- The suggestion shows its label; a suggestion containing a Flexible step is never labeled `CONFIRMED` (BR-015).
- When the status is `PENDING`, `FAILED`, or `NO_SUPPORT`, the API returns `404` and the screen shows "No supported suggestion".

## AC-UC21 — Confirm or reject suggested resolution

- Admin, IT Manager, and Change Engineer can confirm or reject a `READY` suggestion with an optional note; an Agent receives `403` (BR-017).
- Confirming sets `decision`, `decidedBy`, and `decidedAt`; the label becomes `CONFIRMED` only if every statement is Standard.
- Every decision writes a `SUGGESTION_DECISION` audit event.
- A confirmed suggestion is offered as `PAST_INCIDENT` evidence for later anomalies with the same category and scope.

## AC-UC22 — Receive error logs

- A missing, wrong, or inactive log-source key returns `401`; a batch over 1,000 logs returns `400`.
- Sensitive values (user names, e-mail addresses, IP addresses, file paths) are masked before the log is stored (BR-008).
- Duplicates by `externalId` are stored once.
- The response is `202` with accepted, duplicate, and rejected counts.

## AC-UC23 — View related error logs

- All roles see the logs linked to an anomaly, grouped by signature with count, level, first and last seen time, and a masked sample message.
- An anomaly without linked logs shows "No related logs".
- Logs older than the retention period no longer appear; evidence that cited them keeps its masked snapshot (BR-018).
