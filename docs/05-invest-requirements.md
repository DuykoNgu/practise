# INVEST Requirements — CIC V1

> Design status: TARGET V1

Each requirement is small enough to implement and test independently. Cross-cutting authentication, authorization, validation, auditing, and error handling are acceptance constraints, not hidden features.

## INVEST checklist

| Principle | Application in this backlog |
|---|---|
| Independent | Each story produces a demonstrable outcome and identifies only unavoidable prerequisites. |
| Negotiable | UI layout and implementation details may change while the stated outcome and permissions remain fixed. |
| Valuable | Every story names the user benefit. |
| Estimable | Inputs, outputs, roles, and exceptional outcomes are explicit. |
| Small | Each story targets one capability and can be split into API, application, persistence, and UI tasks. |
| Testable | Every story has an observable outcome; detailed acceptance criteria are written in a later phase. |

## Product backlog

| ID | User story | Value | Dependencies | Use case |
|---|---|---|---|---|
| US01 | As an active user, I want to log in so that I can securely access my permitted workspace. | Protected access | Seeded user account | UC01 |
| US02 | As an authenticated user, I want to log out so that my session ends safely. | Session safety | US01 | UC02 |
| US03 | As any role, I want a dashboard of open anomalies so that I immediately see an abnormal ticket spike. | Fast awareness | US01, US12 | UC03 |
| US04 | As a Change Engineer, IT Manager, or Administrator, I want to create a change record with scope and rollback plan so that my change can be traced. | Traceable changes | US01 | UC05 |
| US05 | As an authorized editor, I want to update a change and its status (including rolled back) so that data reflects reality; Change Engineers may update only their own records. | Accurate change data | US06 | UC06 |
| US06 | As any role, I want to filter and inspect changes so that I can look up recent changes. | Change visibility | US01 | UC04 |
| US07 | As an Agent, IT Manager, or Administrator, I want to add a ticket manually so that user reports are recorded. | Complete ticket data | US01, categories | UC08 |
| US08 | As an Agent, IT Manager, or Administrator, I want to preview and import a CSV/Excel file so that bulk tickets are accepted only when valid. | Safe bulk entry | US01, categories | UC09 |
| US09 | As any role, I want to filter and inspect tickets so that I can see tickets of the same group. | Ticket visibility | US01 | UC07 |
| US10 | As any role, I want to view the baseline against actual volume so that I understand what normal looks like. | Context for anomalies | US09 | UC11 |
| US11 | As an IT Manager or Administrator, I want to recompute the baseline so that it reflects new data. | Fresh baseline | US10 | UC12 |
| US12 | As any role, I want to see an anomaly with a ranked, explained list of suspect changes so that I can quickly link tickets to a change. | Faster diagnosis | US06, US09, US10 | UC13, UC14 |
| US13 | As an IT Manager, I want to see the rollback plan and implementer of a suspect so that I can decide on rollback in time. | Faster recovery | US12 | UC14 |
| US14 | As any role, I want to mark a suspect as correct cause or unrelated so that accuracy can be measured and improved. | Learning loop | US12 | UC15 |
| US15 | As an Administrator or IT Manager, I want to inspect audit events so that important actions are traceable. | Accountability | US01 | UC16 |
| US16 | As an Administrator, I want to configure thresholds, tracing window, and weights so that detection fits my organization. | Tunable detection | US01 | UC17 |
| US17 | As an Administrator, I want to create, edit, enable, and disable users so that access remains controlled. | Access administration | US01 | UC18 |
| US18 | As an authenticated user, I want to maintain my profile and password without changing my role so that my account stays current and secure. | Self-service | US01 | UC19 |
| US19 | As an ITSM system, I want to push tickets and changes through the API so that data synchronizes automatically. | Automatic ingestion | US01 | UC10 |
| US20 | As any role, I want to read a suggested cause and resolution for each suspect, with the evidence it cites, so that I know what to do next and can verify it. | Faster resolution | US12, US14 | UC20 |
| US21 | As an IT Manager, Change Engineer, or Administrator, I want to confirm or reject a suggested resolution so that only verified resolutions are reused. | Trusted knowledge | US20 | UC21 |

## Per-story INVEST review

`PASS` means the current design provides enough information for planning. `PARTIAL` means a dependency is still undefined. It does not claim that implementation or tests exist.

| Story | I | N | V | E | S | T | Notes |
|---|---|---|---|---|---|---|---|
| US01 | PASS | PASS | PASS | PASS | PASS | PASS | Authentication mechanism is defined in the architecture phase. |
| US02 | PASS | PASS | PASS | PASS | PASS | PASS | Session end behavior is defined with authentication. |
| US03 | PASS | PASS | PASS | PASS | PASS | PASS | Depends on anomaly output (US12). |
| US04 | PASS | PASS | PASS | PASS | PASS | PASS | Change fields are listed in the scope. |
| US05 | PASS | PASS | PASS | PASS | PASS | PASS | Own-record rule is explicit. |
| US06 | PASS | PASS | PASS | PASS | PASS | PASS | Read/filter/paging outcome is independently testable. |
| US07 | PASS | PASS | PASS | PASS | PASS | PASS | Ticket fields are listed in the scope. |
| US08 | PASS | PASS | PASS | PARTIAL | PASS | PASS | File size and row limits are to be defined. |
| US09 | PASS | PASS | PASS | PASS | PASS | PASS | Read/filter/paging outcome is independently testable. |
| US10 | PASS | PASS | PASS | PARTIAL | PASS | PASS | Baseline window and outlier exclusion are defaults to confirm. |
| US11 | PASS | PASS | PASS | PASS | PASS | PASS | Recompute is on demand and scheduled. |
| US12 | PARTIAL | PASS | PASS | PARTIAL | PARTIAL | PASS | Scoring formula and thresholds are pending the algorithm design; may be split into detection and ranking stories. |
| US13 | PASS | PASS | PASS | PASS | PASS | PASS | Read-only view of existing change data. |
| US14 | PASS | PASS | PASS | PASS | PASS | PASS | Feedback values are fixed: correct cause / unrelated. |
| US15 | PASS | PASS | PASS | PASS | PASS | PASS | Read-only audit access and filters are defined. |
| US16 | PASS | PASS | PASS | PARTIAL | PASS | PASS | Valid ranges for configuration values are to be defined. |
| US17 | PASS | PASS | PASS | PASS | PASS | PASS | Role set is fixed in the use-case document. |
| US18 | PASS | PASS | PASS | PASS | PASS | PASS | Role cannot be changed through the profile. |
| US19 | PASS | PASS | PASS | PARTIAL | PASS | PASS | Payload format and authentication for the ITSM are to be defined. |
| US20 | PASS | PASS | PASS | PARTIAL | PARTIAL | PASS | Evidence sources and the LLM prompt/validation rules are pending design; may be split into evidence collection and suggestion drafting. |
| US21 | PASS | PASS | PASS | PASS | PASS | PASS | Reuses the feedback mechanism of US14; permitted roles are fixed. |
