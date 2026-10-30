# Agent rules

These rules apply to every coding task in this repository. They take precedence over habits and defaults.

## 1. Work screen by screen

- Build one screen at a time, in the order the user asks. A screen is done only when its frontend feature, backend module(s), and tests are all finished and passing.
- Before coding a screen, read its rows in [Information architecture](docs/04-information-architecture.md) (screen inventory, requirement-to-screen mapping, UI/UX state contract), the related use cases and user stories, and the matching paths in [docs/api/openapi.yaml](docs/api/openapi.yaml).
- Only touch the frontend feature and backend modules mapped to the current screen. If another module must change, ask the user first.

| Screen | Route (`src/frontend/app/`) | Frontend feature (`src/frontend/features/`) | Backend module (`src/backend/app/modules/`) |
|---|---|---|---|
| `SCR-01` Login | `(public)/login` | `auth` | `auth` |
| `SCR-02` Dashboard | `(workspace)/dashboard` | `dashboard` | `dashboard` |
| `SCR-10` Anomaly list | `(workspace)/anomalies` | `anomalies` | `anomalies` |
| `SCR-11` Anomaly detail | `(workspace)/anomalies/[anomalyId]` | `anomalies`, `suggestions` | `anomalies`, `suggestions`, `logs` |
| `SCR-20`–`SCR-22` Changes | `(workspace)/changes` | `changes` | `changes` |
| `SCR-30` Ticket list | `(workspace)/tickets` | `tickets` | `tickets` |
| `SCR-31` Ticket import | `(workspace)/tickets/import` | `tickets` | `tickets`, `jobs` |
| `SCR-40` Baseline | `(workspace)/baseline` | `baseline` | `baseline`, `jobs` |
| `SCR-50` Audit log | `(workspace)/audit` | `audit` | `audit` |
| `SCR-60` Settings | `(workspace)/settings` | `settings` | `settings` |
| `SCR-70` Users | `(workspace)/users` | `users` | `users` |
| `SCR-80` Profile | `(workspace)/profile` | `profile` | `users` |
| `SCR-90` Forbidden | `forbidden` | — | — |
| No screen (US19, US22) | — | — | `integration`, `logs` |

Shared code (`src/frontend/components/`, `src/frontend/lib/`, `src/backend/app/core/`, `src/backend/app/ai/`) is added only when the current screen needs it.

## 2. Use the matching skills

Backend (Python + FastAPI):

- Before writing a module: `backend-design:think-before-coding`.
- While writing: `backend-design:error-handling-as-design`, `backend-design:security-discipline`, `backend-design:auth-and-authorization`, `backend-design:query-discipline`.
- Schema or migration work: `backend-design:data-modeling-discipline`, `backend-design:migration-safety`.
- Tests: `backend-design:testing-with-discernment`.
- Python clean code: PEP 8, full type hints, small single-purpose functions, intention-revealing names, no dead code, no duplicated logic; formatted and linted with `ruff`, type-checked with `mypy`.
- Dependencies are pinned in `requirements.txt` (runtime) and `requirements-dev.txt` (tools); install with `pip install -r requirements-dev.txt`.

Frontend (Next.js 16 + React 19 + TypeScript):

- Layout and visual direction: `frontend-design:frontend-design`, `design-superpowers:design`.
- States and interactions: `design-skills:interaction-design`, following the UI/UX state contract.
- Labels, errors, empty states: `design-skills:ux-writing`.
- Before marking a screen done: `design-skills:accessibility-audit`.
- UI base is Tailwind CSS + shadcn/ui: add components with `npm run ui:add <name>`, style with Tailwind classes and the theme tokens in `app/globals.css`, merge classes with `cn()`.
- Research is encouraged to make the UI look better: shadcn-compatible registries and blocks, animation (for example `motion`), icon sets, or other UI libraries. A library may be added when it is built on or works with Tailwind, ships only what is imported, is actively maintained, and does not noticeably slow page load. Mention what was added and why in the commit message. Ask the user when several options are equally good or when a library would replace one already in use.
- Data is managed with TanStack: server data through `@tanstack/react-query` (`useQuery` / `useMutation` inside `features/<area>/hooks/`, keys per feature, invalidate the affected queries after a mutation), tables through `@tanstack/react-table`. Do not copy server data into `useState`, context, or another state library; local UI state stays in components.
- Keep pages light: Server Components by default, `"use client"` only where interaction needs it, heavy client parts (charts) loaded with `next/dynamic`.
- TypeScript clean code: `strict` mode, no `any`, small components, logic in `hooks/`, API calls only in `api.ts`; checked with `npm run lint`, `npm run typecheck`, `npm run format:check`, `npm test`.

Before every commit: `simplify`, then `code-review`.

## 3. Stay within the limits

- Implement only what the docs define for V1: [Scope](docs/01-scope.md), [Features](docs/02-features.md), [INVEST backlog](docs/05-invest-requirements.md). Never build anything listed under *Non-goals*.
- Follow the agreed structure and rules in [Folder structure](docs/07-folder-structure.md): the dependency flow, module boundaries (other modules only through their service), services depending on interfaces, and `ai/` rules.
- Follow the API contract in `docs/api/openapi.yaml` and the schema in `src/database/cic.sql`. Do not change either without asking the user.
- Do not add libraries, endpoints, tables, columns, screens, or settings that the docs do not define without asking the user.
- Do not refactor code outside the current screen.

## 4. Manage context

- Keep each session focused on one screen.
- When a screen is finished and committed, or when the context grows long, suggest `/compact` to the user before continuing.
- Keep a short progress note per screen in the commit message so work can resume after compaction.

## 5. Test and verify quality

- Write tests together with the code. Backend: `pytest` in `src/backend/tests/` (`modules/<module>/`, fakes from `tests/fakes/`). Frontend: tests in `src/frontend/tests/`.
- Cover the happy path, validation errors, 401, 403, conflicts, and the empty/loading/error states from the UI/UX state contract.
- Before reporting a screen as done, run and pass: format, lint, type check, and all tests for both sides. Report failures as they are; never skip, disable, or weaken a test to get green.

## 6. No comments in code

- Never write comments, docstrings, or explanatory text in code.
- Code must explain itself through names, types, and small functions.
- Do not add explanations of the code inside source files; explanations belong in the chat only when the user asks.

## 7. Ask when unsure

- When a requirement is unclear, the docs conflict, or there is more than one reasonable option, stop and ask the user with clear choices and a recommendation. Do not guess.
