# Target folder structure

> Design status: TARGET V1 · Agreed structure, no application code yet

Frontend: **Next.js 16 (App Router) + React 19 + TypeScript**. Backend: **Python + FastAPI**, organized by **module**, with a separate **AI** package. The Backend API and the Analysis Worker share one codebase and one Docker image (see [C2 — Container](architecture/c4/02-container.md)).

## 1. Repository

```text
practise/
├── src/
│   ├── frontend/                 # Next.js 16 + React 19 (Web Frontend)
│   ├── backend/                  # FastAPI API + Analysis Worker, one codebase
│   └── database/
│       └── cic.sql               # PostgreSQL schema (becomes the first migration)
├── docs/
│   ├── api/                      # OpenAPI contract and API documentation
│   ├── architecture/c4/          # C1–C3
│   ├── 01-scope.md … 07-folder-structure.md
│   ├── DATABASE.md
│   └── mindmap.png
├── .gitignore                    # Ignores .env files, keeps .env.example
└── README.md
```

## 2. Frontend — Next.js 16 + React 19

```text
src/frontend/
├── app/                          # App Router: one route per screen in the IA
│   ├── (public)/login/           # SCR-01
│   ├── (workspace)/              # Shell (sidebar + topbar), requires login
│   │   ├── layout.tsx
│   │   ├── dashboard/            # SCR-02
│   │   ├── anomalies/            # SCR-10
│   │   │   └── [anomalyId]/      # SCR-11: suspects, tickets, logs, timeline, suggestion
│   │   ├── changes/              # SCR-20–22
│   │   ├── tickets/              # SCR-30
│   │   │   └── import/           # SCR-31
│   │   ├── baseline/             # SCR-40
│   │   ├── audit/                # SCR-50
│   │   ├── settings/             # SCR-60
│   │   ├── users/                # SCR-70
│   │   └── profile/              # SCR-80
│   ├── forbidden/                # SCR-90
│   └── layout.tsx
├── features/                     # Business logic per area; routes only compose it
│   ├── auth/  dashboard/  anomalies/  suggestions/  changes/  tickets/
│   ├── baseline/  audit/  settings/  users/  profile/
│   │   └── (each: components/, hooks/, api.ts)
├── components/                   # Shared UI: tables, forms, modals, skeletons, score labels
├── lib/
│   ├── api-client.ts             # Adds the JWT, handles 401/403, reads problem+json
│   ├── api-types.ts              # Generated from docs/api/openapi.yaml
│   └── format.ts                 # Dates, times, time zones
├── proxy.ts                      # Redirects by login state and role (Next.js 16 name for middleware)
├── tests/
├── .env.example
└── package.json
```

Dependency flow:

```text
app/ route → features/<area>/components → features/<area>/hooks → features/<area>/api.ts → lib/api-client.ts → REST API
```

Rules:

- Next.js is the frontend only; it holds no business rules and never talks to the database or the LLM.
- Hiding a control is UI only; the backend enforces every permission.
- `NEXT_PUBLIC_*` variables reach the browser, so they never contain secrets.

## 3. Backend — Python + FastAPI, by module

```text
src/backend/
├── app/
│   ├── main.py                   # Creates the FastAPI app, includes api_router
│   ├── worker.py                 # Background loop: claims jobs, calls module services and ai/
│   ├── api_router.py             # Collects every module router under /api/v1
│   ├── core/                     # Shared
│   │   ├── config.py             # Reads .env
│   │   ├── database.py           # Engine, session
│   │   ├── security.py           # JWT, password hashing, API-key hashing
│   │   ├── container.py          # Composition root: binds interfaces to implementations
│   │   ├── deps.py               # Depends(): session, current user, role checks
│   │   └── errors.py             # Errors → problem+json
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/                # Users + profile
│   │   ├── settings/             # Settings + lookups
│   │   ├── changes/
│   │   ├── tickets/              # Tickets + import
│   │   ├── logs/                 # Error-log intake, masking, classification
│   │   ├── integration/          # ITSM / Log Source endpoints → tickets, changes, logs services
│   │   ├── baseline/
│   │   ├── anomalies/            # Anomalies, suspects, scoring, feedback
│   │   ├── suggestions/          # Read and confirm suggested resolutions
│   │   ├── dashboard/
│   │   ├── audit/
│   │   └── jobs/                 # Job table: API creates jobs, worker claims them
│   └── ai/                       # Separate AI package
│       ├── interfaces.py         # Protocol: LLMClient
│       ├── llm_client.py         # Calls the LLM provider
│       ├── masking.py            # Masks sensitive data before sending
│       ├── evidence_collector.py
│       ├── generator.py          # Drafts cause and resolution
│       └── validator.py          # Checks evidence, sets Standard/Hypothesis
├── tests/
│   ├── fakes/                    # In-memory repositories and LLMClient
│   ├── modules/                  # Tests per module
│   └── ai/
├── alembic/                      # Migrations; the first one is cic.sql
├── .env.example
├── requirements.txt
└── Dockerfile                    # One image, run as `api` or `worker`
```

### Inside a module (example: `modules/changes/`)

```text
changes/
├── router.py                     # Controller: endpoints, calls the service, exposed through api_router
├── service.py                    # Business logic; depends only on the repository interface
├── repository.py                 # Protocol ChangeRepository + SQLAlchemy implementation
├── models.py                     # SQLAlchemy models of this module
├── schemas.py                    # Pydantic request/response
└── dependencies.py               # Depends() that builds the service with an injected repository
```

### Dependency flow

```text
api_router → module/router → module/service → module/repository (interface) → PostgreSQL
worker     → module/service or ai/          → repository                     → PostgreSQL
ai/generator → LLMClient (interface) → llm_client → LLM provider
```

### Rules

- A module calls another module only through its **service**, never its repository (for example, `integration` calls `tickets.service`).
- A **service depends on interfaces** (repository Protocols, `LLMClient`); implementations are bound in `core/container.py`. Tests replace them with `tests/fakes/`.
- `ai/` has no router: users read results through the `suggestions` module; the worker calls `ai/` to draft them.
- The suspicion score is computed in `modules/anomalies/service.py` before `ai/` runs, so it never depends on the LLM.
- Only `ai/llm_client.py` talks to the LLM provider, and only after `ai/masking.py`.

### Module ownership

| Module | Tables | API tags |
|---|---|---|
| auth | — (uses `app_users`) | Auth |
| users | `app_users` | Users, Profile |
| settings | `settings`, `departments`, `branches`, `software`, `device_groups`, `categories` | Settings, Lookups |
| changes | `changes`, `change_*` scope tables | Changes |
| tickets | `tickets`, `import_batches` | Tickets, Ticket imports |
| logs | `error_logs` | (used by integration and anomalies) |
| integration | `api_clients` | Integration |
| baseline | `baseline_runs`, `baseline_cells` | Baseline |
| anomalies | `anomalies`, `anomaly_tickets`, `anomaly_logs`, `suspects`, `suspect_factors`, `suspect_feedback` | Anomalies |
| suggestions | `suggestions`, `suggestion_statements`, `statement_evidence`, `guidelines` | Suggestions |
| dashboard | — (reads other modules through their services) | Dashboard |
| audit | `audit_logs` | Audit |
| jobs | `jobs` | — |

## 4. Environment variables

Templates: [`src/backend/.env.example`](../src/backend/.env.example) and [`src/frontend/.env.example`](../src/frontend/.env.example). Copy to `.env` / `.env.local`; these real files are ignored by Git.

| Variable | Used by | Purpose |
|---|---|---|
| `APP_ENV`, `API_HOST`, `API_PORT`, `LOG_LEVEL`, `CORS_ORIGINS` | API | Runtime settings |
| `DATABASE_URL`, `DATABASE_SCHEMA` | API, worker | PostgreSQL connection |
| `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` | API | User authentication |
| `FILE_STORAGE_DIR`, `IMPORT_MAX_FILE_MB`, `IMPORT_MAX_ROWS` | API | Ticket import files and limits |
| `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES` | Worker | LLM provider |
| `WORKER_ID`, `WORKER_POLL_INTERVAL_SECONDS` | Worker | Job polling |
| `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_NAME` | Frontend | API address, app name |

Business thresholds (anomaly threshold, tracing window, weights, log retention) live in the `settings` table so an Administrator can change them without a redeploy.
