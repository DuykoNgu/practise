# Plan — M5 AI evidence

- **Goal:** error logs become evidence on the anomaly detail screen, and every suspect gets an evidence-grounded suggested resolution.
- **Depends on:** M4, and AI track A1–A4 ([ai-package.md](ai-package.md)); this milestone is phase A5
- **Docs:** [ai-pipeline.md](../../docs/architecture/ai-pipeline.md), [ai-package.md](../../docs/architecture/ai-package.md), [C4 L4.2](../../docs/architecture/c4/04-code.md), [class diagrams §4](../../docs/architecture/uml/01-class-diagrams.md), [sequence §3, §5, §7](../../docs/architecture/uml/02-sequence-diagrams.md), [02-features.md F12, F13](../../docs/02-features.md)

## M5-1 Log intake (API only)

| Field | Value |
|---|---|
| Stories / AC | US22 · AC-UC22 |
| Rules / NFR | BR-007, BR-008, BR-018 · NFR-PERF-004, NFR-CAP-003, NFR-PRIV-001, NFR-SEC-005 |
| API | `POST /integration/logs` (`X-API-Key`, kind `LOG_SOURCE`) |
| Tables | `error_logs`, `api_clients`, `jobs` |
| Design | Sequence §3 |
| Backend modules | `logs`, `integration`, worker (`LOG_CLASSIFICATION`); uses `cic_ai.masking`, `cic_ai.classification` |

**Backend**
- [ ] Backend depends on `cic-ai`; `anthropic` removed from `src/backend/requirements.txt`; Docker context includes `src/ai`
- [ ] Mask before insert; raw message never stored; duplicates by `externalId`; `202` with counts
- [ ] Map device group to department and branch
- [ ] `LOG_CLASSIFICATION` job sets signature and category
- [ ] Retention cleanup by `logRetentionDays` (see Open)

**Tests**
- [ ] Key checks; batch limit; duplicates; masking applied; classification job; 1,000-log timing

**Done when:** AC-UC22 passes.

**Open:** I-06 (no `job_type` value for retention cleanup).

## M5-2 SCR-11 Related logs

| Field | Value |
|---|---|
| Stories / AC | US23 · AC-UC23 |
| Rules / NFR | BR-018 · NFR-PERF-003 |
| API | `GET /anomalies/{anomalyId}/logs` |
| Tables | `anomaly_logs`, `error_logs` |
| Backend modules | `anomalies` (linking in detection, F13.4), `logs` |
| Frontend | Related-logs tab on SCR-11 |

**Tasks**
- [ ] Link logs to anomalies by tracing window and scope during detection
- [ ] Endpoint groups by signature with count, level, first/last seen, masked sample
- [ ] Frontend tab with "No related logs" state; masked values shown as masked
- [ ] Tests for linking rules, grouping, retention

**Done when:** AC-UC23 passes.

## M5-3 SCR-11 Suggestion and confirmation

| Field | Value |
|---|---|
| Stories / AC | US20, US21 · AC-UC20, AC-UC21 |
| Rules / NFR | BR-013, BR-014, BR-015, BR-016, BR-017, BR-021 · NFR-AI-001, NFR-AI-002, NFR-AI-003, NFR-PRIV-002, NFR-TIME-003 |
| API | `GET /suspects/{suspectId}/suggestion`, `PUT /suspects/{suspectId}/suggestion/confirmation` |
| Tables | `suggestions`, `suggestion_statements`, `statement_evidence`, `guidelines`, `audit_logs` |
| Design | Sequence §5, §7; ai-pipeline §2 retrieval paths |
| Backend modules | `suggestions` (`EvidenceCollector`, `SuggestionService`, `SuggestionPolicy`), worker (`SUGGESTION_GENERATION`); uses `cic_ai.pipeline` |
| Frontend | Suggestion panel on SCR-11, `features/suggestions` |

**Backend**
- [ ] `EvidenceCollector` walks the five retrieval paths with limits and builds `cic_ai.EvidenceBundle`
- [ ] `SUGGESTION_GENERATION` job after suspects are stored; `FAILED` with retries on LLM error
- [ ] Store statements and evidence (log snapshots kept); status and label rules
- [ ] Confirm/reject by Admin, IT Manager, Change Engineer; Agent `403`; audit `SUGGESTION_DECISION`
- [ ] Confirmed suggestions offered as `PAST_INCIDENT` evidence later

**Frontend**
- [ ] Causes with evidence links; steps labeled Standard (with source) or Flexible; label Confirmed/Hypothesis
- [ ] "No supported suggestion" for `PENDING`, `FAILED`, `NO_SUPPORT`; confirm action hidden for Agents

**Tests**
- [ ] LLM stub failing leaves ranking unchanged; label rules; policy; audit; NFR-AI queries

**Done when:** AC-UC20 and AC-UC21 pass and `cic-ai eval suggestion` still passes.

**Open:** Q-02 (model), Q-13 (guideline management has no endpoint).
