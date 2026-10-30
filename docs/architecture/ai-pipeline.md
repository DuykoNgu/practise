# AI Pipeline and Knowledge Graph

> **Status:** Target design · Implements F05, F06, F12, F13 · Runs in the Analysis Worker

The AI part answers two questions for every abnormal spike of tickets: **which recent change is the likely cause** (rule-based ranking) and **what should we do** (LLM reasoning over evidence). The LLM never decides the ranking, and every cause it states must point to evidence in the knowledge graph.

## 1. End-to-end flow — from input to output

```mermaid
flowchart TB
    subgraph IN["① Input"]
        direction LR
        logsIn["Error logs<br/><i>Log Source → POST /integration/logs</i>"]
        ticketsIn["Tickets<br/><i>manual · import · ITSM</i>"]
        changesIn["Change records<br/><i>scope · implementer · rollback plan</i>"]
    end

    subgraph PREP["② Extract & classify"]
        direction LR
        mask["Masking<br/>names · e-mail · IP · paths → ***"]
        classify["Classification<br/>signature (SHA-256 of normalized message)<br/>category · level"]
        mapScope["Scope mapping<br/>device group → department, branch"]
    end

    subgraph DETECT["③ Detect & rank"]
        direction LR
        baseline["Baseline<br/>mean, std dev per<br/>category × weekday × hour"]
        anomaly["Anomaly detection (rules)<br/>count > mean + 3 × std dev"]
        rank["Suspect ranking (rules, no LLM)<br/>5 factors × weights → score 0–100"]
    end

    KG[("④ Knowledge graph<br/>changes · tickets · logs · scope ·<br/>anomalies · suspects ·<br/>confirmed incidents · guidelines")]

    subgraph RETRIEVE["⑤ Graph retrieval"]
        direction LR
        traverse["Traverse from the suspect:<br/>change → scope → tickets / logs<br/>anomaly → similar past anomalies<br/>→ confirmed resolutions · guidelines"]
        bundle["Evidence bundle<br/>every item has an id"]
    end

    subgraph REASON["⑥ LLM reasoning engine"]
        direction LR
        prompt["Prompt builder<br/>masked evidence + ids<br/>+ instructions to cite ids"]
        llm["LLM<br/>drafts likely cause<br/>and resolution steps"]
    end

    subgraph VALIDATE["⑦ Solution validation"]
        direction LR
        checkCause["Each cause cites a<br/>valid evidence id?<br/>no → remove"]
        checkStep["Each step cites rollback plan,<br/>past incident, or guideline?<br/>yes → Standard · no → Flexible"]
    end

    subgraph OUT["⑧ Output"]
        direction LR
        verified["Verified solution<br/><b>Standard</b> steps with sources<br/>label CONFIRMED after a person confirms"]
        hypothesis["New hypothesis<br/><b>Flexible</b> steps (LLM knowledge)<br/>always label HYPOTHESIS"]
        nosupport["No supported suggestion<br/>no cause with evidence"]
    end

    subgraph FB["⑨ Review & feedback"]
        direction LR
        screen["Anomaly detail screen<br/>suspects · evidence · labels"]
        decide["Suspect feedback<br/>+ confirm / reject suggestion"]
    end

    logsIn --> mask --> classify --> mapScope
    ticketsIn --> mapScope
    changesIn --> KG
    mapScope --> KG
    KG --> baseline --> anomaly --> rank
    rank -->|"suspects stored first"| KG
    rank --> traverse
    KG --> traverse --> bundle --> prompt --> llm
    llm --> checkCause --> checkStep
    checkStep --> verified
    checkStep --> hypothesis
    checkCause --> nosupport
    verified --> screen
    hypothesis --> screen
    nosupport --> screen
    screen --> decide
    decide -->|"confirmed resolution becomes<br/>PAST_INCIDENT knowledge"| KG

    style KG fill:#0b4f9e,color:#fff
    style llm fill:#7b3fbf,color:#fff
    style rank fill:#1168bd,color:#fff
    style anomaly fill:#1168bd,color:#fff
    style checkCause fill:#2e7d32,color:#fff
    style checkStep fill:#2e7d32,color:#fff
    style verified fill:#2e7d32,color:#fff
    style hypothesis fill:#f9a825,color:#000
    style nosupport fill:#9e9e9e,color:#fff
```

| Step | What happens | Code (see [class diagrams](uml/01-class-diagrams.md)) | Data |
|---|---|---|---|
| ① Input | Logs, tickets, and changes arrive through the API or the UI | `integration`, `tickets`, `changes` modules | `error_logs`, `tickets`, `changes` |
| ② Extraction & classification | Mask sensitive data, compute signature and category, map device groups to department and branch | `ai/masking.py`, `LogService`, `LookupService` | `error_logs.signature`, `category_id` |
| ③ Detection & ranking | Compare counts with the baseline, create anomalies, score candidate changes | `BaselineService`, `AnomalyDetectionService`, `SuspectScorer` | `baseline_*`, `anomalies`, `suspects`, `suspect_factors` |
| ④ Knowledge graph | All entities and their links, stored relationally (section 2) | Repositories | All tables below |
| ⑤ Retrieval | Walk the graph from the suspect to collect evidence | `EvidenceCollector` | Read-only joins |
| ⑥ LLM reasoning | Send masked evidence with ids; receive cause and steps that cite ids | `SuggestionGenerator`, `LLMClient` | — |
| ⑦ Validation | Remove uncited causes; mark each step Standard or Flexible | `EvidenceValidator` | — |
| ⑧ Output | Store the suggestion with status and label | `SuggestionService` | `suggestions`, `suggestion_statements`, `statement_evidence` |
| ⑨ Feedback | Users judge suspects and confirm or reject suggestions; confirmed ones feed back into the graph | `anomalies`, `suggestions` modules | `suspect_feedback`, `suggestions.decision` |

## 2. Knowledge graph

The knowledge graph is the set of entities CIC knows about and the relations between them. In V1 it is **stored in PostgreSQL**: nodes are rows, edges are foreign keys and link tables. There is no separate graph database; retrieval is done with SQL joins (and recursive CTEs where a path is longer). A graph database can be introduced later behind the same `EvidenceCollector` if traversal becomes slow.

```mermaid
flowchart LR
    CH(["Change"])
    TK(["Ticket"])
    LG(["Error log"])
    AN(["Anomaly"])
    SP(["Suspect"])
    SG(["Confirmed resolution<br/><i>past incident</i>"])
    GL(["Guideline"])
    RB(["Rollback plan"])
    DEP(["Department"])
    BR(["Branch"])
    SW(["Software"])
    DG(["Device group"])
    CAT(["Category"])
    US(["User"])

    CH -- "AFFECTS" --> DEP
    CH -- "AFFECTS" --> BR
    CH -- "AFFECTS" --> SW
    CH -- "AFFECTS" --> DG
    CH -- "HAS_PLAN" --> RB
    US -- "IMPLEMENTED" --> CH
    TK -- "REPORTED_FROM" --> DEP
    TK -- "REPORTED_FROM" --> BR
    TK -- "ABOUT" --> SW
    TK -- "IN_CATEGORY" --> CAT
    LG -- "EMITTED_BY" --> DG
    LG -- "EMITTED_BY" --> SW
    LG -- "IN_CATEGORY" --> CAT
    DG -- "BELONGS_TO" --> DEP
    TK -- "PART_OF" --> AN
    LG -- "PART_OF" --> AN
    AN -- "IN_GROUP" --> CAT
    CH -- "SUSPECTED_IN" --> SP
    SP -- "FOR" --> AN
    SP -- "RESOLVED_BY" --> SG
    SG -- "CITES" --> LG
    SG -- "CITES" --> RB
    GL -- "APPLIES_TO" --> CAT
    GL -- "APPLIES_TO" --> SW

    style CH fill:#1168bd,color:#fff
    style AN fill:#1168bd,color:#fff
    style SP fill:#0b4f9e,color:#fff
    style SG fill:#2e7d32,color:#fff
    style GL fill:#2e7d32,color:#fff
    style RB fill:#2e7d32,color:#fff
```

### Nodes and edges in the database

| Graph element | Stored as |
|---|---|
| Change, Ticket, Error log, Anomaly, Suspect, User | `changes`, `tickets`, `error_logs`, `anomalies`, `suspects`, `app_users` |
| Department, Branch, Software, Device group, Category | Lookup tables |
| Rollback plan | `changes.rollback_*` columns (1:1 with the change) |
| Confirmed resolution (past incident) | `suggestions` with `decision = CONFIRMED` |
| Guideline | `guidelines` |
| `AFFECTS` | `change_departments`, `change_branches`, `change_software`, `change_device_groups` |
| `REPORTED_FROM`, `ABOUT`, `IN_CATEGORY`, `EMITTED_BY` | Foreign keys on `tickets` and `error_logs` |
| `BELONGS_TO` | `device_groups.department_id`, `branch_id` |
| `PART_OF` | `anomaly_tickets`, `anomaly_logs` |
| `SUSPECTED_IN`, `FOR` | `suspects.change_id`, `suspects.anomaly_id` |
| `RESOLVED_BY`, `CITES` | `suggestions.suspect_id`, `statement_evidence` |
| `APPLIES_TO` | `guidelines.category_id`, `software_id` |

### Retrieval: what `EvidenceCollector` walks for one suspect

| # | Path | Evidence produced |
|---|---|---|
| 1 | Suspect → Anomaly → `PART_OF` ← Error logs (grouped by signature) | `LOG` items (masked messages, counts) |
| 2 | Suspect → Anomaly → `PART_OF` ← Tickets (sample) | `TICKET` items |
| 3 | Suspect → Change → `AFFECTS` → scope; Change → `HAS_PLAN` | `CHANGE` and `ROLLBACK_PLAN` items |
| 4 | Anomaly → same category and overlapping scope → past Anomalies → Suspect → `RESOLVED_BY` (confirmed) | `PAST_INCIDENT` items |
| 5 | Anomaly category / Change software → `APPLIES_TO` ← Guidelines | `GUIDELINE` items |

Limits keep the prompt small: at most 20 log groups, 10 tickets, 5 past incidents, and 5 guidelines, chosen by recency and scope overlap.

## 3. Worked example — the printer case

```mermaid
flowchart LR
    patch["Change<br/>Windows patch KB-123<br/>Tue 22:00"]
    acc(["Department<br/>Accounting"])
    rb["Rollback plan<br/>Uninstall KB-123"]
    t["14 tickets<br/>'cannot print'<br/>Wed 08:00–08:15"]
    l["3 error logs<br/>'Spooler crashed for user ***'"]
    an["Anomaly<br/>Printing · Accounting<br/>14 vs expected 1.5"]
    sp["Suspect #1<br/>score 80 · High"]
    out["Suggestion<br/>Cause: patch broke the spooler<br/>(cites log + ticket)<br/>Step 1: uninstall KB-123 — Standard<br/>Step 2: reinstall printer driver — Flexible<br/>Label: Hypothesis"]

    patch -- "AFFECTS" --> acc
    patch -- "HAS_PLAN" --> rb
    t -- "REPORTED_FROM" --> acc
    t -- "PART_OF" --> an
    l -- "PART_OF" --> an
    patch -- "SUSPECTED_IN" --> sp
    sp -- "FOR" --> an
    sp --> out

    style sp fill:#0b4f9e,color:#fff
    style out fill:#f9a825,color:#000
```

After an IT Manager confirms it, the suggestion is recorded as confirmed but stays **Hypothesis** because step 2 is Flexible. Next time printing tickets spike in Accounting after a patch, retrieval path 4 brings this resolution back as a `PAST_INCIDENT`, and step 1 becomes evidence for a Standard step.

## 4. Mapping to the original hybrid proposal

| Proposed stage | CIC design |
|---|---|
| Incoming Error Logs | ① Input (`ingestLogs`), together with tickets and changes |
| Error Extraction & Classification | ② Masking, signature, category, scope mapping |
| Knowledge Graph Retrieval | ④ + ⑤ Relational knowledge graph and `EvidenceCollector` |
| LLM Reasoning Engine | ⑥ `SuggestionGenerator` + `LLMClient` |
| Solution Validation | ⑦ `EvidenceValidator` |
| Verified Solution / New Hypothesis | ⑧ Standard (CONFIRMED after a person confirms) / Flexible (always HYPOTHESIS) |
| Notification + Feedback | ⑨ In-app review and feedback. Push notifications (e-mail, chat) are not in V1 scope |

Rules behind each stage: [BR-008, BR-010–BR-017](../requirements/business-rules.md). Measurable targets: [NFR-AI-001–004, NFR-PRIV-001–002](../requirements/non-functional-requirements.md).
