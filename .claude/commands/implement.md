---
description: Implement one work item from project/screens (screen = frontend feature + backend modules) after checking it against the project files and docs
argument-hint: "[item id, e.g. SCR-01, PLT-1, API-ITSM, AI-1; empty = next ready item]"
---

Implement work item: **$ARGUMENTS**

Follow `CLAUDE.md` at every step. Work in this exact order and do not write code before step 4.

## 0. Sync check

Run `python project/tools/check_screens.py` (install `project/tools/requirements.txt` once if needed). If it reports problems, stop, show them, and ask how to resolve them before doing anything else.

## 1. Item

1. If `$ARGUMENTS` is empty, open `project/tracker.md` and take the first item in the main track (or the AI track if the user asked for AI work) whose status is ⬜ and whose `depends_on` items are all ✅. Say which item you picked.
2. Open `project/screens/<ID>.yaml`. If it does not exist, stop and ask.
3. Read every key: `covers`, `route`, `roles`, `stories`, `acceptance`, `rules`, `nfr`, `docs`, `frontend`, `backend`, `ai`, `tasks`, `done_when`, `open`.
4. Every id in `depends_on` must be `done`; otherwise stop and ask whether to continue.

## 2. Project

1. `project/risks-and-questions.md`: each id in `open`. If one is still `Open` and blocks a task, stop and ask with options and a recommendation.
2. `project/decisions.md`: decisions that constrain this item (stack, libraries, boundaries).
3. `project/backlog.md`: the text and priority of each story.
4. `project/definition-of-done.md`: the checklist this item must pass.

## 3. Docs

Read only what the item references and note the exact rules you will implement:

- `docs/08-acceptance-criteria.md`: each `acceptance` id.
- `docs/requirements/business-rules.md` and `docs/requirements/non-functional-requirements.md`: each `rules` and `nfr` id.
- `docs/api/openapi.yaml`: each `backend.api` operation — request, response, status codes, problem+json.
- `src/database/cic.sql`: each `backend.tables` table and `backend.jobs` value.
- `docs/04-information-architecture.md`: the `covers` screens, page permissions, and every `frontend.states` entry in the UI/UX state contract.
- Every path in `docs`.
- `docs/07-folder-structure.md`: where each file goes; `docs/architecture/ai-package.md` for `ai` items.

If the item, project files, and docs disagree, or something needed is not defined, stop and ask. Never add endpoints, columns, settings, screens, or libraries that the docs do not define.

Before coding, write a short outline in chat: files, endpoints, tables, components, hooks, tests, and which `tasks` they close. Then continue without waiting unless something above is blocked.

## 4. Code

1. Set the item `status: in_progress` in its YAML.
2. Load the skills listed in `CLAUDE.md` §2 for each side you touch (`claude-api` before any Anthropic SDK call).
3. Backend (`backend.modules`): schemas → repository Protocol and implementation → service → router → wiring in `core/container.py` and `api_router.py`. Other modules only through their service.
4. Frontend (`frontend.feature`): `api.ts` → the listed `hooks` with TanStack Query → the listed `components` with shadcn/ui and Tailwind → page in `app/<route>`. Implement every listed state. Enforce `roles` in the backend and hide unauthorized controls in the UI.
5. AI (`ai`): only inside `src/ai`; add dataset cases with every behavior change.
6. Tests together with the code: happy path, validation, 401, 403, conflict, and each listed state.
7. No comments or docstrings. Do not touch modules or features outside the item without asking.

## 5. Verify

Run every check that applies and fix until all pass; report failures as they are:

- Backend: `ruff format --check`, `ruff check`, `mypy`, `pytest`.
- Frontend: `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
- AI package: `ruff`, `mypy --strict`, `pytest`, `cic-ai eval all` (stub). Run `--live` only after the user approves the cost.

Then run `simplify` and `code-review` on the diff and apply what they find. Check every `done_when` entry.

## 6. Record

In the same commit as the code:

1. In the item YAML, tick finished `tasks` (`[x]`), list in `skills_used` every skill you actually loaded for this item (exact names, e.g. `backend-design:think-before-coding`, `frontend-design:frontend-design`, `simplify`, `code-review`), and set `status: done` (or `review` if something remains, with the reason).
2. Run `python project/tools/check_screens.py --write` to regenerate `project/tracker.md`; it must pass.
3. Add new decisions to `project/decisions.md`; new risks, questions, or doc inconsistencies to `project/risks-and-questions.md`.

Commit as `<ID>: <what was done>` plus a short progress note and a `Skills:` line with the same list, push to the working branch, report what passed, what is left, and which skills were used, and suggest `/compact` before the next item.
