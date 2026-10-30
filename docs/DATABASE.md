# Database Diagram

> Design status: TARGET V1
>
> Runtime status: SCHEMA DESIGN ONLY; validated on PostgreSQL 16, not connected to an application

PostgreSQL schema `cic` for **Change-Incident Correlation**.

Design files: [cic.sql](../src/database/cic.sql) · [06-data-model.md](06-data-model.md)

## Table groups

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 30, "rankSpacing": 60}}}%%
flowchart LR
  subgraph identity ["Identity & integration"]
    U[app_users]
    AC[api_clients]
  end
  subgraph lookups ["Scope lookups"]
    DEP[departments]
    BR[branches]
    SW[software]
    DG[device_groups]
    CAT[categories]
  end
  subgraph inputs ["Inputs"]
    CH[changes] --> CHS["change_departments / branches /<br/>software / device_groups"]
    IB[import_batches] --> T[tickets]
    EL[error_logs]
  end
  subgraph detection ["Detection"]
    BLR[baseline_runs] --> BLC[baseline_cells]
    BLR --> AN[anomalies]
    AN --> AT[anomaly_tickets]
    AN --> AL[anomaly_logs]
  end
  subgraph ranking ["Ranking & feedback"]
    S[suspects] --> SF[suspect_factors]
    S --> FB[suspect_feedback]
  end
  subgraph ai ["AI suggestion"]
    G[guidelines]
    SG[suggestions] --> SS[suggestion_statements] --> SE[statement_evidence]
  end
  subgraph ops ["Operations"]
    J[jobs]
    SET[settings]
    AUD[audit_logs]
  end

  AN --> S
  CH --> S
  S --> SG
  T --> AT
  EL --> AL
  SE -.-> EL
  SE -.-> T
  SE -.-> CH
  SE -.-> G
  lookups --> inputs
```

## Entity-relationship diagram

```mermaid
erDiagram
    app_users ||--o{ changes : implements
    app_users ||--o{ tickets : records
    app_users ||--o{ import_batches : uploads
    app_users ||--o{ suspect_feedback : gives
    app_users ||--o{ suggestions : decides
    app_users ||--o{ guidelines : writes
    app_users ||--o{ jobs : requests
    app_users ||--o{ audit_logs : performs
    api_clients ||--o{ changes : pushes
    api_clients ||--o{ tickets : pushes
    api_clients ||--o{ error_logs : pushes

    departments ||--o{ device_groups : groups
    branches ||--o{ device_groups : groups
    changes ||--o{ change_departments : scopes
    departments ||--o{ change_departments : in
    changes ||--o{ change_branches : scopes
    branches ||--o{ change_branches : in
    changes ||--o{ change_software : scopes
    software ||--o{ change_software : in
    changes ||--o{ change_device_groups : scopes
    device_groups ||--o{ change_device_groups : in

    import_batches ||--o{ tickets : contains
    categories ||--o{ tickets : classifies
    departments ||--o{ tickets : reports
    branches ||--o{ tickets : reports
    categories ||--o{ error_logs : classifies

    baseline_runs ||--o{ baseline_cells : contains
    categories ||--o{ baseline_cells : measures
    baseline_runs ||--o{ anomalies : compared_with
    anomalies ||--o{ anomaly_tickets : contains
    tickets ||--o{ anomaly_tickets : in
    anomalies ||--o{ anomaly_logs : contains
    error_logs ||--o{ anomaly_logs : in

    anomalies ||--o{ suspects : ranks
    changes ||--o{ suspects : suspected_in
    suspects ||--o{ suspect_factors : explains
    suspects ||--o{ suspect_feedback : receives
    suspects ||--o{ suggestions : has_versions
    suggestions ||--o{ suggestion_statements : states
    suggestion_statements ||--o{ statement_evidence : cites
    error_logs |o--o{ statement_evidence : cited_as_log
    tickets |o--o{ statement_evidence : cited_as_ticket
    changes |o--o{ statement_evidence : cited_as_change
    suggestions |o--o{ statement_evidence : cited_as_past_incident
    guidelines |o--o{ statement_evidence : cited_as_guideline

    app_users {
        uuid id PK
        citext email UK
        user_role role
        boolean is_active
    }
    api_clients {
        uuid id PK
        api_client_kind kind
        text key_hash UK
    }
    changes {
        uuid id PK
        change_type type
        timestamptz start_at
        change_status status
        uuid implementer_id FK
        boolean rollback_available
        text rollback_steps
        record_source source
        varchar external_id
    }
    tickets {
        uuid id PK
        timestamptz reported_at
        uuid category_id FK
        uuid department_id FK
        uuid branch_id FK
        uuid software_id FK
        record_source source
        uuid import_batch_id FK
    }
    error_logs {
        uuid id PK
        timestamptz occurred_at
        log_level level
        text message_masked
        char signature
        uuid department_id FK
        uuid category_id FK
    }
    baseline_cells {
        bigint id PK
        uuid baseline_run_id FK
        uuid category_id FK
        smallint weekday
        smallint hour
        numeric mean
        numeric std_dev
    }
    anomalies {
        uuid id PK
        uuid category_id FK
        uuid department_id FK
        timestamptz start_at
        integer actual_count
        numeric expected_count
        severity severity
        anomaly_status status
    }
    suspects {
        uuid id PK
        uuid anomaly_id FK
        uuid change_id FK
        smallint rank
        smallint score
    }
    suspect_factors {
        uuid suspect_id PK
        score_factor factor PK
        numeric contribution
        text explanation
    }
    suggestions {
        uuid id PK
        uuid suspect_id FK
        smallint version
        suggestion_status status
        suggestion_label label
        suggestion_decision decision
        uuid decided_by FK
    }
    suggestion_statements {
        uuid id PK
        uuid suggestion_id FK
        statement_kind kind
        statement_basis basis
        text text
    }
    statement_evidence {
        uuid id PK
        uuid statement_id FK
        evidence_type type
        uuid error_log_id FK
        uuid ticket_id FK
        uuid change_id FK
        text log_snapshot
    }
    jobs {
        uuid id PK
        job_type type
        job_status status
        timestamptz run_after
    }
```

`departments`, `branches`, `software`, `device_groups`, `categories`, `import_batches`, `baseline_runs`, `anomaly_tickets`, `anomaly_logs`, `suspect_feedback`, `guidelines`, `settings`, and `audit_logs` appear in the relationships with their attributes omitted for readability; see [cic.sql](../src/database/cic.sql).

## Enums

| Enum | Values |
|---|---|
| `user_role` | ADMIN, IT_MANAGER, CHANGE_ENGINEER, AGENT |
| `api_client_kind` | ITSM, LOG_SOURCE |
| `record_source` | MANUAL, IMPORT, API |
| `change_type` | PATCH, CONFIG_CHANGE, SOFTWARE_UPGRADE |
| `change_status` | SCHEDULED, IN_PROGRESS, COMPLETED, ROLLED_BACK, FAILED |
| `ticket_status` | NEW, IN_PROGRESS, RESOLVED, CLOSED |
| `import_status` | SUCCEEDED, FAILED |
| `log_level` | WARNING, ERROR, CRITICAL |
| `severity` | HIGH, MEDIUM, LOW |
| `anomaly_status` | OPEN, ACKNOWLEDGED, RESOLVED |
| `run_status` | RUNNING, SUCCEEDED, FAILED |
| `score_factor` | TIME_PROXIMITY, SCOPE_MATCH, CATEGORY_KEYWORD_MATCH, ANOMALY_MAGNITUDE, CHANGE_RISK |
| `feedback_verdict` | CORRECT_CAUSE, UNRELATED |
| `suggestion_status` | PENDING, READY, NO_SUPPORT, FAILED |
| `suggestion_label` | CONFIRMED, HYPOTHESIS |
| `suggestion_decision` | CONFIRMED, REJECTED |
| `statement_kind` | CAUSE, STEP |
| `statement_basis` | STANDARD, LLM_KNOWLEDGE |
| `evidence_type` | LOG, TICKET, CHANGE, ROLLBACK_PLAN, PAST_INCIDENT, GUIDELINE |
| `job_type` | BASELINE_RECOMPUTE, ANOMALY_DETECTION, LOG_CLASSIFICATION, SUGGESTION_GENERATION |
| `job_status` | QUEUED, RUNNING, SUCCEEDED, FAILED |
| `audit_action` | LOGIN, LOGOUT, CREATE, UPDATE, STATUS_CHANGE, IMPORT, CONFIG_CHANGE, FEEDBACK, SUGGESTION_DECISION, BASELINE_RECOMPUTE |
