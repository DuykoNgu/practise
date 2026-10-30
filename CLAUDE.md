# Agent rules

These rules apply to every coding task in this repository. They take precedence over habits and defaults.

## 1. Work screen by screen

- Work comes from the YAML files in [project/screens/](project/screens/README.md): one file per screen (frontend feature + backend modules) or non-screen slice (`PLT-*`, `API-*`, `JOB-*`, `AI-*`, `NFR-*`). They are the single source for route, roles, stories, acceptance, rules, API, tables, components, hooks, states, and tasks.
- Start an item with `/implement <ID>`; it runs `python project/tools/check_screens.py`, then checks the item, `project/`, and `docs/` before any code.
- Build one item at a time, in tracker order unless the user says otherwise. An item is done only when every task is ticked, its checks pass, and `check_screens.py --write` has regenerated `project/tracker.md`.
- Only touch the frontend feature, backend modules, and `cic_ai` modules listed in the item. If anything else must change, ask the user first.
- Shared code (`src/frontend/components/`, `src/frontend/lib/`, `src/backend/app/core/`) is added only when the current item needs it.
- When a doc changes (OpenAPI, schema, IA, rules), run `check_screens.py` and update the affected YAML files in the same commit.
- Hooks in `.claude/settings.json` enforce this: every edit to `project/screens/`, `docs/`, `cic.sql`, or the question list runs `check_screens.py`; every edit under `src/` is scanned for code comments; `git commit` is blocked while `check_screens.py` fails. Fix what they report; never bypass them.

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

AI package (`src/ai`, `cic_ai`):

- Keep the boundary in [AI package](docs/architecture/ai-package.md): no imports from `src/backend`, no database, no web server; only `cic_ai.llm` calls the LLM, and only with masked text.
- Use the `claude-api` skill before writing or changing any Anthropic SDK call.
- Every behavior change comes with dataset cases and passes `cic-ai eval all` in stub mode; checked with `ruff`, `mypy --strict`, `pytest`.
- `--live` evals cost money: run them only after the user approves, and report the printed cost.

Before every commit: `simplify`, then `code-review`.

## 3. Stay within the limits

- Implement only what the docs define for V1: [Scope](docs/01-scope.md), [Features](docs/02-features.md), [INVEST backlog](docs/05-invest-requirements.md). Never build anything listed under *Non-goals*.
- Follow the agreed structure and rules in [Folder structure](docs/07-folder-structure.md): the dependency flow, module boundaries (other modules only through their service), services depending on interfaces, and the `cic_ai` boundary.
- Follow the API contract in `docs/api/openapi.yaml` and the schema in `src/database/cic.sql`. Do not change either without asking the user.
- Do not add libraries, endpoints, tables, columns, screens, or settings that the docs do not define without asking the user.
- Do not refactor code outside the current screen.

## 4. Manage context

- Keep each session focused on one screen.
- When a screen is finished and committed, or when the context grows long, suggest `/compact` to the user before continuing.
- Keep a short progress note per screen in the commit message so work can resume after compaction.
- Read [project/tracker.md](project/tracker.md) at the start of a session to find the next screen; update it, [project/backlog.md](project/backlog.md), and [project/decisions.md](project/decisions.md) in the same commit as the work.

## 5. Test and verify quality

- Write tests together with the code. Backend: `pytest` in `src/backend/tests/` (`modules/<module>/`, fakes from `tests/fakes/`). AI package: `pytest` in `src/ai/tests/` plus `cic-ai eval`. Frontend: tests in `src/frontend/tests/`.
- Cover the happy path, validation errors, 401, 403, conflicts, and the empty/loading/error states from the UI/UX state contract.
- Before reporting a screen as done, run and pass: format, lint, type check, and all tests for both sides. Report failures as they are; never skip, disable, or weaken a test to get green.

## 6. No comments in code

- Never write comments, docstrings, or explanatory text in code.
- Code must explain itself through names, types, and small functions.
- Do not add explanations of the code inside source files; explanations belong in the chat only when the user asks.

## 7. Ask when unsure

- When a requirement is unclear, the docs conflict, or there is more than one reasonable option, stop and ask the user with clear choices and a recommendation. Do not guess.
