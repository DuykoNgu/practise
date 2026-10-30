# Scope V1

> Design status: TARGET V1
>
> Implementation status: NOT STARTED (documentation phase)

Product name: **Change-Incident Correlation (CIC)**.

## Problem

When tickets rise abnormally, the IT team needs to answer quickly: **which recent change is the likely cause?**

Real example: on Tuesday at 22:00 IT applies a Windows patch to the Accounting department. On Wednesday morning there are 14 "cannot print" tickets. Today only an experienced person can connect the two events; service desk agents usually handle each ticket on its own and may need hours to realize it is one shared incident.

A good solution needs a simple place to:

- record changes with their scope and rollback plan;
- receive tickets from several sources;
- know the normal ticket volume (baseline);
- detect when volume is abnormal;
- rank recent changes as suspects, with reasons the user can verify.

This is not an ITSM replacement, not a CMDB, and not a root-cause analysis tool.

## Input data

### Change record

| Field | Description |
|---|---|
| Type | Patch · configuration change · software upgrade |
| Time | Start and end of execution (with time zone) |
| Scope | Device group, department, software, branch (one or more) |
| Implementer | IT account that performed the change, and the approver |
| Rollback plan | Available or not, steps, estimated duration, risk level |
| Status | Scheduled · In progress · Completed · Rolled back · Failed |

### Ticket

| Field | Description |
|---|---|
| Created time | When the user reported the problem |
| Category | For example: Printing, Network, Email, Accounting software, Login |
| Reporter | Department and branch of the reporter |
| Related device / software | Device group, software name, version |
| Description | Free text, used for keyword matching against changes |
| Status | New · In progress · Resolved · Closed |

### Baseline

Average ticket count (and standard deviation) per **hour slot × weekday × category**, computed from ticket history (default: last 8 weeks, excluding periods already marked as incidents).

## Target V1 goals

The target V1 supports:

- Login through the REST API with backend authentication and authorization.
- Change management (list, add/edit modal, detail modal, status updates).
- Ticket management with manual entry, CSV/Excel import (preview and validation), and API ingestion from an ITSM system.
- Baseline calculation and comparison with actual volume.
- Anomaly detection per category, department, branch, and software.
- Ranked suspect changes with an explainable score (0–100).
- Suggested resolution for each suspect change, built from cited evidence (related tickets, rollback plan, previously confirmed incidents) and written by an LLM; every statement must cite its evidence, and a suggestion is marked *confirmed* or *hypothesis*.
- Suspect feedback (correct cause / unrelated) to measure and tune accuracy.
- Persisted audit log.
- System configuration (thresholds, tracing window, ranking weights).
- User management (Admin) and personal profile.
- Backend-enforced roles and permissions.

## Non-goals

V1 does **not** include:

- Automatic execution of rollback or any change on real infrastructure.
- Replacing the ITSM or CMDB; CIC reads and correlates data only.
- Root-cause analysis at log or system level.
- Predicting incidents before a change is applied.
- Free-form chatbot or conversational assistant. The LLM only explains suspects and drafts suggested resolutions; it never computes the suspicion score.
- Resolution suggestions that cannot cite evidence. The system suggests only; it never executes a resolution.
- Ingesting raw application/error logs (tickets and change records remain the signals in V1).
- External identity providers and multi-factor authentication.

## Target V1 architecture

```text
Web frontend (SPA)
    → REST/HTTPS/JSON
Multi-tier backend API
    → Relational database (changes, tickets, baselines, correlation results)
    → Background processor (baseline, anomaly detection, ranking)
    → LLM service (explanation and suggested resolution, with evidence validation)
    → File storage for imports
```

This is an idea-level view. Detailed architecture (C4, data model, API) is defined in later phases.
