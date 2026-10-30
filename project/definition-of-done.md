# Definition of Done — CIC V1

## Screen

A screen (or API-only slice) is ✅ only when every item holds.

**Scope**
- [ ] Every story mapped to the screen in [backlog.md](backlog.md) meets its `AC-UC` criteria.
- [ ] Applicable business rules (`BR-*`) are enforced where [business-rules.md](../docs/requirements/business-rules.md) says.
- [ ] Endpoints match `docs/api/openapi.yaml`; tables match `src/database/cic.sql`. No unapproved additions.

**Backend**
- [ ] Router → service → repository interface; other modules reached only through their service.
- [ ] Role and ownership checked in the backend for every endpoint.
- [ ] Errors returned as problem+json; no stack traces or secrets in responses or logs.
- [ ] Audit events written for actions listed in BR-021.

**Frontend**
- [ ] Built with Tailwind CSS + shadcn/ui; data through TanStack Query hooks in `features/<area>/hooks/`.
- [ ] All states from the UI/UX state contract: loading, empty, validation, API error, 401, 403, conflict, saving, success.
- [ ] Unauthorized controls and navigation are not rendered.
- [ ] Accessibility: labels, focus order, modal focus trap, no color-only status (NFR-ACC-001).

**Quality**
- [ ] Tests cover happy path, validation errors, 401, 403, conflicts, and UI states.
- [ ] Coverage meets NFR-MAINT-001 for the touched services.
- [ ] Backend: `ruff format --check`, `ruff check`, `mypy`, `pytest` pass.
- [ ] Frontend: `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.
- [ ] No comments or docstrings in code ([CLAUDE.md §6](../CLAUDE.md)).
- [ ] `simplify` and `code-review` run on the diff.

**Bookkeeping**
- [ ] Committed and pushed with a progress note in the message.
- [ ] [tracker.md](tracker.md) and [backlog.md](backlog.md) updated.
- [ ] New decisions added to [decisions.md](decisions.md); new risks or questions to [risks-and-questions.md](risks-and-questions.md).

## Milestone

- [ ] Every row of the milestone in [tracker.md](tracker.md) is ✅.
- [ ] The milestone exit criteria in [roadmap.md](roadmap.md) are demonstrated.
- [ ] CI is green on `main`.
- [ ] README "Project Progress" checklist updated when a milestone completes a listed item.
