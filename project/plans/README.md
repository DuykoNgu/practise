# Plans

One plan per milestone. Every work item has an **ID** used by [tracker.md](../tracker.md) and by the `/implement` command ([.claude/commands/implement.md](../../.claude/commands/implement.md)).

| Plan | Items | Depends on |
|---|---|---|
| [M0 Platform](m0-platform.md) | M0-1 … M0-4 | — |
| [M1 Access](m1-access.md) | M1-1 … M1-3 | M0 |
| [M2 Administration](m2-administration.md) | M2-1, M2-2 | M1 |
| [M3 Data intake](m3-data-intake.md) | M3-1 … M3-4 | M2 |
| [M4 Detection and ranking](m4-detection.md) | M4-1 … M4-5 | M3 |
| [M5 AI evidence](m5-ai-evidence.md) | M5-1 … M5-3 | M4, A1–A4 |
| [M6 Audit and hardening](m6-audit-hardening.md) | M6-1, M6-2 | M5 |
| [AI package](ai-package.md) | A1 … A5 | — (A5 = M5) |

## Work item format

Each item has the same fields so an agent can check it against the docs before coding:

| Field | Meaning |
|---|---|
| Stories / AC | User stories and acceptance criteria in [08-acceptance-criteria.md](../../docs/08-acceptance-criteria.md) |
| Rules / NFR | Business rules and non-functional requirements that apply |
| API | Paths in [openapi.yaml](../../docs/api/openapi.yaml) — implement exactly these |
| Tables | Tables in [cic.sql](../../src/database/cic.sql) — no new columns without approval |
| Design | Sequence and class diagrams, algorithms, IA rows |
| Backend / Frontend / Tests | Task checklists; tick them in the same commit as the work |
| Done when | Observable result that closes the item |
| Open | Questions from [risks-and-questions.md](../risks-and-questions.md) that block or shape the item |

## How to run an item

```text
/implement M1-1
```

Without an ID, `/implement` picks the first item in [tracker.md](../tracker.md) that is not done and whose dependencies are done.
