---
description: Implement one plan item (M0-1 … M6-2, A1 … A5) after checking it against the plan, project tracking, and docs
argument-hint: "[item id, e.g. M1-1 or A1; empty = next item]"
---

Implement plan item: **$ARGUMENTS**

Follow `CLAUDE.md` at every step. Work in this exact order and do not write code before step 4.

## 1. Plan

1. If `$ARGUMENTS` is empty, open `project/tracker.md` and take the first item that is not ✅ and whose milestone dependencies (listed in `project/plans/README.md`) are ✅. Say which item you picked.
2. Find the item in `project/plans/` (`m0-platform.md` … `m6-audit-hardening.md`, `ai-package.md`). If it does not exist, stop and ask.
3. Read the whole item: stories, AC, rules, NFR, API, tables, design links, task checklists, "Done when", "Open".

## 2. Project

1. `project/tracker.md`: confirm the item and its dependencies; if a dependency is not ✅, stop and ask whether to continue.
2. `project/backlog.md`: the stories of the item and their acceptance ids.
3. `project/risks-and-questions.md`: every question or inconsistency named in the item's "Open" field. If one is still `Open` and blocks the work, stop and ask the user with options and a recommendation.
4. `project/decisions.md`: decisions that constrain the item (stack, libraries, boundaries).
5. `project/definition-of-done.md`: the checklist this item must pass.

## 3. Docs

Read only the parts the item links to, and note the exact rules you will implement:

- `docs/08-acceptance-criteria.md` — the `AC-UC*` sections of the item.
- `docs/requirements/business-rules.md` and `docs/requirements/non-functional-requirements.md` — the listed ids.
- `docs/api/openapi.yaml` — the listed paths: request, response, status codes, error format.
- `src/database/cic.sql` — the listed tables, constraints, enums.
- `docs/04-information-architecture.md` — screen row, page permissions, UI/UX state contract (screens only).
- Design links in the item: sequence and class diagrams, `docs/09-algorithms.md`, `docs/architecture/ai-package.md`.
- `docs/07-folder-structure.md` — where each file goes.

Cross-check: if the plan, project files, and docs disagree, or something needed is not defined, stop and ask. Do not invent endpoints, columns, settings, or screens.

Before coding, write a short outline in chat: files to create or change, endpoints, tables, tests, and which checklist boxes they close. Then continue without waiting unless something above is blocked.

## 4. Code

1. Load the skills listed in `CLAUDE.md` §2 for the side you are working on (backend, frontend, or AI package; `claude-api` before any Anthropic SDK call).
2. Backend first: schemas → repository Protocol and implementation → service → router → wiring in `core/container.py` and `api_router.py`.
3. Frontend second: `features/<area>/api.ts` → hooks with TanStack Query → components with shadcn/ui and Tailwind → route in `app/`.
4. AI package items: only inside `src/ai`; add dataset cases with every behavior change.
5. Write tests together with the code: happy path, validation, 401, 403, conflict, and the UI states of the screen.
6. No comments or docstrings. No changes outside the item's modules without asking.

## 5. Verify

Run every check that applies and fix until all pass; report failures as they are:

- Backend: `ruff format --check`, `ruff check`, `mypy`, `pytest`.
- Frontend: `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
- AI package: `ruff`, `mypy --strict`, `pytest`, `cic-ai eval all` (stub). Run `--live` only after the user approves the cost.

Then run `simplify` and `code-review` on the diff and apply what they find.

## 6. Record

In the same commit as the code:

- Tick the finished boxes in the item's plan file.
- Update the item's row in `project/tracker.md` (and the progress table) and the story status in `project/backlog.md`.
- Add new decisions to `project/decisions.md`; new risks, questions, or doc inconsistencies to `project/risks-and-questions.md`.

Commit with a message `<ITEM-ID>: <what was done>` followed by a short progress note, push to the working branch, report what passed, what is left, and suggest `/compact` before the next item.
