# Risks and open questions — CIC V1

## Open questions

| ID | Question | Blocks | Owner | Status |
|---|---|---|---|---|
| Q-01 | Team size, sprint length, and target date for V1? | Dates in roadmap and sprints | Product owner | Open |
| Q-02 | Which LLM model and budget for suggestions (`LLM_MODEL`)? | M5 | Product owner | Open |
| Q-03 | Exact ITSM payload mapping for the target ITSM product (fields, status values)? | US19 (M3) | Integration owner | Open |
| Q-04 | Organization time zone used for baseline weekday/hour (BR-020)? | M4 | Product owner | Open |
| Q-05 | Which plugins replace the current skills in `CLAUDE.md` §2 (py-pit, lattice, design-drift) and which design style (Linear, Vercel, other)? | M0 UI shell | Product owner | Open |
| Q-06 | Where is V1 deployed (on-prem VM, cloud, container platform) and who runs backups (NFR-BCP-001)? | M6 | Operations | Open |
| Q-07 | Is a seeded demo dataset (8 weeks of tickets) needed for review demos? | M4 exit | Product owner | Open |
| Q-08 | Approve the new `LLM_EFFORT` environment variable (default `medium`)? | A4 | Product owner | Open |
| Q-09 | Confirm the proposed eval bars (M-CLS-01 ≥ 0.85, M-SUG-05 ≥ 0.80, M-SUG-06 ≥ 0.70, latency p95 ≤ 60 s) after the first live baseline? | A4 | Product owner | Open |
| Q-10 | Who labels the gold suggestion cases (IT Manager review)? | A3 | Product owner | Open |
| Q-11 | F09 lists managing categories and department/branch/software mappings, but openapi.yaml only has `GET /lookups`. Seed-only in V1, or add endpoints? | M0-2, M2-2 | Product owner | Open |
| Q-12 | How are ITSM and log-source API clients created and rotated (no endpoint)? Seed/CLI script? | M0-2, M3-4 | Product owner | Open |
| Q-13 | How are guidelines created (no endpoint)? Seed/CLI script? | M5-3 | Product owner | Open |
| Q-14 | Health endpoint required by NFR-OBS-001 is not in openapi.yaml. Add `GET /health` outside `/api/v1`? | M0-1 | Tech lead | Open |
| Q-15 | Where is the failed-login counter for NFR-SEC-003 stored (database table or in-process)? | M1-1 | Tech lead | Open |

## Doc inconsistencies

| ID | Where | Issue | Suggested fix |
|---|---|---|---|
| I-01 | [05-invest-requirements.md](../docs/05-invest-requirements.md) per-story review | US08, US10, US12, US16, US19, US20, US22, US23 are still `PARTIAL`, but limits, ranges, algorithms, and the AI pipeline are now defined (BR-006, BR-007, BR-009, BR-019, 09-algorithms.md, ai-pipeline.md). | Re-review and set to `PASS` where resolved. |
| I-02 | [02-features.md](../docs/02-features.md) F06 | Says the formula "is defined in the algorithm design phase"; it now exists. | Link to 09-algorithms.md §4. |
| I-03 | [04-information-architecture.md](../docs/04-information-architecture.md) | "No UI exists yet" will be stale after M1. | Update when SCR-01 ships. |
| I-04 | IA routes vs [07-folder-structure.md](../docs/07-folder-structure.md) | IA uses route `/403`; folder structure uses `app/forbidden/`. | Pick one before M1-2. |
| I-05 | `CLAUDE.md` screen table | SCR-31 lists backend module `jobs`, but NFR-IMPORT-001 makes import synchronous. | Drop `jobs` from SCR-31 unless async import is wanted. |
| I-06 | [cic.sql](../src/database/cic.sql) `job_type` | BR-018 needs a scheduled log-retention cleanup, but `job_type` has no value for it. | Add a job type or run cleanup inside another job; decide before M5-1. |

## Risks

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | Not enough ticket history to build a reliable baseline (BR-009 needs ≥ 3 weeks per cell). | Medium | High | Category-only fallback; seed demo data; show "insufficient history" state. | Backend |
| R-02 | Suspect ranking accuracy below NFR-AI-004 target (top 3 ≥ 70%). | Medium | High | Feedback loop (US14), tunable weights (US16), monthly quality report. | Product |
| R-03 | Sensitive data leaks to the LLM. | Low | High | Masking before storage and LLM (BR-008), test corpus ≥ 500 lines (NFR-PRIV-001), captured-prompt tests. | Backend |
| R-04 | LLM outage or latency delays suggestions. | Medium | Medium | Ranking independent of LLM (BR-016); retries; `FAILED` status shown in UI. | Backend |
| R-05 | Worker job duplication under concurrency. | Low | Medium | Row-level claim in `jobs`, retry limit 3 (NFR-REL-002), concurrency test. | Backend |
| R-06 | Dependency churn (Next.js 16, Tailwind 4, TanStack Table 9, pandas 3 are recent majors). | Medium | Medium | Pinned versions, lockfile, CI on every push, upgrade one major at a time. | Tech lead |
| R-07 | Scope creep beyond V1 (chatbot, auto-rollback, log platform). | Medium | Medium | Non-goals in [01-scope.md](../docs/01-scope.md); `CLAUDE.md` §3. | Product |
| R-08 | Performance targets missed at capacity (200k tickets, 2M logs). | Medium | Medium | Indexes from 06-data-model.md, paginated APIs, load tests in M6 earlier for heavy queries. | Backend |
| R-09 | Live evals add LLM cost on every run. | Medium | Low | Stub mode by default and in CI; `--limit`; cost printed per run; live runs need approval. | AI |
| R-10 | Contract drift between `cic_ai.EvidenceBundle` and the backend `EvidenceCollector`. | Medium | Medium | Single model in `cic_ai.evidence`; backend tests build bundles with it. | Backend |
