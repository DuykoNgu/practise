# Plan — M0 Platform

- **Goal:** the minimum shared code that SCR-01 needs, plus CI. Nothing speculative.
- **Depends on:** —
- **Docs:** [07-folder-structure.md](../../docs/07-folder-structure.md), [C2 Container](../../docs/architecture/c4/02-container.md), [C3 Component](../../docs/architecture/c4/03-component.md), [non-functional-requirements.md](../../docs/requirements/non-functional-requirements.md), [sequence §8 error conventions](../../docs/architecture/uml/02-sequence-diagrams.md#8-common-error-conventions)

## M0-1 Backend core

| Field | Value |
|---|---|
| Rules / NFR | BR-020 (UTC), NFR-OBS-001, NFR-SEC-005 |
| API | Error format `application/problem+json` as in openapi.yaml; health check (see Open) |
| Tables | — |

**Backend**
- [ ] `app/main.py`, `app/api_router.py` mounting `/api/v1`
- [ ] `core/config.py` with pydantic-settings reading `src/backend/.env.example` variables
- [ ] `core/database.py` (SQLAlchemy 2 engine and session, schema from `DATABASE_SCHEMA`)
- [ ] `core/errors.py`: domain errors → problem+json with trace id; no stack traces in responses
- [ ] `core/security.py`: JWT encode/decode (30 min, NFR-SEC-001), Argon2 hashing via pwdlib, API-key hashing
- [ ] `core/deps.py`: session, current user, role check, API-key client
- [ ] `core/container.py`: composition root
- [ ] Structured JSON logging with trace id; secrets never logged
- [ ] Health endpoint for API (see Open)

**Tests**
- [ ] Error mapping, JWT expiry, hashing, role check dependency

**Done when:** `uvicorn app.main:app` starts, health returns OK, ruff/mypy/pytest pass.

**Open:** Q-14 (health endpoint is not in openapi.yaml).

## M0-2 Database migration and seed

| Field | Value |
|---|---|
| Rules / NFR | BR-019 defaults, NFR-MAINT-002 |
| Tables | All of `cic.sql` |
| Design | [06-data-model.md](../../docs/06-data-model.md), [DATABASE.md](../../docs/DATABASE.md) |

**Backend**
- [ ] Alembic setup; first migration applies `src/database/cic.sql` unchanged
- [ ] Seed script: one Administrator, default `settings`, lookup data (categories with keywords, departments, branches, software, device groups)
- [ ] Seed or CLI to create API clients for ITSM and log source (see Open)

**Tests**
- [ ] Migration upgrade on an empty PostgreSQL 15+ database
- [ ] Seed is idempotent

**Done when:** `alembic upgrade head` + seed produce a working database; Administrator can be loaded by the auth repository.

**Open:** Q-11 (lookup management), Q-12 (API client management).

## M0-3 Frontend foundation and shell

| Field | Value |
|---|---|
| Rules / NFR | NFR-ACC-001, NFR-I18N-001, BR-020 |
| API | All paths through `lib/api-client.ts`; types from `npm run api:types` |
| Design | [IA: navigation, page permissions, UI/UX state contract](../../docs/04-information-architecture.md) |

**Frontend**
- [ ] `lib/api-types.ts` generated from openapi.yaml
- [ ] `lib/api-client.ts`: base URL, JWT header, 401 → clear session and go to login, 403 → forbidden page, problem+json parsing
- [ ] `lib/format.ts`: UTC in, viewer time zone out
- [ ] `proxy.ts`: redirect by login state and role
- [ ] `(workspace)/layout.tsx`: sidebar + topbar; unauthorized items not rendered
- [ ] Shared skeleton, empty state, and error components from shadcn/ui
- [ ] TanStack Query provider already in `app/providers.tsx`

**Tests**
- [ ] api-client handles 401, 403, problem+json
- [ ] Sidebar renders only permitted items per role

**Done when:** an authenticated placeholder page renders inside the shell with role-filtered navigation.

## M0-4 CI and Docker

| Field | Value |
|---|---|
| Rules / NFR | NFR-MAINT-002 |

**Tasks**
- [ ] CI workflow: backend ruff, mypy, pytest; frontend format, lint, typecheck, test, build; OpenAPI validation; migration check
- [ ] Add `src/ai` jobs when A1 lands (ruff, mypy, pytest, `cic-ai eval all` stub)
- [ ] `src/backend/Dockerfile`: one image, command `api` or `worker`
- [ ] Local compose for PostgreSQL, API, worker, web (development only)

**Done when:** CI is green on `main` and the image starts as `api` and `worker`.

**Open:** Q-06 (deployment target).
