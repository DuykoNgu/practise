# C4 Level 4 — Code — Two Core Features

> **Status:** Target design · Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2

The two features that answer the core question "which recent change caused this spike, and what should we do?":

- **L4.1 Suspect Ranking** — `modules/anomalies` (rule-based, no LLM).
- **L4.2 Suggested Resolution** — `modules/suggestions` + the [`cic_ai` package](../ai-package.md) (LLM with evidence validation).

Both run in the Analysis Worker; users read the results through the Backend API.

## L4.1 Suspect Ranking

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

## L4.2 Suggested Resolution

```mermaid
flowchart TB
    subgraph sugg["modules/suggestions [Module]"]
        direction TB
        router["suggestions.router<br/><i>[FastAPI router]</i><br/>get_suggested_resolution,<br/>confirm_suggested_resolution"]
        service["SuggestionService<br/><i>[Python class]</i><br/>generate (worker), get_current,<br/>decide (confirm / reject)"]
        policy["SuggestionPolicy<br/><i>[Python class]</i><br/>Only IT Manager, Change Engineer,<br/>Admin may decide"]
        repo["SuggestionRepository<br/><i>[Protocol]</i><br/>next_version, add, get_current, update"]
        impl["SqlAlchemySuggestionRepository<br/><i>[Python class]</i>"]
        collector["EvidenceCollector<br/>SQL walk: logs, tickets, change, rollback plan,<br/>confirmed past incidents, guidelines"]
        router --> service
        service --> policy
        service --> repo
        impl -.->|"implements"| repo
    end

    subgraph ai["cic_ai [Package · src/ai]"]
        direction TB
        bundle["EvidenceBundle<br/>Contract: items with short refs"]
        masker["Masker<br/>Removes names, e-mails, IPs, paths"]
        generator["SuggestionGenerator<br/>Builds the prompt, parses the draft"]
        llm["LLMClient<br/><i>[Protocol]</i>"]
        provider["AnthropicLLMClient<br/>Implements LLMClient"]
        validator["EvidenceValidator<br/>Drops uncited causes,<br/>sets basis and label"]
        bundle --> masker --> generator --> llm
        provider -.->|"implements"| llm
        generator --> validator
    end

    worker["worker.py"]
    db[("PostgreSQL")]
    ext["LLM Provider"]

    worker --> service
    service --> collector
    collector -->|"builds"| bundle
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

## Shared rules for both features

- The suspicion score is final before `cic_ai` runs; `SuggestionService.generate` reads suspects, it never changes scores.
- `SuspectScorer` and `EvidenceValidator` are pure classes (no database, no network) so they are unit-tested directly.
- Services depend on Protocols; `core/container.py` binds the SQLAlchemy repositories and `cic_ai.AnthropicLLMClient`. Tests use `tests/fakes/` and `cic_ai.StubLLMClient`.
- If the LLM call fails, the suggestion is stored with status `FAILED`, the job is retried up to `max_attempts`, and the screen shows "No supported suggestion".
- Every decision (confirm / reject) and every feedback is written to the audit log through `AuditService`.
