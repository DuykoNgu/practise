# C1 — System Context

> **Purpose:** show who uses CIC, which external systems it talks to, and what it is responsible for, without implementation technology.

```mermaid
flowchart LR
    admin(["Administrator"])
    manager(["IT Manager"])
    engineer(["Change Engineer"])
    agent(["Service Desk Agent"])

    subgraph boundary[" "]
        cic["CIC — Change-Incident Correlation<br/><i>[Software System]</i><br/>Detects abnormal ticket spikes, ranks recent<br/>changes as suspects, analyzes related error logs,<br/>and suggests resolutions with evidence"]
    end

    itsm["ITSM System<br/><i>[External Software System]</i><br/>Source of tickets and change records"]
    logsrc["Log Source<br/><i>[External Software System]</i><br/>Applications or log shippers<br/>that push error logs"]
    llm["LLM Provider<br/><i>[External Software System]</i><br/>Generates explanations and<br/>suggested resolutions"]

    admin -- "manages users and configuration" --> cic
    manager -- "reviews suspects, decides on rollback,<br/>confirms resolutions" --> cic
    engineer -- "records changes and rollback plans,<br/>confirms resolutions" --> cic
    agent -- "records and imports tickets,<br/>reviews anomalies and suspects" --> cic
    itsm -- "pushes tickets and changes<br/>[REST / API key]" --> cic
    logsrc -- "pushes error logs<br/>[REST / API key]" --> cic
    cic -- "sends masked evidence,<br/>receives drafted text [HTTPS]" --> llm

    style cic fill:#1168bd,color:#fff
    style itsm fill:#999,color:#fff
    style logsrc fill:#999,color:#fff
    style llm fill:#999,color:#fff
```

## System Boundary

CIC is responsible for login and authorization, change and ticket records, ticket import, error-log intake, baselines, anomaly detection, suspect ranking, AI analysis and suggested resolutions, feedback, audit logs, configuration, user management, and personal profiles.

Outside the boundary:

- **ITSM System** keeps owning tickets and changes; CIC only receives copies.
- **Log Source** pushes error logs; CIC does not collect logs from servers.
- **LLM Provider** only writes text from the masked evidence CIC sends; it never computes the suspicion score and never receives unmasked log data.
- CIC never executes a rollback or fix on real infrastructure.

## People and External Systems

| Element | Type | Interaction |
|---|---|---|
| Administrator | Person | Full access, users, configuration |
| IT Manager | Person | Reviews suspects and evidence, decides on rollback, confirms or rejects resolutions, reads the audit log |
| Change Engineer | Person | Records changes and rollback plans (own records), confirms or rejects resolutions |
| Service Desk Agent | Person | Records and imports tickets, reviews anomalies, suspects, logs, and suggestions |
| ITSM System | External system | Pushes tickets and changes through the integration API |
| Log Source | External system | Pushes error logs through the integration API |
| LLM Provider | External system | Receives masked evidence and returns drafted explanations and resolutions |

**Next:** zoom into the Software System → [C2 — Container](02-container.md).

**Sources of truth:** `docs/01-scope.md`, `docs/03-use-cases.md`, `docs/api/openapi.yaml`.
