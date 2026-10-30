# Plan — M4 Detection and ranking

- **Goal:** CIC detects ticket spikes against the baseline and ranks recent changes as explained suspects.
- **Depends on:** M3 (changes and tickets exist)
- **Docs:** [09-algorithms.md](../../docs/09-algorithms.md), [C4 L4.1 Suspect Ranking](../../docs/architecture/c4/04-code.md), [class diagrams §3](../../docs/architecture/uml/01-class-diagrams.md), [sequence §4, §6](../../docs/architecture/uml/02-sequence-diagrams.md), [ai-pipeline.md ③](../../docs/architecture/ai-pipeline.md)

## M4-1 SCR-40 Baseline

| Field | Value |
|---|---|
| Stories / AC | US10, US11 · AC-UC11, AC-UC12 |
| Rules / NFR | BR-009, BR-020, BR-021 · NFR-REL-002 |
| API | `GET /baselines`, `POST /baselines/recompute` |
| Tables | `baseline_runs`, `baseline_cells`, `jobs`, `settings` |
| Design | 09-algorithms §2 |
| Backend modules | `baseline`, `jobs`, `worker.py` (job `BASELINE_RECOMPUTE`) |
| Frontend | `(workspace)/baseline`, `features/baseline`; chart baseline vs actual (recharts via `next/dynamic`) |

**Backend**
- [ ] `jobs` module: create, claim with row lock, retry ≤ 3, two workers never run one job
- [ ] Worker loop with poll interval and last-job heartbeat
- [ ] Baseline per category × weekday × hour (optional department/branch), zeros for empty hours, ≥ 3 weeks or category-only fallback, exclude resolved anomaly ranges
- [ ] Latest `SUCCEEDED` run is active; failed run never replaces it
- [ ] Recompute on demand (IT Manager, Admin) and on schedule; audit event

**Frontend**
- [ ] Filters by category and group; chart and table; recompute button with progress

**Tests**
- [ ] Algorithm unit tests with the 09-algorithms examples; concurrency of job claim; role check

**Done when:** AC-UC11 and AC-UC12 pass.

**Open:** Q-04 (organization time zone).

## M4-2 Detection and ranking (worker)

| Field | Value |
|---|---|
| Stories / AC | US12 (system part) · AC-UC13 |
| Rules / NFR | BR-010, BR-011, BR-012, BR-016 · NFR-TIME-001, NFR-TIME-002, NFR-MAINT-001 (≥ 90% `SuspectScorer`) |
| API | — |
| Tables | `anomalies`, `anomaly_tickets`, `suspects`, `suspect_factors`, `jobs`, `settings` |
| Design | 09-algorithms §3–§4, §6 edge cases; sequence §4 |
| Backend modules | `anomalies` (`AnomalyDetectionService`, `SuspectScorer`), `jobs`, worker (`ANOMALY_DETECTION`) |

**Backend**
- [ ] Detection every interval: z-test, severity, no duplicates, store and link tickets
- [ ] Candidates inside the tracing window; five factors in [0, 1]; weighted score 0–100 and level
- [ ] Suspects committed before any LLM work; rerun rules from 09-algorithms §4.4

**Tests**
- [ ] Printer worked example (09-algorithms §5) reproduces exactly
- [ ] Every edge case in 09-algorithms §6; weights from settings

**Done when:** AC-UC13 passes with seeded data; anomaly and suspects are stored within NFR-TIME limits.

## M4-3 SCR-10 Anomaly list

| Field | Value |
|---|---|
| Stories / AC | US12 · AC-UC14 |
| Rules / NFR | BR-001 · NFR-PERF-001 |
| API | `GET /anomalies` |
| Tables | `anomalies` |
| Backend modules | `anomalies` |
| Frontend | `(workspace)/anomalies`, `features/anomalies` |

**Tasks**
- [ ] Backend list with filters (status, severity, group, time) and paging
- [ ] Frontend table; severity shown as text and color; empty state
- [ ] Tests for filters and roles

**Done when:** all roles see open anomalies with filters.

## M4-4 SCR-11 Anomaly detail — suspects

| Field | Value |
|---|---|
| Stories / AC | US12, US13, US14 · AC-UC14, AC-UC15 |
| Rules / NFR | BR-001, BR-021 · NFR-PERF-003 |
| API | `GET /anomalies/{anomalyId}`, `GET /anomalies/{anomalyId}/suspects`, `GET /anomalies/{anomalyId}/tickets`, `GET /anomalies/{anomalyId}/timeline`, `POST /suspects/{suspectId}/feedback` |
| Tables | `anomalies`, `suspects`, `suspect_factors`, `anomaly_tickets`, `suspect_feedback`, `changes`, `audit_logs` |
| Design | Sequence §6; IA state "No suspect" |
| Backend modules | `anomalies`, `changes` (through its service) |
| Frontend | `(workspace)/anomalies/[anomalyId]`; suspects with factor explanations, rollback plan and implementer, tickets, timeline, feedback |

**Tasks**
- [ ] Backend detail, suspects with per-factor explanation, tickets, timeline
- [ ] Feedback `CORRECT_CAUSE` / `UNRELATED` with note; audit event
- [ ] Frontend: score number + High/Medium/Low label; open suspect shows rollback plan and implementer; "No suspect found" state
- [ ] Tabs placeholders for related logs and suggestion (filled in M5)
- [ ] Tests for roles, feedback, empty states

**Done when:** AC-UC14 and AC-UC15 pass.

## M4-5 SCR-02 Dashboard

| Field | Value |
|---|---|
| Stories / AC | US03 · AC-UC03 |
| Rules / NFR | BR-020 · NFR-PERF-003 |
| API | `GET /dashboard` |
| Tables | read through `anomalies`, `tickets`, `baseline` services |
| Backend modules | `dashboard` |
| Frontend | `(workspace)/dashboard`; open anomalies, tickets vs baseline chart, top suspects |

**Tasks**
- [ ] Backend aggregate through other module services only
- [ ] Frontend date range and group filter; chart loaded with `next/dynamic`
- [ ] Tests for filters and empty state

**Done when:** AC-UC03 passes within NFR-PERF-003.
