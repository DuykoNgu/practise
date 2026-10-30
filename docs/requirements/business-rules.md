# Business Rules — CIC V1

> Design status: TARGET V1
>
> Implementation status: NOT STARTED

Each rule names where it comes from and where it is enforced. Numbers marked *configurable* are defaults stored in the `settings` table.

## Access

### BR-001 — Roles
- **Source:** `03-use-cases.md` · **Related:** all UCs
- **Rule:** The only V1 roles are `ADMIN`, `IT_MANAGER`, `CHANGE_ENGINEER`, `AGENT`. Each API operation lists its allowed roles in `x-roles`; the backend is authoritative.
- **Enforced in:** `core/deps.py`, module policies.

### BR-002 — Change ownership
- **Source:** UC06, AC-UC06
- **Rule:** A Change Engineer may edit or change the status of a change only when they are its implementer. Admin and IT Manager may edit any change.
- **Enforced in:** `ChangePolicy.ensure_can_edit`.

## Inputs

### BR-003 — Change scope
- **Source:** `01-scope.md`, AC-UC05
- **Rule:** A change names at least one scope value (department, branch, software, or device group). Scope names must exist in the lookup tables.
- **Enforced in:** `ChangeValidator`, `LookupService`.

### BR-004 — Rollback plan
- **Source:** `01-scope.md`, `cic.sql`
- **Rule:** If a rollback plan is marked available, its steps are required. Estimated minutes, when given, are ≥ 0.
- **Enforced in:** `ChangeValidator`, database CHECK.

### BR-005 — Atomic ticket import
- **Source:** AC-UC09, `cic.sql`
- **Rule:** An import stores every row or none. A failed batch has 0 imported rows.
- **Enforced in:** `TicketService` (one transaction), database CHECK.

### BR-006 — Import limits
- **Source:** `.env.example`, NFR-IMPORT-001
- **Rule:** CSV/Excel files are at most 10 MB and 5,000 data rows.
- **Enforced in:** `TicketService` before parsing completes.

### BR-007 — Idempotent integration
- **Source:** UC10, UC22, `cic.sql`
- **Rule:** Items from ITSM and log sources carry an `externalId`; the pair (client, `externalId`) is stored once. A batch holds at most 1,000 items. Only active API clients of the matching kind are accepted.
- **Enforced in:** `core/deps.py` (API key), unique constraint.

### BR-008 — Log masking
- **Source:** F13.2, AC-UC22
- **Rule:** User names, e-mail addresses, IP addresses, and file paths in a log message are replaced by `***` before the log is stored. The raw message is never stored and never sent to the LLM.
- **Enforced in:** `cic_ai.masking` (`src/ai`), called by `LogService.ingest`; measured by `cic-ai eval masking`.

## Detection

### BR-009 — Baseline
- **Source:** `01-scope.md`, `cic.sql`
- **Rule:** The baseline is the mean and standard deviation of ticket counts per category × weekday × hour (optionally per department or branch), over the last 8 weeks (*configurable*), excluding time ranges of resolved anomalies. Hours without tickets count as 0. A cell needs at least 3 weeks of history; otherwise the category-only cell is used. The latest `SUCCEEDED` run is active; a failed run never replaces it. Details: [09-algorithms.md §2](../09-algorithms.md#2-baseline).
- **Enforced in:** `BaselineService`.

### BR-010 — Anomaly
- **Source:** F05, AC-UC13
- **Rule:** A group is anomalous when its ticket count in the last 60 minutes is greater than `expected + threshold × sigma`, with threshold 3.0 (*configurable*) and `sigma = max(std_dev, √max(expected, 1))`. Severity: HIGH if z ≥ 2 × threshold, MEDIUM if z ≥ 1.5 × threshold, otherwise LOW. Details: [09-algorithms.md §3](../09-algorithms.md#3-anomaly-detection). Detection runs every 15 minutes (*configurable*). An anomaly names at least one group (category, department, branch, software).
- **Enforced in:** `AnomalyDetectionService`, database CHECK.

### BR-011 — Candidate changes
- **Source:** F06, AC-UC13
- **Rule:** A change is a candidate for an anomaly when `start_at` is within the tracing window before `anomaly.start_at` (48 hours, *configurable*) and its status is not `SCHEDULED`.
- **Enforced in:** `SuspectRankingService`.

## Ranking

### BR-012 — Suspicion score
- **Source:** F06, class diagram 3
- **Rule:** Each of the five factors (time proximity, scope match, category/keyword match, anomaly magnitude, change risk) is a value in [0, 1]. `score = round(100 × Σ(weightᵢ × factorᵢ) / Σ weightᵢ)`, weights *configurable*. If scope match and category/keyword match are both 0, the score is capped at 39 (relevance gate). Keywords match whole words or phrases only. Level: High ≥ 70, Medium ≥ 40, otherwise Low. Ranks are 1..n by descending score; ties are broken by the later `start_at`. Factor formulas: [09-algorithms.md §4](../09-algorithms.md#4-suspect-ranking). Each factor stores its contribution and a human-readable explanation.
- **Enforced in:** `SuspectScorer` (pure), database CHECK (0–100, unique rank).

## AI suggestion

### BR-013 — Evidence for causes
- **Source:** F12.3
- **Rule:** Every cause statement cites at least one evidence item from the suspect's evidence bundle (log, ticket, change, rollback plan, past confirmed incident, or guideline). A cause without valid evidence is removed. If no cause remains, the suggestion is `NO_SUPPORT`.
- **Enforced in:** `EvidenceValidator`, database CHECK (cause basis is `STANDARD`).

### BR-014 — Step basis
- **Source:** F12.4
- **Rule:** A step that cites a rollback plan, past confirmed incident, or guideline is `STANDARD`. A step without valid evidence is `LLM_KNOWLEDGE` (shown as *Flexible*).
- **Enforced in:** `EvidenceValidator`.

### BR-015 — Label
- **Source:** F12.5
- **Rule:** A new suggestion is `HYPOTHESIS`. It becomes `CONFIRMED` only when a permitted person confirms it **and** every statement is `STANDARD`. Confirming a suggestion that contains a Flexible step records the decision but keeps the label `HYPOTHESIS`.
- **Enforced in:** `SuggestionService.decide`, database CHECK.

### BR-016 — Score independence
- **Source:** C4 C3.2, AC-UC13
- **Rule:** Suspects and scores are committed before any LLM call. The LLM never changes a score or a rank. An LLM failure marks the suggestion `FAILED` and retries up to 3 attempts.
- **Enforced in:** worker job order, `SuggestionService.generate`.

### BR-017 — Who decides
- **Source:** UC21
- **Rule:** Only Admin, IT Manager, and Change Engineer can confirm or reject a suggestion. Agents can read suggestions and give suspect feedback.
- **Enforced in:** `SuggestionPolicy.ensure_can_decide`.

## Data lifecycle and configuration

### BR-018 — Log retention
- **Source:** F13.7, `cic.sql`
- **Rule:** Error logs are deleted after 30 days (*configurable*, 1–365). Their links to anomalies are deleted with them; evidence keeps a masked snapshot.
- **Enforced in:** scheduled cleanup job, foreign keys.

### BR-019 — Settings ranges
- **Source:** `cic.sql`
- **Rule:** threshold > 0; tracing window 1–720 hours; baseline window 1–52 weeks; detection interval 1–1,440 minutes; log retention 1–365 days; weights ≥ 0 and not all 0.
- **Enforced in:** `SettingsService`, database CHECK.

### BR-020 — Time
- **Rule:** All times are stored and returned in UTC (ISO 8601 with offset) and displayed in the viewer's time zone. Baseline weekday and hour use the organization's time zone.
- **Enforced in:** API schemas, `lib/format.ts`.

### BR-021 — Audit
- **Rule:** Login, logout, create, update, status change, import, configuration change, feedback, suggestion decision, and baseline recompute write an audit event. Audit entries are never edited or deleted by the application.
- **Enforced in:** `AuditService`.
