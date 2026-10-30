# Screens — single source of truth for build work

Every unit of work is one YAML file in this folder: a **screen** (frontend feature + backend modules) or a non-screen **slice** (platform, API-only, worker, AI package, verification). All files share one schema, so every screen is planned, built, and checked the same way.

- `/implement <ID>` reads `<ID>.yaml` first ([.claude/skills/implement/SKILL.md](../../.claude/skills/implement/SKILL.md)).
- `python project/tools/check_screens.py` validates every file against the docs and regenerates [tracker.md](../tracker.md).
- Nothing else in `project/` repeats this data; [roadmap.md](../roadmap.md) holds milestone goals and exits, [backlog.md](../backlog.md) holds story text and priority.

## Build order

| Track | Order |
|---|---|
| main | PLT-1 → PLT-2 → PLT-3 → PLT-4 → SCR-01 → SCR-90 → SCR-80 → SCR-70 → SCR-60 → SCR-20 → SCR-30 → SCR-31 → API-ITSM → SCR-40 → JOB-DETECT → SCR-10 → SCR-11.1 → SCR-02 → API-LOGS → SCR-11.2 → SCR-11.3 → SCR-50 → NFR-VERIFY |
| ai | AI-1 → AI-2 → AI-3 → AI-4 (joins main at API-LOGS and SCR-11.3) |

## Schema

| Key | Required | Value |
|---|---|---|
| `id` | yes | Same as the file name: `PLT-n`, `SCR-nn`, `SCR-nn.n`, `API-*`, `JOB-*`, `AI-n`, `NFR-*` |
| `kind` | yes | `screen` · `platform` · `api` · `worker` · `ai` · `verification` |
| `name` | yes | Short name |
| `track` | yes | `main` or `ai` |
| `milestone` | yes | `M0` … `M6` or `AI` |
| `order` | yes | Unique build position inside the track |
| `depends_on` | yes | Item ids that must be `done` first |
| `status` | yes | `todo` · `in_progress` · `review` · `done` · `blocked` |
| `covers` | screen | IA screen ids this item delivers (`SCR-20`, `SCR-21`, `SCR-22`) |
| `route` | screen | Folder under `src/frontend/app/` |
| `presentation` | screen | As in the IA screen inventory |
| `roles` | yes | Action → roles. Roles: `PUBLIC`, `ADMIN`, `IT_MANAGER`, `CHANGE_ENGINEER`, `AGENT`, `ITSM`, `LOG_SOURCE`, `WORKER`; suffix `:own` limits to own records |
| `stories` | yes | `US*` ids from [05-invest-requirements.md](../../docs/05-invest-requirements.md) |
| `acceptance` | yes | `AC-UC*` ids from [08-acceptance-criteria.md](../../docs/08-acceptance-criteria.md) |
| `rules` | yes | `BR-*` ids from [business-rules.md](../../docs/requirements/business-rules.md) |
| `nfr` | yes | `NFR-*` ids from [non-functional-requirements.md](../../docs/requirements/non-functional-requirements.md) |
| `docs` | yes | Repository paths (anchors allowed) to read before coding |
| `frontend.feature` | screen | Folder under `src/frontend/features/`, or `null` |
| `frontend.components` | screen | PascalCase component names |
| `frontend.hooks` | screen | TanStack Query hooks: `use<Entities>` list, `use<Entity>` detail, `useCreate*`, `useUpdate*`, verbs for actions |
| `frontend.states` | screen | From the state vocabulary below |
| `frontend.shared` | no | Shared files under `src/frontend/` |
| `backend.modules` | yes | Folders under `src/backend/app/modules/` |
| `backend.shared` | no | Shared files under `src/backend/` |
| `backend.api` | yes | `METHOD /path` exactly as in [openapi.yaml](../../docs/api/openapi.yaml) |
| `backend.tables` | yes | Tables in [cic.sql](../../src/database/cic.sql) |
| `backend.jobs` | yes | `job_type` values in cic.sql |
| `ai.modules` / `ai.cli` / `ai.datasets` / `ai.metrics` | ai | Parts of [`cic_ai`](../../docs/architecture/ai-package.md); metric ids `M-*` |
| `tasks.backend` / `tasks.frontend` / `tasks.ai` / `tests` | yes | Strings starting with `[ ]` or `[x]` |
| `done_when` | yes | Observable results that close the item |
| `skills_used` | yes | Skills actually loaded while building the item (`name` or `plugin:name`), filled in by `/implement`; required once status is `review` or `done` |
| `open` | yes | `Q-*` / `I-*` ids from [risks-and-questions.md](../risks-and-questions.md) that shape the item |

## State vocabulary

From the [UI/UX state contract](../../docs/04-information-architecture.md#uiux-state-contract): `loading`, `empty`, `filtered-empty`, `no-suspect`, `no-suggestion`, `no-related-logs`, `suggestion-label`, `masked-data`, `validation-error`, `api-error`, `unauthorized`, `forbidden`, `conflict`, `saving`, `success`.

## Checks run by `check_screens.py`

| Check | Fails when |
|---|---|
| Schema | A required key is missing, a value is outside its vocabulary, or `id` differs from the file name |
| Order | Two items share an order in a track; a dependency is missing, later in order, or forms a cycle |
| Status | `done` with an unticked task; `in_progress`/`done` while a dependency is not `done`; `review`/`done` with an empty `skills_used` |
| Docs ids | A story, AC, BR, NFR, metric, question, or IA screen id does not exist in the docs |
| Contract | An API path is not in openapi.yaml, a table or job type is not in cic.sql, a module or feature is not in 07-folder-structure.md, a doc path does not exist |
| Coverage | A user story, OpenAPI operation, table, IA screen, or backend module is not covered by any item |
