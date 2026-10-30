# Feature Catalog

> Design status: TARGET V1

UI product: **CIC**. Target V1 behavior is defined by the use cases, user stories, and later architecture documents.

| ID | Name | V1 | Priority |
|---|---|---|---|
| F01 | Authentication and authorization | Yes | Must |
| F02 | Change Management | Yes | Must |
| F03 | Ticket Management | Yes | Must |
| F04 | Baseline | Yes | Must |
| F05 | Anomaly Detection | Yes | Must |
| F06 | Correlation and Suspect Ranking | Yes | Must |
| F07 | Dashboard and Incident Detail | Yes | Must |
| F08 | Suspect Feedback | Yes | Should |
| F09 | System Configuration | Yes | Should |
| F10 | Audit Log | Yes | Should |
| F11 | Users and Profile | Yes | Must |
| F12 | Suggested Resolution | Yes | Should |
| F13 | Error Log Analysis | Yes | Should |

## F01 Authentication and authorization

- F01.1 Login (email, password)
- F01.2 Logout
- F01.3 Role-based access control enforced by the backend
- F01.4 Route guard and role guard (403 screen)

## F02 Change Management

List with filters (type, time, scope, status), add/edit using a **modal**, view details using a **modal**, status updates (including marking a change as rolled back), rollback plan.

Fields: type, title, description, start/end time, scope (device group, department, software, branch), implementer, approver, rollback plan, status. Changes can be entered manually, imported, or synchronized through the API.

## F03 Ticket Management

List with filters (time, category, department, branch, software) and detail view. Sources: manual entry, CSV/Excel import (preview and validation), API from an ITSM system.

## F04 Baseline

Compute and store average tickets per hour slot / weekday / category; chart baseline versus actual; recompute on schedule or on demand; exclude incident periods from the baseline data.

## F05 Anomaly Detection

Periodically compare actual ticket volume with the baseline per group (category, department, branch, software). When a threshold is exceeded, create an **anomaly**: affected group, time range, actual versus expected tickets, and severity.

## F06 Correlation and Suspect Ranking

For each anomaly, find changes inside the tracing window before the spike started and compute a suspicion score from:

| Factor | Meaning |
|---|---|
| Time proximity | The closer a change is to the spike, the more suspicious it is |
| Scope match | The ticket's department / branch / software / device group falls inside the change scope |
| Category and keyword match | Ticket category or keywords relate to the change type or target |
| Anomaly magnitude | How many times the ticket volume exceeds baseline |
| Change risk | Change type and whether a rollback plan exists |

Result: a suspect list ordered by score, with an **explanation per factor** so users can verify it. The detailed formula is defined in the algorithm design phase.

## F07 Dashboard and Incident Detail

Overview: open anomalies, tickets versus baseline chart, top suspects. Anomaly detail: ranked suspects, related tickets, timeline (changes and tickets), rollback plan, implementer, and the suggested resolution of each suspect.

## F08 Suspect Feedback

Users confirm whether a suspect was the **actual cause** or **unrelated**, with an optional note. The data is used to measure accuracy and tune weights.

## F09 System Configuration

Anomaly thresholds, tracing window (default 48 hours), factor weights, processing schedule, categories, and department / branch / software mappings.

## F10 Audit Log

Records login, change create/update, ticket import, configuration changes, and suspect feedback. Columns: user, action, object, details, time.

## F11 Users and Profile

Administrators create, edit, and disable users and assign roles. Users update their profile and change their password.

## F12 Suggested Resolution

For each suspect change, the system proposes a likely cause and a resolution. The suspicion score is still computed by rules and statistics (F06); the LLM only writes the explanation and the resolution.

- F12.1 Collect evidence: related error logs (F13), related tickets and time window, scope match, the change's rollback plan, previously confirmed incidents with similar category and scope (from F08 feedback).
- F12.2 Draft the suggestion with an LLM from that evidence.
- F12.3 Validate the cause: every statement about the cause must cite its evidence (log IDs, ticket IDs, change ID, time window); statements without evidence are removed.
- F12.4 Give the resolution in two kinds, each labeled with its **basis**:
  - **Standard**: taken from the rollback plan, previously confirmed incidents, or internal guidance. It cites its source.
  - **Flexible**: based on the LLM's general knowledge. It may have no source, so it is always labeled **Hypothesis**.
- F12.5 Label each suggestion: **Confirmed** (all statements are standard and a person confirmed it) or **Hypothesis** (anything else).
- F12.6 Confirm or reject: only IT Manager, Change Engineer, and Administrator can mark a suggestion as confirmed; the outcome feeds F08.

The system only suggests. Rollback or any fix is performed by a person, never automatically. If no evidence supports the cause, the screen shows "No supported suggestion".

## F13 Error Log Analysis

Error logs give the AI technical evidence behind a spike of tickets.

- F13.1 Receive error logs through the API (push by a log source) and normalize them: time, source, device group, department, branch, level, code, message.
- F13.2 Mask sensitive data (user names, e-mail addresses, IP addresses, file paths) before storage for analysis and before any call to the LLM.
- F13.3 Extract and classify: compute a signature, group identical errors, assign a category.
- F13.4 Link logs to anomalies and suspects when they fall inside the tracing window and match the scope (department, branch, software, device group).
- F13.5 Analyze: the LLM reads the linked logs, the tickets, and the suspect change to explain the likely cause (feeds F12).
- F13.6 Show the related error logs on the anomaly detail screen.
- F13.7 Keep logs for a configurable retention period, then delete them.
