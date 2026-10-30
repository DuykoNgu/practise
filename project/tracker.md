# Screen tracker — CIC V1

One row per plan item ([plans/](plans/README.md)), in build order. `/implement <ID>` works on one row. Update the row in the same commit that moves the work forward. Legend: [README](README.md#status-legend).

| ID | Item | Milestone | Backend | Frontend | Tests | A11y | Done | Notes |
|---|---|---|---|---|---|---|---|---|
| [M0-1](plans/m0-platform.md) | Backend core | M0 | ⬜ | — | ⬜ | — | ⬜ | |
| [M0-2](plans/m0-platform.md) | Database migration and seed | M0 | ⬜ | — | ⬜ | — | ⬜ | |
| [M0-3](plans/m0-platform.md) | Frontend foundation and shell | M0 | — | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M0-4](plans/m0-platform.md) | CI and Docker | M0 | — | — | ⬜ | — | ⬜ | |
| [M1-1](plans/m1-access.md) | SCR-01 Login + logout | M1 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M1-2](plans/m1-access.md) | SCR-90 Forbidden | M1 | — | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M1-3](plans/m1-access.md) | SCR-80 Profile | M1 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M2-1](plans/m2-administration.md) | SCR-70 Users | M2 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M2-2](plans/m2-administration.md) | SCR-60 Settings | M2 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M3-1](plans/m3-data-intake.md) | SCR-20–22 Changes | M3 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M3-2](plans/m3-data-intake.md) | SCR-30 Tickets | M3 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M3-3](plans/m3-data-intake.md) | SCR-31 Ticket import | M3 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M3-4](plans/m3-data-intake.md) | ITSM integration (API) | M3 | ⬜ | — | ⬜ | — | ⬜ | |
| [M4-1](plans/m4-detection.md) | SCR-40 Baseline | M4 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M4-2](plans/m4-detection.md) | Detection and ranking (worker) | M4 | ⬜ | — | ⬜ | — | ⬜ | |
| [M4-3](plans/m4-detection.md) | SCR-10 Anomaly list | M4 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M4-4](plans/m4-detection.md) | SCR-11 Anomaly detail — suspects | M4 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M4-5](plans/m4-detection.md) | SCR-02 Dashboard | M4 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M5-1](plans/m5-ai-evidence.md) | Log intake (API) | M5 | ⬜ | — | ⬜ | — | ⬜ | |
| [M5-2](plans/m5-ai-evidence.md) | SCR-11 Related logs | M5 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M5-3](plans/m5-ai-evidence.md) | SCR-11 Suggestion + confirm | M5 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M6-1](plans/m6-audit-hardening.md) | SCR-50 Audit log | M6 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
| [M6-2](plans/m6-audit-hardening.md) | NFR verification | M6 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |

## AI track

Columns: Code, Tests (`pytest`), Evals (`cic-ai eval` bars), Done.

| Phase | Item | Code | Tests | Evals | Done | Notes |
|---|---|---|---|---|---|---|
| [A1](plans/ai-package.md#a1--package-and-masking) | Package + masking | ⬜ | ⬜ | ⬜ | ⬜ | |
| [A2](plans/ai-package.md#a2--classification) | Classification | ⬜ | ⬜ | ⬜ | ⬜ | |
| [A3](plans/ai-package.md#a3--suggestion-pipeline-in-stub-mode) | Suggestion pipeline (stub) + CI | ⬜ | ⬜ | ⬜ | ⬜ | |
| [A4](plans/ai-package.md#a4--live-mode-and-baseline) | Live mode + baseline | ⬜ | ⬜ | ⬜ | ⬜ | Needs Q-02, Q-08, Q-09 |

## Progress

| Milestone | Rows | Done |
|---|---|---|
| M0 | 4 | 0 |
| M1 | 3 | 0 |
| M2 | 2 | 0 |
| M3 | 4 | 0 |
| M4 | 5 | 0 |
| M5 | 3 | 0 |
| M6 | 2 | 0 |
| AI track | 4 | 0 |
| **Total** | **27** | **0** |
