# Plan — AI package `cic_ai` and terminal evals

- **Design:** [docs/architecture/ai-package.md](../../docs/architecture/ai-package.md)
- **Status:** Planned · no code yet
- **Track:** AI track A1–A4, runs in parallel with M0–M4 and joins the backend in M5 ([roadmap](../roadmap.md#ai-track))

## Goal

Develop the LLM and log-processing parts of CIC as a standalone package that can be run, tested, and measured from the terminal before the backend needs it, so the quality of masking and suggestions is known in numbers before the anomaly detail screen ships.

## Scope

| In | Out |
|---|---|
| Masking, log classification, evidence contract, prompt, LLM client, draft parsing, validation | Baseline, anomaly detection, suspect scoring (stay in backend modules) |
| `cic-ai` CLI, eval datasets, metrics, thresholds, JSON reports | Database access, `EvidenceCollector` SQL, API endpoints, UI |
| Stub mode for CI, live mode against Anthropic | Prompt or model tuning beyond the first baseline |

## Phases

### A1 — Package and masking

| Task | Done when |
|---|---|
| `src/ai/pyproject.toml`, package `cic_ai`, `cic-ai` entry point, ruff/mypy/pytest config | `pip install -e src/ai[dev]` works and `cic-ai --help` prints commands |
| `.gitignore` entry for `src/ai/evals/reports/` | Reports never reach the remote |
| `Masker` for user names, e-mail, IPv4, IPv6, Windows and Unix paths | Unit tests pass |
| `cic-ai corpus masking` and a committed `masking.jsonl` of ≥ 500 lines | Corpus is reproducible from its seed |
| `cic-ai mask` and `cic-ai eval masking` | M-MASK-01 = 1.00, M-MASK-02 = 0, M-MASK-03 ≥ 0.95 |

### A2 — Classification

| Task | Done when |
|---|---|
| `LogClassifier`: normalization (numbers, hex, GUIDs, timestamps), SHA-256 signature, category from keywords | Unit tests pass |
| `classification.jsonl` + `categories.json` | ≥ 100 messages across all seed categories |
| `cic-ai classify` and `cic-ai eval classification` | M-CLS-01 ≥ 0.85, M-CLS-02 = M-CLS-03 = 1.00 |

### A3 — Suggestion pipeline in stub mode

| Task | Done when |
|---|---|
| `EvidenceItem` / `EvidenceBundle` models with short refs | Shape agreed with `modules/suggestions` (see open question Q-10) |
| `PromptBuilder`, `DraftParser`, `EvidenceValidator`, `pipeline.suggest` | Every row of the `EvidenceValidator` rules table in [class diagrams](../../docs/architecture/uml/01-class-diagrams.md) has a test |
| `StubLLMClient` replaying canned responses | Deterministic, no network |
| `suggestions.jsonl` with the printer case and ≥ 30 cases including adversarial tags | Every tag in the design doc has at least 3 cases |
| `cic-ai suggest` and `cic-ai eval suggestion` (stub) | All stub bars pass |
| CI job: ruff, mypy, pytest, `cic-ai eval all` (stub) | Green on `main` |

### A4 — Live mode and baseline

| Task | Done when |
|---|---|
| `AnthropicLLMClient`: JSON schema output, explicit effort, refusal fallback, timeout, retries, usage capture | Live `cic-ai suggest` runs on the printer case |
| `pricing.toml`, cost and latency metrics | Cost printed per case and per run |
| First live baseline on the full suggestion dataset | Report numbers recorded in [decisions.md](../decisions.md); live bars confirmed or adjusted with the product owner |

### A5 — Backend integration (part of M5)

| Task | Done when |
|---|---|
| Backend depends on `cic-ai`; `anthropic` removed from `src/backend/requirements.txt` | Backend installs with the local package; Docker build context includes `src/ai` |
| `LogService.ingest` calls `Masker`; worker `LOG_CLASSIFICATION` calls `LogClassifier` | US22 acceptance criteria pass |
| `EvidenceCollector` in `modules/suggestions` builds `EvidenceBundle`; worker `SUGGESTION_GENERATION` calls `pipeline.suggest` | US20 acceptance criteria pass; ranking unaffected when the LLM stub fails (NFR-AI-003) |

## Commands at the end of the plan

```bash
cd src/ai && pip install -e ".[dev]"
```

```bash
cic-ai eval all
```

```bash
cic-ai eval suggestion --live --limit 10
```

```bash
cic-ai suggest evals/datasets/printer-case.json --live
```

## Risks

| Risk | Mitigation |
|---|---|
| Synthetic masking corpus misses real-world patterns | Add anonymized real log lines when a log source is connected; keep recall bar at 1.00 |
| Live evals cost money on every run | `--limit`, cost printed before and after, stub mode in CI |
| Gold labels for suggestions are subjective | Labels reviewed by an IT Manager; only refs and status are scored, not wording |
| Contract drift between `EvidenceBundle` and backend | Contract lives in `cic_ai.evidence`; backend tests build bundles with the same models |
