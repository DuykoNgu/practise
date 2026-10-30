# Sequence Diagrams — CIC V1

> **Status:** Target design · Endpoints follow [openapi.yaml](../../api/openapi.yaml)

Pattern for user flows: **Actor → Next.js page → api-client → FastAPI router → Service → Repository → PostgreSQL**. Background flows start at `worker.py`. Solid arrows are requests, dashed arrows are responses; `alt` shows mutually exclusive outcomes.

| # | Flow | Trigger | Use case / story |
|---|---|---|---|
| 1 | Login | `POST /auth/login` | UC01 · US01 |
| 2 | Create and edit a change | `POST /changes`, `PUT /changes/{changeId}` | UC05, UC06 · US04, US05 |
| 3 | Ingest error logs | `POST /integration/logs` | UC22 · US22 |
| 4 | Detect anomaly and rank suspects | Scheduled job | UC13 · US12 |
| 5 | Generate suggested resolution | `SUGGESTION_GENERATION` job | UC13, UC20 · US20 |
| 6 | Review anomaly, suspects, and suggestion | `GET /anomalies/{id}/suspects`, `GET /suspects/{id}/suggestion` | UC14, UC20, UC23 · US12, US20, US23 |
| 7 | Confirm or reject a suggestion | `PUT /suspects/{id}/suggestion/confirmation` | UC21 · US21 |

## 1. Login — `POST /api/v1/auth/login`

```mermaid
sequenceDiagram
    actor User
    participant Page as Login page (Next.js)
    participant Client as api-client
    participant Router as auth.router
    participant Service as AuthService
    participant Repo as UserRepository
    participant Hasher as PasswordHasher
    participant Token as TokenService
    participant Audit as AuditService
    participant DB as PostgreSQL

    User->>Page: Enter e-mail and password, click Login
    alt Required field empty
        Page-->>User: Show field error (no request sent)
    else Form valid
        Page->>Client: login(email, password)
        Client->>Router: POST /auth/login
        Router->>Service: login(email, password)
        Service->>Repo: get_by_email(email)
        Repo->>DB: SELECT app_users WHERE email = ?
        DB-->>Repo: row or none
        Repo-->>Service: User or None
        alt Unknown user, inactive, or wrong password
            Service->>Hasher: verify(password, hash)
            Hasher-->>Service: false
            Service-->>Router: raise InvalidCredentials
            Router-->>Client: 401 problem+json
            Client-->>Page: error
            Page-->>User: "E-mail or password is incorrect"
        else Valid
            Service->>Hasher: verify(password, hash)
            Hasher-->>Service: true
            Service->>Token: issue(user)
            Token-->>Service: access token (30 min)
            Service->>Repo: touch_last_login(user.id, now)
            Service->>Audit: record(LOGIN, user)
            Audit->>DB: INSERT audit_logs
            Service-->>Router: LoginResponse
            Router-->>Client: 200 token + user
            Client-->>Page: store token
            Page-->>User: Redirect to dashboard
        end
    end
```

## 2. Create and edit a change — `POST /changes`, `PUT /changes/{changeId}`

```mermaid
sequenceDiagram
    actor Eng as Change Engineer
    participant Page as Changes page (Next.js)
    participant Router as changes.router
    participant Deps as core.deps
    participant Service as ChangeService
    participant Policy as ChangePolicy
    participant Lookups as LookupService
    participant Validator as ChangeValidator
    participant Repo as ChangeRepository
    participant Audit as AuditService
    participant DB as PostgreSQL

    Eng->>Page: Fill change form (type, time, scope, rollback plan), Save
    Page->>Router: POST /changes (Bearer JWT)
    Router->>Deps: current_user()
    Deps-->>Router: CurrentUser(role = CHANGE_ENGINEER)
    Router->>Service: create(data, actor)
    Service->>Policy: ensure_can_create(actor)
    Service->>Lookups: resolve_scope(scope names)
    alt Unknown department, branch, software, or device group
        Lookups-->>Service: raise UnknownScope
        Service-->>Router: 400 field errors
        Router-->>Page: problem+json
        Page-->>Eng: Highlight the scope field
    else Scope resolved
        Lookups-->>Service: ScopeIds
        Service->>Validator: validate(data, scope_ids)
        alt No scope, end before start, or rollback without steps
            Validator-->>Service: raise ValidationError
            Service-->>Router: 400 field errors
            Router-->>Page: problem+json
            Page-->>Eng: Keep input, focus first error
        else Valid
            Service->>Repo: add(change)
            Repo->>DB: INSERT changes + change_* scope rows (one transaction)
            Service->>Audit: record(CREATE, change)
            Service-->>Router: ChangeRead
            Router-->>Page: 201 Created
            Page-->>Eng: Close modal, refresh list
        end
    end

    Note over Eng,DB: Edit: PUT /changes/{changeId}
    Eng->>Page: Edit a change, Save
    Page->>Router: PUT /changes/{changeId}
    Router->>Service: update(change_id, data, actor)
    Service->>Repo: get(change_id)
    Repo-->>Service: Change
    Service->>Policy: ensure_can_edit(actor, change)
    alt Actor is a Change Engineer and not the implementer
        Policy-->>Service: raise Forbidden
        Service-->>Router: 403
        Router-->>Page: problem+json
        Page-->>Eng: Show Forbidden message
    else Allowed
        Service->>Repo: update(change)
        Repo->>DB: UPDATE changes, replace scope rows
        Service->>Audit: record(UPDATE, change)
        Router-->>Page: 200 ChangeRead
    end
```

## 3. Ingest error logs — `POST /api/v1/integration/logs`

```mermaid
sequenceDiagram
    participant Src as Log Source
    participant Router as integration.router
    participant Deps as core.deps
    participant Service as LogService
    participant Masker as ai.Masker
    participant Lookups as LookupService
    participant Repo as ErrorLogRepository
    participant Jobs as JobService
    participant DB as PostgreSQL

    Src->>Router: POST /integration/logs (X-API-Key, up to 1000 logs)
    Router->>Deps: api_client(kind = LOG_SOURCE)
    alt Missing, wrong, or inactive key
        Deps-->>Router: raise Unauthorized
        Router-->>Src: 401 problem+json
    else Key valid
        Deps-->>Router: ApiClient
        Router->>Service: ingest(batch, client)
        loop Each log
            Service->>Masker: mask(message)
            Masker-->>Service: masked message
            Service->>Lookups: map device group to department and branch
        end
        Service->>Repo: add_many(logs, client)
        Repo->>DB: INSERT error_logs ON CONFLICT (source_client_id, external_id) DO NOTHING
        DB-->>Repo: inserted count
        Repo-->>Service: accepted, duplicates
        Service->>Jobs: enqueue(LOG_CLASSIFICATION)
        Jobs->>DB: INSERT jobs
        Service-->>Router: IngestResult
        Router-->>Src: 202 accepted, duplicates, rejected
    end
```

The raw message is never stored: masking happens before the insert.

## 4. Detect anomaly and rank suspects — scheduled job

```mermaid
sequenceDiagram
    participant Worker as worker.py
    participant Jobs as JobRepository
    participant Detect as AnomalyDetectionService
    participant Baseline as BaselineService
    participant Tickets as TicketService
    participant Logs as LogService
    participant Rank as SuspectRankingService
    participant Changes as ChangeService
    participant Scorer as SuspectScorer
    participant Repo as SuspectRepository
    participant DB as PostgreSQL

    Worker->>Jobs: claim_next(worker_id)
    Jobs->>DB: SELECT jobs WHERE status = QUEUED FOR UPDATE SKIP LOCKED
    Jobs-->>Worker: ANOMALY_DETECTION job
    Worker->>Detect: detect(now)
    Detect->>Baseline: active_cells()
    Detect->>Tickets: count_by_group(last bucket)
    loop Each group
        alt actual > mean + threshold × std_dev
            Detect->>Logs: logs_in(window, scope)
            Detect->>DB: INSERT anomalies, anomaly_tickets, anomaly_logs
            Detect->>Rank: rank(anomaly)
            Rank->>Changes: find_in_window(start - tracing window, start)
            Changes-->>Rank: candidate changes
            alt No candidate
                Rank-->>Detect: no suspects ("No suspect found")
            else Candidates found
                loop Each change
                    Rank->>Scorer: score(anomaly, change, context, weights)
                    Scorer-->>Rank: ScoreResult (score, level, factors)
                end
                Rank->>Repo: replace_for_anomaly(anomaly, results sorted by score)
                Repo->>DB: DELETE old suspects, INSERT suspects + suspect_factors
                Rank->>DB: INSERT jobs (SUGGESTION_GENERATION per suspect)
            end
        else Within baseline
            Detect-->>Detect: skip group
        end
    end
    Worker->>Jobs: mark_succeeded(job)
```

The ranking finishes and is committed before any LLM call.

## 5. Generate suggested resolution — `SUGGESTION_GENERATION` job

```mermaid
sequenceDiagram
    participant Worker as worker.py
    participant Service as SuggestionService
    participant Repo as SuggestionRepository
    participant Collector as EvidenceCollector
    participant Gen as SuggestionGenerator
    participant Masker as Masker
    participant LLM as LLMClient
    participant Provider as LLM Provider
    participant Validator as EvidenceValidator
    participant DB as PostgreSQL

    Worker->>Service: generate(suspect_id)
    Service->>Repo: next_version(suspect_id)
    Service->>Repo: add(status = PENDING)
    Service->>Collector: collect(suspect_id)
    Collector->>DB: logs, tickets, change, rollback plan, confirmed past incidents, guidelines
    Collector-->>Service: EvidenceBundle
    Service->>Gen: draft(bundle)
    Gen->>Masker: mask(every text in bundle)
    Gen->>LLM: complete(prompt with evidence ids)
    LLM->>Provider: HTTPS request
    alt Provider error or timeout
        Provider-->>LLM: error
        LLM-->>Gen: raise LLMUnavailable
        Gen-->>Service: error
        Service->>Repo: update(status = FAILED)
        Service-->>Worker: retry later (attempts < max_attempts)
    else Draft returned
        Provider-->>LLM: text
        LLM-->>Gen: text
        Gen-->>Service: Draft (causes, steps)
        Service->>Validator: validate(draft, bundle)
        alt No cause cites valid evidence
            Validator-->>Service: status = NO_SUPPORT
        else At least one supported cause
            Validator-->>Service: status = READY, label = HYPOTHESIS, basis per step
        end
        Service->>Repo: update(suggestion, statements, evidence)
        Repo->>DB: UPDATE suggestions, INSERT suggestion_statements, statement_evidence
        Service-->>Worker: done
    end
```

## 6. Review anomaly, suspects, and suggestion

```mermaid
sequenceDiagram
    actor Agent as Service Desk Agent
    participant Page as Anomaly detail (Next.js)
    participant Client as api-client
    participant AnRouter as anomalies.router
    participant SgRouter as suggestions.router
    participant SuspRepo as SuspectRepository
    participant SgService as SuggestionService
    participant DB as PostgreSQL

    Agent->>Page: Open anomaly from dashboard
    Page->>Client: getAnomaly, listSuspects, listAnomalyLogs
    Client->>AnRouter: GET /anomalies/{id}, /suspects, /logs
    AnRouter->>SuspRepo: list_by_anomaly(id)
    SuspRepo->>DB: SELECT suspects, suspect_factors ORDER BY rank
    AnRouter-->>Client: anomaly, suspects with factors, log groups
    Client-->>Page: data
    alt No suspects
        Page-->>Agent: "No suspect found", suggest widening the window
    else Suspects
        Page-->>Agent: Ranked suspects with score, level, factor explanations
        Agent->>Page: Open suspect #1
        Page->>Client: getSuggestedResolution(suspect_id)
        Client->>SgRouter: GET /suspects/{id}/suggestion
        SgRouter->>SgService: get_current(suspect_id)
        SgService->>DB: latest version + statements + evidence
        alt Status NO_SUPPORT, FAILED, or PENDING
            SgRouter-->>Client: 404 no-supported-suggestion
            Page-->>Agent: "No supported suggestion"
        else READY
            SgRouter-->>Client: 200 SuggestionRead
            Page-->>Agent: Cause with evidence, steps labeled Standard or Flexible, label Hypothesis or Confirmed
        end
    end
```

The Agent sees no confirm button: the UI hides it, and the API would reject it (flow 7).

## 7. Confirm or reject a suggestion — `PUT /suspects/{suspectId}/suggestion/confirmation`

```mermaid
sequenceDiagram
    actor Mgr as IT Manager
    participant Page as Anomaly detail (Next.js)
    participant Router as suggestions.router
    participant Service as SuggestionService
    participant Policy as SuggestionPolicy
    participant Repo as SuggestionRepository
    participant Audit as AuditService
    participant DB as PostgreSQL

    Mgr->>Page: Click Confirm (or Reject), add note
    Page->>Router: PUT /suspects/{id}/suggestion/confirmation
    Router->>Service: decide(suspect_id, decision, note, actor)
    Service->>Policy: ensure_can_decide(actor)
    alt Actor is an Agent
        Policy-->>Service: raise Forbidden
        Router-->>Page: 403 problem+json
    else Allowed
        Service->>Repo: get_current(suspect_id)
        Repo-->>Service: Suggestion (READY)
        alt Decision is REJECTED
            Service->>Repo: update(decision = REJECTED, label = HYPOTHESIS)
        else Decision is CONFIRMED
            Service->>Policy: ensure_confirmable(suggestion)
            alt Some statement is LLM_KNOWLEDGE
                Service->>Repo: update(decision = CONFIRMED, label = HYPOTHESIS)
                Note right of Service: Recorded as confirmed by a person,<br/>but stays a hypothesis because it<br/>contains LLM-knowledge steps
            else All statements STANDARD
                Service->>Repo: update(decision = CONFIRMED, label = CONFIRMED)
            end
        end
        Repo->>DB: UPDATE suggestions SET decision, decided_by, decided_at
        Service->>Audit: record(SUGGESTION_DECISION, suggestion)
        Router-->>Page: 200 SuggestionRead
        Page-->>Mgr: Show updated label
    end
```

A confirmed suggestion becomes `PAST_INCIDENT` evidence for later similar anomalies (flow 5).

## 8. Common error conventions

| Situation | Status | Where it is decided |
|---|---|---|
| Field validation fails | 400 with `errors` per field | Pydantic schema or `*Validator` |
| Missing or invalid JWT / API key | 401 | `core.deps` |
| Role or own-record rule fails | 403 | `*Policy` |
| Resource or supported suggestion not found | 404 | Service |
| Duplicate e-mail | 409 | `UserService` (unique constraint) |
| Unexpected error | 500 with `traceId` only | `core.errors` |
