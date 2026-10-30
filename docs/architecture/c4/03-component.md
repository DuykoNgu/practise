# C3 — Component

> **Purpose:** show how the two application containers, Backend API and Analysis Worker, are decomposed.

## C3.1 Backend API

```mermaid
flowchart TB
    web["Web Frontend<br/><i>[Container]</i>"]
    ext["ITSM System / Log Source<br/><i>[External Systems]</i>"]
    db[("PostgreSQL<br/><i>[Container]</i>")]
    files[("File Storage<br/><i>[Container]</i>")]

    subgraph api["Backend API [Container]"]
        direction TB
        http["HTTP API<br/><i>[Component]</i><br/>REST endpoints, request validation,<br/>ProblemDetails error mapping"]
        identity["Identity & Access<br/><i>[Component]</i><br/>Login, JWT, RBAC,<br/>own-record policy"]
        intake["Integration Intake<br/><i>[Component]</i><br/>API key check, idempotent intake<br/>of tickets, changes, logs"]
        masking["Log Masking<br/><i>[Component]</i><br/>Removes user names, e-mails,<br/>IPs, paths from log messages"]
        change["Change Management<br/><i>[Component]</i><br/>Change CRUD, status,<br/>scope, rollback plan"]
        ticket["Ticket Management<br/><i>[Component]</i><br/>Ticket CRUD, CSV/Excel preview<br/>and atomic import"]
        incident["Incident Query<br/><i>[Component]</i><br/>Dashboard, anomalies, suspects,<br/>related tickets and logs, timeline"]
        suggestion["Suggestion & Feedback<br/><i>[Component]</i><br/>Read suggestions, confirm or reject,<br/>suspect feedback"]
        admin["Settings, Users & Profile<br/><i>[Component]</i><br/>Configuration, lookups,<br/>user admin, profile"]
        jobs["Job Requests<br/><i>[Component]</i><br/>Queues baseline recompute<br/>and analysis jobs"]
        audit["Audit Log<br/><i>[Component]</i><br/>Records business actions"]
        persistence["Persistence<br/><i>[Component]</i><br/>Repositories, transactions,<br/>SQL mapping"]
    end

    web --> http
    ext --> http
    http --> identity
    http --> intake
    http --> change
    http --> ticket
    http --> incident
    http --> suggestion
    http --> admin
    http --> jobs
    intake --> masking
    intake --> persistence
    change --> persistence
    ticket --> persistence
    ticket --> files
    incident --> persistence
    suggestion --> persistence
    admin --> persistence
    jobs --> persistence
    change -.->|"events"| audit
    ticket -.->|"import results"| audit
    suggestion -.->|"confirmations"| audit
    admin -.->|"config and user changes"| audit
    audit --> persistence
    persistence --> db

    style http fill:#1168bd,color:#fff
    style identity fill:#1168bd,color:#fff
    style intake fill:#1168bd,color:#fff
    style masking fill:#0b4f9e,color:#fff
    style change fill:#1168bd,color:#fff
    style ticket fill:#1168bd,color:#fff
    style incident fill:#1168bd,color:#fff
    style suggestion fill:#0b4f9e,color:#fff
    style admin fill:#1168bd,color:#fff
    style jobs fill:#1168bd,color:#fff
    style audit fill:#1168bd,color:#fff
    style persistence fill:#1168bd,color:#fff
```

## C3.2 Analysis Worker

```mermaid
flowchart TB
    db[("PostgreSQL<br/><i>[Container]</i>")]
    llm["LLM Provider<br/><i>[External System]</i>"]

    subgraph worker["Analysis Worker [Container]"]
        direction TB
        runner["Job Runner<br/><i>[Component]</i><br/>Schedule and job-table polling,<br/>retries, one job per lock"]
        baseline["Baseline Calculator<br/><i>[Component]</i><br/>Mean and deviation per<br/>hour × weekday × category"]
        detector["Anomaly Detector<br/><i>[Component]</i><br/>Compares actual volume with baseline<br/>per group, creates anomalies"]
        classifier["Log Classifier & Linker<br/><i>[Component]</i><br/>Signature, category, links logs<br/>to anomalies by time and scope"]
        ranker["Suspect Ranker<br/><i>[Component]</i><br/>Rule-based score 0–100<br/>with per-factor explanation"]
        evidence["Evidence Collector<br/><i>[Component]</i><br/>Logs, tickets, change, rollback plan,<br/>confirmed past incidents"]
        generator["Suggestion Generator<br/><i>[Component]</i><br/>Builds the prompt, calls the LLM,<br/>parses cause and resolution"]
        validator["Evidence Validator<br/><i>[Component]</i><br/>Drops uncited cause statements,<br/>sets basis and label"]
        persistence["Persistence<br/><i>[Component]</i><br/>Repositories and SQL mapping"]
    end

    runner --> baseline
    runner --> detector
    runner --> classifier
    detector --> ranker
    classifier --> ranker
    ranker --> evidence
    evidence --> generator
    generator --> llm
    generator --> validator
    baseline --> persistence
    detector --> persistence
    classifier --> persistence
    ranker --> persistence
    evidence --> persistence
    validator --> persistence
    runner --> persistence
    persistence --> db

    style runner fill:#1168bd,color:#fff
    style baseline fill:#1168bd,color:#fff
    style detector fill:#1168bd,color:#fff
    style classifier fill:#1168bd,color:#fff
    style ranker fill:#0b4f9e,color:#fff
    style evidence fill:#1168bd,color:#fff
    style generator fill:#0b4f9e,color:#fff
    style validator fill:#0b4f9e,color:#fff
    style persistence fill:#1168bd,color:#fff
```

## Component catalog

| Container | Component | Responsibility | Features / use cases |
|---|---|---|---|
| Backend API | HTTP API | Endpoints from `docs/api/openapi.yaml`, validation, error mapping | All |
| Backend API | Identity & Access | Login, JWT, RBAC, own-record rule for changes | F01 · UC01, UC02 |
| Backend API | Integration Intake | API-key auth, idempotent intake by `externalId` | F03, F13 · UC10, UC22 |
| Backend API | Log Masking | Masks sensitive data before a log is stored | F13.2 |
| Backend API | Change Management | Change CRUD and status, scope, rollback plan | F02 · UC04–UC06 |
| Backend API | Ticket Management | Ticket CRUD, import preview and atomic import | F03 · UC07–UC09 |
| Backend API | Incident Query | Dashboard, anomalies, suspects, related tickets and logs, timeline | F07 · UC03, UC14, UC23 |
| Backend API | Suggestion & Feedback | Read suggestions, confirm or reject, suspect feedback | F08, F12 · UC15, UC20, UC21 |
| Backend API | Settings, Users & Profile | Configuration, lookups, users, profile | F09, F11 · UC17–UC19 |
| Backend API | Job Requests | Writes recompute and analysis jobs to the job table | F04 · UC12 |
| Backend API | Audit Log | Records business actions | F10 · UC16 |
| Analysis Worker | Job Runner | Runs scheduled and requested jobs, locking, retries | F04, F05 |
| Analysis Worker | Baseline Calculator | Computes baselines, excludes incident periods | F04 · UC11, UC12 |
| Analysis Worker | Anomaly Detector | Creates anomalies when volume exceeds the threshold | F05 · UC13 |
| Analysis Worker | Log Classifier & Linker | Signature, category, links logs to anomalies | F13.3, F13.4 |
| Analysis Worker | Suspect Ranker | Rule-based score and factor explanations | F06 · UC13 |
| Analysis Worker | Evidence Collector | Gathers evidence for each suspect | F12.1 |
| Analysis Worker | Suggestion Generator | Calls the LLM with masked evidence | F12.2, F13.5 |
| Analysis Worker | Evidence Validator | Removes uncited cause statements; sets `basis` and `label` | F12.3–F12.5 |

## Dependency Flow

- **Backend API:** HTTP API → feature components → Persistence → PostgreSQL. Feature components send events to Audit Log; they do not call each other except through Persistence.
- **Analysis Worker:** Job Runner → Baseline / Anomaly Detector / Log Classifier → Suspect Ranker → Evidence Collector → Suggestion Generator → Evidence Validator → Persistence.
- The Suspect Ranker finishes before the Suggestion Generator runs, so the score never depends on the LLM.
- If the LLM call fails, suspects and scores are still stored; the suggestion is retried later and the screen shows "No supported suggestion" until then.
