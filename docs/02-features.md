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

- F12.1 Collect evidence: related tickets and time window, scope match, the change's rollback plan, previously confirmed incidents with similar category and scope (from F08 feedback).
- F12.2 Draft the suggestion with an LLM from that evidence only.
- F12.3 Validate: every statement must cite its evidence (ticket IDs, change ID, time window); statements without evidence are removed.
- F12.4 Label each suggestion: **Confirmed** (based on a previously confirmed incident) or **Hypothesis** (needs verification).
- F12.5 Confirm or reject: only IT Manager, Change Engineer, and Administrator can mark a suggestion as confirmed; the outcome feeds F08.

The system only suggests. Rollback or any fix is performed by a person, never automatically. If no evidence supports a suggestion, the screen shows "No supported suggestion".
