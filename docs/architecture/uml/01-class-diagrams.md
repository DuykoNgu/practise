# Class Diagrams — Authentication, Changes, Suspect Ranking, Suggested Resolution

> **Status:** Target design · Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2
>
> Names follow [Target Folder Structure](../../07-folder-structure.md); tables follow [cic.sql](../../../src/database/cic.sql); operations follow [openapi.yaml](../../api/openapi.yaml).

Stereotypes: `<<router>>` FastAPI router functions · `<<Pydantic>>` request/response schema · `<<SQLAlchemy>>` table model · `<<Protocol>>` interface injected by `core/container.py`.

## 1. Authentication — `modules/auth`, `modules/users`, `core/security`

```mermaid
classDiagram
    direction TB

    class AuthRouter {
        <<router>>
        +login(body: LoginRequest) LoginResponse
        +logout(user: CurrentUser) None
    }
    class LoginRequest {
        <<Pydantic>>
        +email: EmailStr
        +password: SecretStr
    }
    class LoginResponse {
        <<Pydantic>>
        +access_token: str
        +expires_at: datetime
        +user: UserRead
    }
    class AuthService {
        -users: UserRepository
        -hasher: PasswordHasher
        -tokens: TokenService
        -audit: AuditService
        +login(email, password) LoginResponse
    }
    class UserRepository {
        <<Protocol>>
        +get_by_email(email) Optional~User~
        +get(user_id) Optional~User~
        +touch_last_login(user_id, at) None
    }
    class SqlAlchemyUserRepository {
        -session: Session
    }
    class PasswordHasher {
        +hash(plain) str
        +verify(plain, hashed) bool
    }
    class TokenService {
        -secret: str
        -expire_minutes: int
        +issue(user) AccessToken
        +decode(token) TokenClaims
    }
    class CurrentUser {
        +id: UUID
        +role: UserRole
        +require(roles) None
    }
    class User {
        <<SQLAlchemy>>
        +id: UUID
        +email: str
        +password_hash: str
        +role: UserRole
        +is_active: bool
    }

    AuthRouter --> AuthService
    AuthRouter ..> LoginRequest
    AuthRouter ..> LoginResponse
    AuthService --> UserRepository
    AuthService --> PasswordHasher
    AuthService --> TokenService
    SqlAlchemyUserRepository ..|> UserRepository
    SqlAlchemyUserRepository --> User
    TokenService ..> CurrentUser : decode builds
```

Rules: an inactive user cannot log in; the same error is returned for an unknown e-mail and a wrong password; the password hash never leaves `AuthService`.

## 2. Change Management — `modules/changes`

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

Rules: `ChangePolicy.ensure_can_edit` lets a Change Engineer edit only changes where they are the implementer; `ChangeValidator` requires at least one scope value, `end_at ≥ start_at`, and steps when a rollback plan is available. Scope names are resolved to lookup ids by `LookupService` (module `settings`).

## 3. Suspect Ranking — `modules/anomalies`

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

Rules: the score is `round(100 × Σ(weightᵢ × factorᵢ) / Σ weightᵢ)` with each factor in [0, 1], capped at 39 when scope and keyword match are both 0 (factor formulas: [09-algorithms.md](../../09-algorithms.md#4-suspect-ranking)); level is High ≥ 70, Medium ≥ 40, otherwise Low; ranks are 1..n by descending score; a new ranking replaces the old suspects of that anomaly in one transaction and enqueues one `SUGGESTION_GENERATION` job per suspect.

## 4. Suggested Resolution — `modules/suggestions` + `cic_ai` (`src/ai`)

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

`EvidenceValidator` rules:

| Input | Result |
|---|---|
| Cause statement with no evidence, or evidence that is not in the bundle | Removed |
| No cause statement left | `status = NO_SUPPORT` (screen: "No supported suggestion") |
| Step citing a rollback plan, past incident, or guideline from the bundle | `basis = STANDARD` |
| Step without valid evidence | `basis = LLM_KNOWLEDGE` |
| Any statement | `label = HYPOTHESIS` at creation; only `SuggestionService.decide` sets `CONFIRMED`, and only when every statement is `STANDARD` |

## 5. Shared enums

| Enum | Values |
|---|---|
| `UserRole` | ADMIN, IT_MANAGER, CHANGE_ENGINEER, AGENT |
| `ScoreFactor` | TIME_PROXIMITY, SCOPE_MATCH, CATEGORY_KEYWORD_MATCH, ANOMALY_MAGNITUDE, CHANGE_RISK |
| `Severity` | HIGH, MEDIUM, LOW |
| `StatementBasis` | STANDARD, LLM_KNOWLEDGE |
| `SuggestionStatus` | PENDING, READY, NO_SUPPORT, FAILED |
| `SuggestionLabel` | CONFIRMED, HYPOTHESIS |

Python enums mirror the PostgreSQL enums in `cic.sql` one-to-one.

## 6. Mapping boundaries

- `router` ↔ Pydantic schemas only; never SQLAlchemy models.
- `service` ↔ Protocols and plain dataclasses; maps models to schemas before returning.
- `repository` ↔ SQLAlchemy models and the session; commits are owned by the request (API) or the job (worker).
