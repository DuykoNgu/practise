# Project management — CIC V1

This folder tracks **how** CIC V1 gets built: milestones, backlog, progress per screen, decisions, and risks. **What** CIC must do lives in [`docs/`](../docs); rules for coding agents live in [`CLAUDE.md`](../CLAUDE.md).

| File | Purpose | Updated when |
|---|---|---|
| [roadmap.md](roadmap.md) | Milestones M0–M6 in build order, with exit criteria | A milestone starts, finishes, or changes scope |
| [backlog.md](backlog.md) | All 23 user stories mapped to feature, priority, screen, modules, acceptance criteria, milestone | A story changes status |
| [tracker.md](tracker.md) | Progress per screen: backend, frontend, tests, accessibility, done | A screen moves forward |
| [definition-of-done.md](definition-of-done.md) | Checklist a screen and a milestone must pass | The quality bar changes |
| [decisions.md](decisions.md) | Decision log with reasons | A technical or product decision is made |
| [risks-and-questions.md](risks-and-questions.md) | Risks, open questions, doc inconsistencies | A risk or question appears or is resolved |
| [sprints/](sprints/README.md) | Sprint template and sprint plans | A sprint is planned or reviewed |
| [plans/](plans/ai-package.md) | Work plans for larger tracks (AI package and evals) | A plan starts, changes, or a phase finishes |

## Status legend

| Mark | Meaning |
|---|---|
| ⬜ | Not started |
| 🟨 | In progress |
| 🟦 | In review (code complete, checks running or review pending) |
| ✅ | Done — passes [definition-of-done.md](definition-of-done.md) |
| ⛔ | Blocked — reason in [risks-and-questions.md](risks-and-questions.md) |

## Working loop

```mermaid
flowchart LR
    A["Pick next screen<br/>roadmap.md"] --> B["Read docs rows<br/>IA · UC · US · AC · BR · OpenAPI"]
    B --> C["Build backend module<br/>+ tests"]
    C --> D["Build frontend feature<br/>+ tests"]
    D --> E["Run checks<br/>definition-of-done.md"]
    E -->|Fail| C
    E -->|Pass| F["Commit and push"]
    F --> G["Update tracker.md<br/>and backlog.md"]
    G --> H["Suggest /compact"]
    H --> A
```

## Current status

- Design phase: **complete** (scope, features, use cases, INVEST backlog, IA, acceptance criteria, business rules, NFRs, algorithms, C4, data model, OpenAPI, folder structure, class and sequence diagrams).
- Dependency setup: **complete** (`src/backend/requirements*.txt`, `src/frontend/package.json` with Tailwind CSS 4, shadcn/ui, TanStack Query).
- Implementation: **not started** — next milestone is [M0 Platform](roadmap.md#m0--platform); the [AI track](roadmap.md#ai-track) A1–A4 can run in parallel.
- AI package: **planned** — design in [ai-package.md](../docs/architecture/ai-package.md), plan in [plans/ai-package.md](plans/ai-package.md).
