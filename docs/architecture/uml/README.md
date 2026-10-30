# Detailed UML — CIC

> **Status:** Target design

| Document | Content |
|---|---|
| [Class diagrams](01-class-diagrams.md) | Authentication, Change Management, Suspect Ranking, Suggested Resolution |
| [Sequence diagrams](02-sequence-diagrams.md) | Login, change create/edit, log ingestion, detection and ranking, suggestion generation, review, confirmation |
| [C4 Level 4 — Code](../c4/04-code.md) | Code collaboration for Suspect Ranking and Suggested Resolution |

## Relationship to C4 and other documents

- C3 components ([03-component.md](../c4/03-component.md)) map to modules in [07-folder-structure.md](../../07-folder-structure.md); this folder shows the classes inside those modules.
- Class and field names follow [cic.sql](../../../src/database/cic.sql) and [openapi.yaml](../../api/openapi.yaml).
- Formulas for baseline, anomaly detection, and each score factor are in [09-algorithms.md](../../09-algorithms.md); the classes here fix where that logic lives (`BaselineService`, `AnomalyDetectionService`, `SuspectScorer`).
