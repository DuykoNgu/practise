# Change-Incident Correlation (CIC)

Change-Incident Correlation helps IT teams answer one question when tickets suddenly spike: **"Which recent change is most likely the cause?"** It brings together change records, tickets, and historical baselines, detects abnormal ticket volume, and ranks the recent changes as "suspects" with an explainable score, so the service desk no longer depends on a few experienced people to connect the dots.

> **Real example:** On Tuesday at 22:00, IT applies a Windows patch to the Accounting department. On Wednesday morning, 14 "cannot print" tickets arrive. CIC detects the spike against the baseline, links it to the patch, and puts that change at the top of the suspect list together with its rollback plan and the engineer who applied it.

## 1. Requirements — INVEST, Use Cases, and Acceptance Criteria

Requirements define what CIC must do, who uses it, the value delivered, and the observable conditions of success. User stories are reviewed with INVEST and mapped to use cases.

### 1.1 Product mind map

![CIC mind map](docs/mindmap.png)

### 1.2 INVEST requirements

The V1 backlog includes 23 user stories. These stories cover login, change and ticket management, ticket import, baseline, anomaly and suspect review, feedback, audit log, configuration, user management, personal profile, ITSM and log ingestion, error-log review, and AI-suggested resolutions.
Before a user story is ready for development, it is checked using the INVEST criteria.

| Criterion       | Meaning in CIC                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Independent** | Each story should provide a clear feature and depend on other stories only when necessary.                          |
| **Negotiable**  | The UI and technical implementation can change as long as the main goal and permission rules stay the same.         |
| **Valuable**    | Each story should provide value to the user or the business.                                                        |
| **Estimable**   | Roles, inputs, outputs, dependencies, and important failure outcomes are documented.                                |
| **Small**       | Each story covers one primary capability and can be divided into API, application, persistence, UI, and test tasks. |
| **Testable**    | Every story maps to observable outcomes and expected authorization, validation, and error behavior.                 |

```text
US01–US02   Authentication and session
US03        Incident dashboard
US04–US06   Change management
US07–US09   Ticket management and import
US10–US11   Baseline
US12–US14   Anomaly, ranked suspects, and feedback
US20–US21   Suggested resolution and its confirmation
US22–US23   Error logs: ingestion and review
US15        Audit log
US16        System configuration
US17–US18   User management and personal profile
US19        ITSM API ingestion
```

The complete story-level review is maintained in [INVEST Requirements](docs/05-invest-requirements.md).

### 1.3 Use cases

```mermaid
flowchart TB
    subgraph roles["Actors"]
        direction LR
        admin(["Administrator"])
        manager(["IT Manager"])
        engineer(["Change Engineer"])
        agent(["Service Desk Agent"])
    end

    subgraph system["CIC — System Boundary"]
        direction LR
        adminCases["<b>Administrator</b><br/><br/>UC01 Login · UC02 Logout<br/>UC03 View Dashboard · UC19 Manage Profile<br/>UC04 View Changes · UC05–06 Add/Edit Changes<br/>UC07 View Tickets · UC08 Add Ticket · UC09 Import Tickets<br/>UC11 View Baseline · UC12 Recompute Baseline<br/>UC14 View Anomaly and Suspects<br/>UC15 Give Suspect Feedback<br/>UC23 View Related Error Logs<br/>UC20 View Suggested Resolution<br/>UC21 Confirm Suggested Resolution<br/>UC16 View Audit Log · UC17 Configure System<br/>UC18 Manage Users"]
        managerCases["<b>IT Manager</b><br/><br/>UC01 Login · UC02 Logout<br/>UC03 View Dashboard · UC19 Manage Profile<br/>UC04 View Changes · UC05–06 Add/Edit Changes<br/>UC07 View Tickets · UC08 Add Ticket · UC09 Import Tickets<br/>UC11 View Baseline · UC12 Recompute Baseline<br/>UC14 View Anomaly and Suspects<br/>UC15 Give Suspect Feedback<br/>UC23 View Related Error Logs<br/>UC20 View Suggested Resolution<br/>UC21 Confirm Suggested Resolution<br/>UC16 View Audit Log"]
        engineerCases["<b>Change Engineer</b><br/><br/>UC01 Login · UC02 Logout<br/>UC03 View Dashboard · UC19 Manage Profile<br/>UC04 View Changes · UC05–06 Add/Edit Own Changes<br/>UC07 View Tickets · UC11 View Baseline<br/>UC14 View Anomaly and Suspects<br/>UC15 Give Suspect Feedback<br/>UC23 View Related Error Logs<br/>UC20 View Suggested Resolution<br/>UC21 Confirm Suggested Resolution"]
        agentCases["<b>Service Desk Agent</b><br/><br/>UC01 Login · UC02 Logout<br/>UC03 View Dashboard · UC19 Manage Profile<br/>UC04 View Changes<br/>UC07 View Tickets · UC08 Add Ticket · UC09 Import Tickets<br/>UC11 View Baseline<br/>UC14 View Anomaly and Suspects<br/>UC15 Give Suspect Feedback<br/>UC23 View Related Error Logs<br/>UC20 View Suggested Resolution"]
    end

    admin --> adminCases
    manager --> managerCases
    engineer --> engineerCases
    agent --> agentCases

    classDef actor fill:#666,color:#fff,stroke:#333
    classDef primary fill:#1168bd,color:#fff,stroke:#0b4f9e
    classDef standard fill:#3a7bd5,color:#fff,stroke:#245fa8
    class admin,manager,engineer,agent actor
    class adminCases,managerCases primary
    class engineerCases,agentCases standard
    style roles fill:#fff,stroke:#bbb,stroke-dasharray:5 5
    style system fill:#f8fbff,stroke:#1168bd,stroke-dasharray:5 5
```

Three system actors are not shown: the **ITSM system** (UC10, pushes tickets and changes through the API), the **log source** (UC22, pushes error logs through the API), and the **background processor** (UC13, detects anomalies, ranks suspects, analyzes related logs, and drafts suggested resolutions).

For detailed actors, permissions, and business flows, see [Actors, roles, and use cases](docs/03-use-cases.md).

### 1.4 Roles and permissions

| Capability                       | Admin | IT Manager | Change Engineer   | Agent     |
| -------------------------------- | ----- | ---------- | ----------------- | --------- |
| View dashboard, anomalies, suspects | Yes | Yes        | Yes               | Yes       |
| View changes and tickets         | Yes   | Yes        | Yes               | Yes       |
| Create changes                   | Yes   | Yes        | Yes               | No        |
| Edit changes                     | Yes   | Yes        | Own records only  | No        |
| Create / import tickets          | Yes   | Yes        | No                | Yes       |
| View baseline                    | Yes   | Yes        | Yes               | Yes       |
| Recompute baseline               | Yes   | Yes        | No                | No        |
| Give suspect feedback            | Yes   | Yes        | Yes               | Yes       |
| View related error logs          | Yes   | Yes        | Yes               | Yes       |
| View suggested resolution        | Yes   | Yes        | Yes               | Yes       |
| Confirm / reject suggested resolution | Yes | Yes     | Yes               | No        |
| Audit log                        | Yes   | Yes        | No                | No        |
| System configuration             | Yes   | No         | No                | No        |
| User management                  | Yes   | No         | No                | No        |

The backend must enforce RBAC and the own-record policy; hiding frontend controls serves UI/UX only.

## 2. Information Architecture, Screen Hierarchy, and UI/UX

The information architecture organizes the authenticated workspace by business capability. Screen permissions and navigation follow the role matrix, while loading, empty, validation, error, saving, and success states are defined consistently.

### 2.1 Information architecture

An information architecture is more than a list of pages. CIC defines it through four systems — organization, labeling, navigation, and hierarchy — following the classic IA model (Rosenfeld & Morville).

**Organization scheme.** Pages are grouped by the *job the user is doing*, not by database table: **Monitor** (what is wrong now), **Records** (the data that explains it), **Analysis** (what normal looks like), and **Administration** (who and how the system is configured). Inside a group, items are organized by object (Change, Ticket, Anomaly).

**Site map.** Level 0 is the product, level 1 is a navigation group, level 2 is a page, level 3 is a section or modal inside a page.

```mermaid
flowchart TB
    CIC(["CIC"])
    CIC --> Public["Public"]
    CIC --> Shell["Authenticated workspace<br/>(sidebar + topbar)"]
    CIC --> Sys["System page"]
    Public --> Login["Login"]
    Sys --> Forbidden["403 Forbidden"]

    Shell --> Monitor["MONITOR"]
    Shell --> Records["RECORDS"]
    Shell --> Analysis["ANALYSIS"]
    Shell --> Admin["ADMINISTRATION"]
    Shell --> Utility["UTILITY (topbar)"]

    Monitor --> Dash["Dashboard"]
    Dash --> D1["Open anomalies"]
    Dash --> D2["Tickets versus baseline"]
    Dash --> D3["Top suspects"]
    Monitor --> Anom["Anomalies"]
    Anom --> A1["Anomaly list"]
    Anom --> A2["Anomaly detail"]
    A2 --> A3["Ranked suspects<br/>score + explanation"]
    A2 --> A4["Related tickets"]
    A2 --> A5["Timeline"]
    A2 --> A8["Related error logs"]
    A2 --> A6["Suspect feedback"]
    A2 --> A7["Suggested resolution<br/>standard + hypothesis"]

    Records --> Chg["Changes"]
    Chg --> C1["Change list"]
    Chg --> C2["Add / edit change<br/>(modal)"]
    Chg --> C3["Change detail<br/>(modal)"]
    Records --> Tkt["Tickets"]
    Tkt --> T1["Ticket list"]
    Tkt --> T2["Add ticket<br/>(modal)"]
    Tkt --> T3["Import<br/>preview + history"]

    Analysis --> Base["Baseline"]
    Base --> B1["Baseline versus actual"]
    Base --> B2["Recompute"]

    Admin --> Audit["Audit log"]
    Admin --> Set["Settings"]
    Set --> S1["Thresholds and tracing window"]
    Set --> S2["Ranking weights"]
    Set --> S3["Categories and scope mappings"]
    Admin --> Usr["Users"]
    Usr --> U1["Add / edit user<br/>(modal)"]

    Utility --> Prof["Profile"]
    Prof --> P1["Account"]
    Prof --> P2["Security"]
    Prof --> P3["Roles and permissions"]
    Utility --> U2["Time range and time zone"]
    Utility --> U3["Log out"]

    classDef root fill:#222,color:#fff,stroke:#000
    classDef group fill:#1168bd,color:#fff,stroke:#0b4f9e
    classDef page fill:#dbeafe,color:#111,stroke:#3a7bd5
    classDef leaf fill:#fff,color:#111,stroke:#bbb
    class CIC root
    class Monitor,Records,Analysis,Admin,Utility group
    class Dash,Anom,Chg,Tkt,Base,Audit,Set,Usr,Prof page
    class D1,D2,D3,A1,A2,A3,A4,A5,A6,A7,A8,C1,C2,C3,T1,T2,T3,B1,B2,S1,S2,S3,U1,U2,U3,P1,P2,P3,Login,Forbidden leaf
```

**Navigation model.**

| Layer | Where | Content |
|---|---|---|
| Global | Sidebar | The four groups and their level-2 pages; groups with no permitted page are hidden |
| Utility | Topbar | Profile, time range / time zone, logout |
| Local | Tabs inside a page | Anomaly detail (Suspects · Related tickets · Timeline), Settings, Profile |
| Contextual | Links inside content | Suspect → change detail; change detail → anomalies it is suspected in; ticket → anomaly it belongs to |

**Labeling.** Labels use the user's vocabulary and one term per concept: *Change* (never "modification"), *Ticket*, *Anomaly*, *Suspect*, *Baseline*. A suspect always shows its score as a number plus a High / Medium / Low label.

**Role scope.** Every level-2 page declares which roles can see it (see [page permissions](docs/04-information-architecture.md#page-permissions)). Unauthorized pages are not rendered in the sidebar, and direct access resolves to 403.

### 2.2 Screen hierarchy

Login leads to the authenticated shell. The shell owns navigation to feature pages; change, ticket, and user create/edit interactions use feature-owned modals. The anomaly detail page links to the suspect change detail. Unauthorized navigation resolves to the Forbidden screen.

```mermaid
flowchart TB
    Login["Login"] --> Shell["Authenticated shell"]
    Shell --> Dashboard["Dashboard"]
    Shell --> Anomalies["Anomaly list"]
    Anomalies --> AnomalyDetail["Anomaly detail and ranked suspects"]
    Dashboard --> AnomalyDetail
    Shell --> Changes["Change list"]
    Changes --> ChangeForm["Add or edit change modal"]
    Changes --> ChangeDetail["Change detail modal"]
    AnomalyDetail --> ChangeDetail
    Shell --> Tickets["Ticket list"]
    Tickets --> Import["Ticket import"]
    Shell --> Baseline["Baseline"]
    Shell --> Audit["Audit log"]
    Shell --> Settings["Settings"]
    Shell --> Users["User management"]
    Users --> UserForm["Add or edit user modal"]
    Shell --> Profile["Profile"]
    Shell --> Forbidden["403 Forbidden"]
```

Detailed screen IDs, user flows, screen states, accessibility rules, and use-case mappings are maintained in [Information Architecture](docs/04-information-architecture.md).

### 2.3 Current UI prototype

No UI prototype exists yet. Screens will be designed from the [screen inventory](docs/04-information-architecture.md#3-screen-inventory) in a later phase.

## 3. C4 Architecture

This README presents C1–C3. Responsibilities, architecture rules, and the component catalog are maintained in the architecture documentation directory.

### C1 — System Context

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

### C2 — Container

```mermaid
flowchart TB
    people(["Administrator / IT Manager /<br/>Change Engineer / Service Desk Agent"])
    itsm["ITSM System<br/><i>[External System]</i>"]
    logsrc["Log Source<br/><i>[External System]</i>"]
    llm["LLM Provider<br/><i>[External System]</i>"]

    subgraph platform["CIC [Software System Boundary]"]
        direction TB
        subgraph presentation["Presentation"]
            web["Web Frontend<br/><i>[Container: Next.js 16 + React 19]</i><br/>Dashboard, anomalies, suspects, changes,<br/>tickets, baseline, settings, users"]
        end
        subgraph application["Application"]
            api["Backend API<br/><i>[Container: Python + FastAPI]</i><br/>Authentication, RBAC, CRUD, import,<br/>integration intake, log masking, feedback"]
            worker["Analysis Worker<br/><i>[Container: Python worker process]</i><br/>Baseline, anomaly detection, suspect ranking,<br/>log classification and linking, AI suggestions"]
        end
        subgraph data["Data"]
            db[("PostgreSQL<br/><i>[Container: Database]</i><br/>Changes, tickets, logs, baselines, anomalies,<br/>suspects, suggestions, feedback, jobs, audit")]
            files[("File Storage<br/><i>[Container: Filesystem / object storage]</i><br/>Uploaded import files")]
        end
    end

    people --> web
    web -- "REST / HTTPS / JSON<br/>Bearer JWT" --> api
    itsm -- "REST / HTTPS / JSON<br/>API key" --> api
    logsrc -- "REST / HTTPS / JSON<br/>API key" --> api
    api -- "SQL" --> db
    api -- "store / read files" --> files
    worker -- "SQL: read data, write results,<br/>poll job table" --> db
    worker -- "HTTPS: masked evidence" --> llm

    style web fill:#1168bd,color:#fff
    style api fill:#1168bd,color:#fff
    style worker fill:#1168bd,color:#fff
    style db fill:#1168bd,color:#fff
    style files fill:#1168bd,color:#fff
    style itsm fill:#999,color:#fff
    style logsrc fill:#999,color:#fff
    style llm fill:#999,color:#fff
```

The Backend API and the Analysis Worker communicate through a job table in PostgreSQL, not a message broker. Logs are masked by the Backend API on receipt; only the Analysis Worker calls the LLM Provider, after the suspicion score is computed.

### C3 — Component

#### C3.1 Backend API

```mermaid
flowchart TB
    web["Web Frontend<br/><i>[Container]</i>"]
    ext["ITSM System / Log Source<br/><i>[External Systems]</i>"]
    db[("PostgreSQL<br/><i>[Container]</i>")]
    files[("File Storage<br/><i>[Container]</i>")]

    subgraph api["Backend API [Container]"]
        direction TB
        http["HTTP API<br/><i>[Component]</i><br/>FastAPI routers, Pydantic validation,<br/>problem+json error mapping"]
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

#### C3.2 Analysis Worker

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

Complete documentation: [C4 Architecture](docs/architecture/c4/README.md).

## 4. Database Diagrams and OpenAPI 3.0 Contract

This step defines the persistence contract (PostgreSQL) and the HTTP contract (OpenAPI) between the Web Frontend, external systems, and the backend.

### 4.1 Database diagrams

The PostgreSQL model links the three inputs (changes, tickets, error logs) to detection (baselines, anomalies), ranking (suspects), and AI suggestions with cited evidence. Scope values (department, branch, software, device group, category) are shared lookup tables, so scope matching compares ids rather than free text.

```mermaid
erDiagram
    changes ||--o{ suspects : suspected_in
    anomalies ||--o{ suspects : ranks
    baseline_runs ||--o{ anomalies : compared_with
    baseline_runs ||--o{ baseline_cells : contains
    anomalies ||--o{ anomaly_tickets : contains
    tickets ||--o{ anomaly_tickets : in
    anomalies ||--o{ anomaly_logs : contains
    error_logs ||--o{ anomaly_logs : in
    suspects ||--o{ suspect_factors : explains
    suspects ||--o{ suspect_feedback : receives
    suspects ||--o{ suggestions : has_versions
    suggestions ||--o{ suggestion_statements : states
    suggestion_statements ||--o{ statement_evidence : cites
    app_users ||--o{ changes : implements
    app_users ||--o{ suggestions : decides
    api_clients ||--o{ error_logs : pushes

    changes {
        uuid id PK
        change_type type
        timestamptz start_at
        uuid implementer_id FK
        boolean rollback_available
    }
    tickets {
        uuid id PK
        timestamptz reported_at
        uuid category_id FK
        uuid department_id FK
        uuid branch_id FK
    }
    error_logs {
        uuid id PK
        timestamptz occurred_at
        text message_masked
        char signature
    }
    anomalies {
        uuid id PK
        timestamptz start_at
        integer actual_count
        numeric expected_count
        severity severity
    }
    suspects {
        uuid id PK
        uuid anomaly_id FK
        uuid change_id FK
        smallint rank
        smallint score
    }
    suggestions {
        uuid id PK
        uuid suspect_id FK
        smallint version
        suggestion_label label
        suggestion_decision decision
    }
    suggestion_statements {
        uuid id PK
        statement_kind kind
        statement_basis basis
    }
    statement_evidence {
        uuid id PK
        evidence_type type
        text log_snapshot
    }
```

Key rules enforced by the schema: a cause statement is always evidence-based, each evidence row cites exactly one thing, `CONFIRMED` requires a person's decision, ticket import is atomic, and integration intake is idempotent by `(source_client_id, external_id)`. Error logs keep only the masked message and are deleted after the retention period; evidence keeps a masked snapshot.

See the [detailed database diagram](docs/DATABASE.md), [data model](docs/06-data-model.md), and [PostgreSQL schema](src/database/cic.sql).

### 4.2 OpenAPI 3.0 API documentation

The REST contract is defined with OpenAPI 3.0 and derived from the use cases and screens. It covers authentication, dashboard, anomalies and ranked suspects, related error logs, suggested resolutions, changes, tickets and import, baseline, audit log, settings, users, profile, and ITSM and log ingestion.

- Contract: [`docs/api/openapi.yaml`](docs/api/openapi.yaml)
- Conventions, role per operation, and screen-to-API mapping: [API documentation](docs/api/README.md)

## 5. Frontend and Backend Folder Structures

The frontend uses **Next.js 16 + React 19 + TypeScript**. The backend uses **Python + FastAPI**, organized by module, with a separate AI package; the API and the worker share one codebase.

### 5.1 Repository layout

```text
practise/
├── src/
│   ├── frontend/                 # Next.js 16 + React 19 (Web Frontend)
│   ├── backend/                  # FastAPI API + Analysis Worker, one codebase
│   └── database/cic.sql          # PostgreSQL schema
├── docs/                         # Requirements, IA, C4, data model, API, folder structure
├── .gitignore                    # Ignores .env files, keeps .env.example
├── CLAUDE.md                     # Rules for coding agents
└── README.md
```

### 5.2 Target Next.js structure

```text
src/frontend/
├── app/                 # App Router: (public)/login, (workspace)/dashboard, anomalies/[anomalyId],
│                        # changes, tickets/import, baseline, audit, settings, users, profile, forbidden
├── features/            # auth, dashboard, anomalies, suggestions, changes, tickets,
│                        # baseline, audit, settings, users, profile (components/, hooks/, api.ts)
├── components/          # Shared UI; ui/ holds shadcn/ui components
├── lib/                 # api-client, api-types (from OpenAPI), formatting, utils (cn)
├── proxy.ts             # Login and role redirects (Next.js 16 name for middleware)
├── tests/               # Vitest + Testing Library
├── components.json      # shadcn/ui configuration
├── .env.example
└── package.json         # Tailwind CSS 4, shadcn/ui, react-hook-form + zod, TanStack Query/Table
```

```text
app/ route → feature component → feature hook → feature api.ts → api-client → REST API
```

### 5.3 Target FastAPI modular structure

```text
src/backend/
├── app/
│   ├── main.py  worker.py  api_router.py
│   ├── core/            # config, database, security, container (DI), deps, errors
│   ├── modules/         # auth, users, settings, changes, tickets, logs, integration,
│   │   └── <module>/    # baseline, anomalies, suggestions, dashboard, audit, jobs
│   │       ├── router.py        # controller, exposed through api_router
│   │       ├── service.py       # business logic, depends on interfaces
│   │       ├── repository.py    # Protocol + SQLAlchemy implementation
│   │       ├── models.py  schemas.py  dependencies.py
│   └── ai/              # LLMClient interface, llm_client, masking, evidence, generator, validator
├── tests/               # fakes/, modules/, ai/
├── alembic/
├── .env.example
├── requirements.txt     # runtime dependencies (pinned)
├── requirements-dev.txt # + pytest, ruff, mypy
└── Dockerfile           # one image: api or worker
```

```text
api_router → module/router → module/service → repository interface → PostgreSQL
worker → module/service or ai/ → repository → PostgreSQL
```

Modules call each other only through services; implementations are injected from `core/container.py`, so tests swap them for fakes.

Module ownership, rules, and environment variables: [Target Folder Structure](docs/07-folder-structure.md).

## 6. Detailed Class and Sequence Design

Detailed design derives from the C4 components (section 3), the database and OpenAPI contracts (section 4), and the module structure (section 5). Names are Python classes inside the FastAPI modules; these are target design views.

### 6.1 C4 Level 4 — Code collaboration

The two core features: **Suspect Ranking** (rule-based, no LLM) and **Suggested Resolution** (LLM with evidence validation). Both run in the worker; users read the results through the API.

#### L4.1 Suspect Ranking

```mermaid
flowchart TB
    subgraph ranking["modules/anomalies [Module]"]
        direction TB
        router["anomalies.router<br/><i>[FastAPI router]</i><br/>list_suspects, submit_feedback"]
        detect["AnomalyDetectionService<br/><i>[Python class]</i><br/>Compares ticket counts with the<br/>active baseline, creates anomalies"]
        rank["SuspectRankingService<br/><i>[Python class]</i><br/>Finds changes in the tracing window,<br/>scores them, stores ranked suspects"]
        scorer["SuspectScorer<br/><i>[Python class, pure]</i><br/>Five factors × weights → score 0–100,<br/>level, explanation per factor"]
        repo["SuspectRepository / AnomalyRepository<br/><i>[Protocol]</i><br/>replace_for_anomaly, list_by_anomaly"]
        impl["SqlAlchemySuspectRepository<br/><i>[Python class]</i><br/>Implements the Protocol with SQL"]
        detect --> rank
        rank --> scorer
        rank --> repo
        router --> repo
        impl -.->|"implements"| repo
    end

    worker["worker.py<br/><i>[Job runner]</i>"]
    baseline["BaselineService<br/><i>[modules/baseline]</i>"]
    tickets["TicketService<br/><i>[modules/tickets]</i>"]
    changes["ChangeService<br/><i>[modules/changes]</i>"]
    logs["LogService<br/><i>[modules/logs]</i>"]
    jobs["JobService<br/><i>[modules/jobs]</i>"]
    db[("PostgreSQL")]

    worker --> detect
    detect --> baseline
    detect --> tickets
    rank --> changes
    rank --> logs
    rank -->|"enqueue SUGGESTION_GENERATION"| jobs
    impl --> db

    style scorer fill:#0b4f9e,color:#fff
    style rank fill:#0b4f9e,color:#fff
    style detect fill:#1168bd,color:#fff
    style router fill:#1168bd,color:#fff
    style repo fill:#1168bd,color:#fff
    style impl fill:#1168bd,color:#fff
```

#### L4.2 Suggested Resolution

```mermaid
flowchart TB
    subgraph sugg["modules/suggestions [Module]"]
        direction TB
        router["suggestions.router<br/><i>[FastAPI router]</i><br/>get_suggested_resolution,<br/>confirm_suggested_resolution"]
        service["SuggestionService<br/><i>[Python class]</i><br/>generate (worker), get_current,<br/>decide (confirm / reject)"]
        policy["SuggestionPolicy<br/><i>[Python class]</i><br/>Only IT Manager, Change Engineer,<br/>Admin may decide"]
        repo["SuggestionRepository<br/><i>[Protocol]</i><br/>next_version, add, get_current, update"]
        impl["SqlAlchemySuggestionRepository<br/><i>[Python class]</i>"]
        router --> service
        service --> policy
        service --> repo
        impl -.->|"implements"| repo
    end

    subgraph ai["ai/ [Package]"]
        direction TB
        collector["EvidenceCollector<br/>Logs, tickets, change, rollback plan,<br/>confirmed past incidents, guidelines"]
        masker["Masker<br/>Removes names, e-mails, IPs, paths"]
        generator["SuggestionGenerator<br/>Builds the prompt, parses the draft"]
        llm["LLMClient<br/><i>[Protocol]</i>"]
        provider["AnthropicLLMClient<br/>Implements LLMClient"]
        validator["EvidenceValidator<br/>Drops uncited causes,<br/>sets basis and label"]
        collector --> masker --> generator --> llm
        provider -.->|"implements"| llm
        generator --> validator
    end

    worker["worker.py"]
    db[("PostgreSQL")]
    ext["LLM Provider"]

    worker --> service
    service --> collector
    service --> generator
    service --> validator
    impl --> db
    provider --> ext

    style service fill:#0b4f9e,color:#fff
    style validator fill:#0b4f9e,color:#fff
    style router fill:#1168bd,color:#fff
    style policy fill:#1168bd,color:#fff
    style repo fill:#1168bd,color:#fff
    style impl fill:#1168bd,color:#fff
```

Source: [C4 Level 4 — Code](docs/architecture/c4/04-code.md)

### 6.2 Core class diagrams

#### 1. Change Management

```mermaid
classDiagram
    direction TB

    class ChangesRouter {
        <<router>>
        +list_changes(filters, page, user) Page~ChangeRead~
        +get_change(change_id, user) ChangeRead
        +create_change(body: ChangeCreate, user) ChangeRead
        +update_change(change_id, body: ChangeCreate, user) ChangeRead
        +update_change_status(change_id, body: StatusUpdate, user) ChangeRead
    }
    class ChangeCreate {
        <<Pydantic>>
        +type: ChangeType
        +title: str
        +start_at: datetime
        +end_at: Optional~datetime~
        +scope: ScopeIn
        +implementer_id: UUID
        +rollback_plan: RollbackPlanIn
        +status: ChangeStatus
    }
    class ScopeIn {
        <<Pydantic>>
        +departments: list~str~
        +branches: list~str~
        +software: list~str~
        +device_groups: list~str~
    }
    class ChangeService {
        -repo: ChangeRepository
        -policy: ChangePolicy
        -validator: ChangeValidator
        -lookups: LookupService
        -audit: AuditService
        +create(data, actor) ChangeRead
        +update(change_id, data, actor) ChangeRead
        +update_status(change_id, status, note, actor) ChangeRead
        +find_in_window(start, end) list~Change~
    }
    class ChangePolicy {
        +ensure_can_create(actor) None
        +ensure_can_edit(actor, change) None
    }
    class ChangeValidator {
        +validate(data, scope_ids) None
    }
    class LookupService {
        +resolve_scope(scope: ScopeIn) ScopeIds
    }
    class ChangeRepository {
        <<Protocol>>
        +add(change) Change
        +get(change_id) Optional~Change~
        +update(change) Change
        +list(filters, page) Page~Change~
        +started_between(start, end) list~Change~
    }
    class SqlAlchemyChangeRepository {
        -session: Session
    }
    class Change {
        <<SQLAlchemy>>
        +id: UUID
        +type: ChangeType
        +start_at: datetime
        +status: ChangeStatus
        +implementer_id: UUID
        +rollback_available: bool
        +rollback_steps: Optional~str~
        +departments: list~Department~
        +branches: list~Branch~
        +software: list~Software~
        +device_groups: list~DeviceGroup~
    }
    class AuditService {
        +record(action, object_type, object_id, actor, details) None
    }

    ChangesRouter --> ChangeService
    ChangesRouter ..> ChangeCreate
    ChangeCreate *-- ScopeIn
    ChangeService --> ChangeRepository
    ChangeService --> ChangePolicy
    ChangeService --> ChangeValidator
    ChangeService --> LookupService
    ChangeService --> AuditService
    SqlAlchemyChangeRepository ..|> ChangeRepository
    SqlAlchemyChangeRepository --> Change
```

#### 2. Suspect Ranking

```mermaid
classDiagram
    direction TB

    class AnomaliesRouter {
        <<router>>
        +list_anomalies(filters, page, user) Page~AnomalyRead~
        +get_anomaly(anomaly_id, user) AnomalyRead
        +list_suspects(anomaly_id, user) list~SuspectRead~
        +list_anomaly_logs(anomaly_id, page, user) Page~ErrorLogGroup~
        +submit_suspect_feedback(suspect_id, body, user) None
    }
    class AnomalyDetectionService {
        -baseline: BaselineService
        -tickets: TicketService
        -anomalies: AnomalyRepository
        -settings: SettingsService
        +detect(now) list~Anomaly~
    }
    class SuspectRankingService {
        -changes: ChangeService
        -logs: LogService
        -scorer: SuspectScorer
        -suspects: SuspectRepository
        -jobs: JobService
        +rank(anomaly) list~Suspect~
    }
    class SuspectScorer {
        <<pure>>
        +score(anomaly, change, context, weights) ScoreResult
        -time_proximity(anomaly, change) FactorScore
        -scope_match(anomaly, change) FactorScore
        -category_keyword_match(anomaly, change) FactorScore
        -anomaly_magnitude(anomaly) FactorScore
        -change_risk(change) FactorScore
    }
    class ScoreResult {
        +score: int
        +level: Severity
        +factors: list~FactorScore~
    }
    class FactorScore {
        +factor: ScoreFactor
        +contribution: float
        +explanation: str
    }
    class Weights {
        +time_proximity: float
        +scope_match: float
        +category_keyword: float
        +anomaly_magnitude: float
        +change_risk: float
    }
    class AnomalyRepository {
        <<Protocol>>
        +add(anomaly, ticket_ids, log_ids) Anomaly
        +get(anomaly_id) Optional~Anomaly~
        +list(filters, page) Page~Anomaly~
    }
    class SuspectRepository {
        <<Protocol>>
        +replace_for_anomaly(anomaly_id, results) list~Suspect~
        +list_by_anomaly(anomaly_id) list~Suspect~
        +save_feedback(suspect_id, user_id, verdict, note) None
    }
    class Anomaly {
        <<SQLAlchemy>>
        +id: UUID
        +category_id: UUID
        +department_id: UUID
        +start_at: datetime
        +actual_count: int
        +expected_count: Decimal
        +severity: Severity
    }
    class Suspect {
        <<SQLAlchemy>>
        +id: UUID
        +anomaly_id: UUID
        +change_id: UUID
        +rank: int
        +score: int
        +factors: list~SuspectFactor~
    }

    AnomaliesRouter --> AnomalyRepository
    AnomaliesRouter --> SuspectRepository
    AnomalyDetectionService --> AnomalyRepository
    AnomalyDetectionService ..> SuspectRankingService : new anomaly
    SuspectRankingService --> SuspectScorer
    SuspectRankingService --> SuspectRepository
    SuspectScorer ..> Weights
    SuspectScorer ..> ScoreResult
    ScoreResult *-- FactorScore
    AnomalyRepository ..> Anomaly
    SuspectRepository ..> Suspect
```

#### 3. Suggested Resolution

```mermaid
classDiagram
    direction TB

    class SuggestionsRouter {
        <<router>>
        +get_suggested_resolution(suspect_id, user) SuggestionRead
        +confirm_suggested_resolution(suspect_id, body: DecisionIn, user) SuggestionRead
    }
    class SuggestionService {
        -repo: SuggestionRepository
        -policy: SuggestionPolicy
        -collector: EvidenceCollector
        -generator: SuggestionGenerator
        -validator: EvidenceValidator
        -audit: AuditService
        +generate(suspect_id) Suggestion
        +get_current(suspect_id) SuggestionRead
        +decide(suspect_id, decision, note, actor) SuggestionRead
    }
    class SuggestionPolicy {
        +ensure_can_decide(actor) None
        +ensure_confirmable(suggestion) None
    }
    class SuggestionRepository {
        <<Protocol>>
        +next_version(suspect_id) int
        +add(suggestion) Suggestion
        +get_current(suspect_id) Optional~Suggestion~
        +update(suggestion) Suggestion
    }
    class EvidenceCollector {
        +collect(suspect_id) EvidenceBundle
    }
    class EvidenceBundle {
        +logs: list~LogEvidence~
        +tickets: list~TicketEvidence~
        +change: ChangeEvidence
        +past_incidents: list~PastIncident~
        +guidelines: list~Guideline~
    }
    class Masker {
        +mask(text) str
    }
    class SuggestionGenerator {
        -llm: LLMClient
        -masker: Masker
        +draft(bundle) Draft
    }
    class LLMClient {
        <<Protocol>>
        +complete(prompt, timeout) str
    }
    class AnthropicLLMClient {
        -api_key: str
        -model: str
    }
    class EvidenceValidator {
        <<pure>>
        +validate(draft, bundle) ValidatedSuggestion
    }
    class Draft {
        +causes: list~DraftStatement~
        +steps: list~DraftStatement~
    }
    class DraftStatement {
        +text: str
        +basis: StatementBasis
        +evidence: list~EvidenceRef~
    }
    class ValidatedSuggestion {
        +status: SuggestionStatus
        +label: SuggestionLabel
        +causes: list~DraftStatement~
        +steps: list~DraftStatement~
    }
    class Suggestion {
        <<SQLAlchemy>>
        +id: UUID
        +suspect_id: UUID
        +version: int
        +status: SuggestionStatus
        +label: SuggestionLabel
        +decision: Optional~SuggestionDecision~
        +statements: list~SuggestionStatement~
    }

    SuggestionsRouter --> SuggestionService
    SuggestionService --> SuggestionRepository
    SuggestionService --> SuggestionPolicy
    SuggestionService --> EvidenceCollector
    SuggestionService --> SuggestionGenerator
    SuggestionService --> EvidenceValidator
    EvidenceCollector ..> EvidenceBundle
    SuggestionGenerator --> Masker
    SuggestionGenerator --> LLMClient
    AnthropicLLMClient ..|> LLMClient
    SuggestionGenerator ..> Draft
    Draft *-- DraftStatement
    EvidenceValidator ..> ValidatedSuggestion
    SuggestionRepository ..> Suggestion
```

Authentication, enums, validator rules, and mapping boundaries: [Class diagrams](docs/architecture/uml/01-class-diagrams.md).

### 6.3 Sequence diagrams

Seven runtime sequences map each user story and OpenAPI operation to its router, service, policy/validator, repository, database interaction, and error paths:

| # | Flow | Trigger |
|---|---|---|
| 1 | Login | `POST /auth/login` |
| 2 | Create and edit a change (own-record rule) | `POST /changes`, `PUT /changes/{changeId}` |
| 3 | Ingest error logs (masking, idempotency) | `POST /integration/logs` |
| 4 | Detect anomaly and rank suspects | Scheduled worker job |
| 5 | Generate suggested resolution (LLM, validation) | `SUGGESTION_GENERATION` job |
| 6 | Review anomaly, suspects, and suggestion | `GET /anomalies/{id}/suspects`, `GET /suspects/{id}/suggestion` |
| 7 | Confirm or reject a suggestion | `PUT /suspects/{id}/suggestion/confirmation` |

- [Sequence diagrams](docs/architecture/uml/02-sequence-diagrams.md)
- [Detailed UML overview](docs/architecture/uml/README.md)

## Documentation

- Requirements: [Scope](docs/01-scope.md), [Features](docs/02-features.md), [INVEST backlog](docs/05-invest-requirements.md).
- Actors and use cases: [Actors, roles, and use cases](docs/03-use-cases.md).
- UI/UX: [Information architecture](docs/04-information-architecture.md).
- Architecture: [C4 model](docs/architecture/c4/README.md).
- Folder structure: [Next.js and FastAPI modules](docs/07-folder-structure.md).
- Code-level design: [C4 Level 4](docs/architecture/c4/04-code.md), [class diagrams](docs/architecture/uml/01-class-diagrams.md), [sequence diagrams](docs/architecture/uml/02-sequence-diagrams.md).
- Database: [Data model](docs/06-data-model.md), [ER diagram](docs/DATABASE.md), [PostgreSQL schema](src/database/cic.sql).
- API contract: [OpenAPI 3.0 specification](docs/api/openapi.yaml) and [API documentation](docs/api/README.md).
- Agent rules: [CLAUDE.md](CLAUDE.md).

## Project Progress

- [x] Define scope, goals, and user roles
- [x] Write the feature list and use cases
- [x] Write user stories following INVEST
- [x] Design the information architecture and screen permissions
- [x] Design the screen hierarchy, task flows, and UI states
- [ ] Write acceptance criteria and business rules
- [ ] Write non-functional requirements
- [ ] Design the baseline, anomaly detection, and suspect ranking algorithms
- [x] Design the C4 System Context, Container, and Component views
- [x] Design the database schema and data relationships
- [x] Write the API documentation in OpenAPI 3.0
- [x] Design the Next.js frontend and FastAPI backend folder structure
- [x] Design class diagrams and sequence diagrams
- [ ] Build the UI prototype for each role
- [ ] Build the backend and connect the frontend to the API
