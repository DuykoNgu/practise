# Algorithms — Baseline, Anomaly Detection, Suspect Ranking

> Design status: TARGET V1
>
> Validation: the formulas were run in a Python prototype and the SQL in PostgreSQL 16 on the printer example (section 5); the numbers in this document come from those runs.

These algorithms are rule-based and explainable: no machine learning model and no LLM decide whether a spike is abnormal or which change is suspected. The LLM only runs afterwards ([AI pipeline](architecture/ai-pipeline.md)). Rules: [BR-009–BR-012](requirements/business-rules.md).

## 1. Parameters

| Parameter | Default | Where | Meaning |
|---|---|---|---|
| `baseline_window_weeks` | 8 | `settings` | Weeks of history in the baseline |
| `anomaly_threshold` (k) | 3.0 | `settings` | Standard deviations above the mean |
| `detection_interval_minutes` | 15 | `settings` | How often detection runs |
| `tracing_window_hours` (T) | 48 | `settings` | How far back candidate changes are searched |
| `weight_*` | 1 each | `settings` | Weight of each of the five factors |
| `MIN_SAMPLE_WEEKS` | 3 | code constant | Minimum history for a baseline cell |
| `WINDOW_MINUTES` | 60 | code constant | Length of the detection window |
| `SIGMA_FLOOR` | √max(mean, 1) | code constant | Lower bound of the deviation used in detection |
| `RELEVANCE_CAP` | 39 | code constant | Highest score when scope and keyword both do not match |
| `CLOSE_AFTER_RUNS` | 2 | code constant | Normal runs in a row before an anomaly gets an end time |

Code constants can be moved to `settings` later if they need tuning without a deploy.

## 2. Baseline

### 2.1 Definition

A **cell** is one combination of *category × weekday × hour* (ISO weekday 1–7, hour 0–23, in the organization's time zone), computed at three levels:

| Level | `department_id` | `branch_id` |
|---|---|---|
| Category only | NULL | NULL |
| Category × department | set | NULL |
| Category × branch | NULL | set |

For each cell, the sample is the ticket count of that weekday-hour in each of the last `baseline_window_weeks` weeks. **Hours without tickets count as 0** (otherwise the mean would be too high).

```text
mean    = average of the weekly counts
std_dev = sample standard deviation of the weekly counts
```

### 2.2 Rules

- **Incident exclusion:** a week's value is dropped from a cell if that hour overlaps a `RESOLVED` anomaly of the same group, so past incidents do not inflate "normal".
- **Cold start:** a cell with fewer than `MIN_SAMPLE_WEEKS` (3) usable weeks is not stored. Detection then uses the category-only cell; if that is missing too, the group is not evaluated.
- **Schedule:** recomputed daily at 02:00 (organization time zone) and on demand (UC12). Each run is a new `baseline_runs` row; the latest `SUCCEEDED` run is active, and a failed run never replaces it.

### 2.3 SQL (category × department level)

```sql
WITH hours AS (          -- every hour of the window, so empty hours count as 0
  SELECT generate_series(:run_day - make_interval(weeks => :weeks),
                         :run_day - interval '1 hour', interval '1 hour') AS slot
),
counts AS (
  SELECT date_trunc('hour', reported_at) AS slot, category_id, department_id, count(*) AS n
  FROM cic.tickets
  WHERE reported_at >= :run_day - make_interval(weeks => :weeks) AND reported_at < :run_day
  GROUP BY 1, 2, 3
),
grid AS (
  SELECT h.slot, g.category_id, g.department_id, coalesce(c.n, 0) AS n
  FROM hours h
  CROSS JOIN (SELECT DISTINCT category_id, department_id FROM counts) g
  LEFT JOIN counts c USING (slot, category_id, department_id)
  -- incident exclusion: anti-join on resolved anomalies of the same group (omitted for brevity)
)
SELECT category_id, department_id,
       extract(isodow FROM slot)::int AS weekday,
       extract(hour   FROM slot)::int AS hour,
       avg(n) AS mean, stddev_samp(n) AS std_dev, count(*) AS sample_weeks
FROM grid
GROUP BY category_id, department_id, weekday, hour
HAVING count(*) >= 3;    -- MIN_SAMPLE_WEEKS
```

The session runs with the organization's time zone (`SET TIME ZONE`) so `isodow` and `hour` are local.

## 3. Anomaly detection

### 3.1 When and what

Every `detection_interval_minutes` (15), the worker evaluates the **last 60 minutes** (rolling window) for each group: category, category × department, category × branch.

### 3.2 Test

```text
actual    = tickets of the group reported in [now − 60 min, now)
expected  = Σ (minutes of the window in hour cell h / 60) × mean_h        (the window can span two hour cells)
variance  = Σ (minutes of the window in hour cell h / 60) × std_dev_h²
sigma     = max( √variance , √max(expected, 1) )                          (SIGMA_FLOOR)
z         = (actual − expected) / sigma
abnormal  ⇔ z > k                                                         (k = anomaly_threshold, default 3)
```

The floor stops tiny cells from firing on noise: a cell that never has tickets needs at least 4 tickets in an hour before it is abnormal (`z = 4 > 3`). A busy cell (mean 20, std 4) needs more than 33.

### 3.3 Severity

| z | Severity |
|---|---|
| ≥ 2k (6) | HIGH |
| ≥ 1.5k (4.5) | MEDIUM |
| > k (3) | LOW |

### 3.4 Avoiding duplicates

- **Most specific group wins:** if category × department fires and holds ≥ 80% of the tickets of the category-only group in the same window, the category-only anomaly is not created. The same applies to branch.
- **Extend, do not repeat:** if an `OPEN` anomaly of the same group has no `end_at`, the new window extends it (new tickets are linked, `actual_count` and peak z are updated, and suspects are re-ranked).
- **Close:** after `CLOSE_AFTER_RUNS` (2) normal runs in a row, `end_at` is set to the end of the last abnormal window. The status stays `OPEN` until a user acknowledges or resolves it.

### 3.5 What is stored and linked

| Field | Value |
|---|---|
| `start_at` | Start of the first abnormal window |
| `actual_count`, `expected_count` | Of the peak window |
| `software_id` | Software shared by ≥ 60% of the anomaly's tickets, otherwise NULL |
| `anomaly_tickets` | Tickets of the group from `start_at` to `end_at` (or now) |
| `anomaly_logs` | Error logs from `start_at − 1 h` to `end_at` whose department or branch matches (directly or through the device group) **and** whose category or software matches |

## 4. Suspect ranking

### 4.1 Candidates

A change is a candidate when `anomaly.start_at − T ≤ change.start_at ≤ anomaly.start_at` (T = 48 h) and its status is not `SCHEDULED`. No candidate means "No suspect found".

### 4.2 Five factors, each in [0, 1]

| Factor | Formula | Explanation shown to the user |
|---|---|---|
| **Time proximity** | `1 − Δ / T`, where Δ = hours from the change's end (or start, if no end) to `anomaly.start_at`, clamped to [0, 1] | "Finished 9.5 h before the spike started" |
| **Scope match** | Share of the anomaly's tickets that match the change scope: (department ∈ change departments **or** device group ∈ change device groups **or** software ∈ change software) **and** (branch ∈ change branches, if the change names branches) | "14 of 14 tickets come from the change's scope (Accounting)" |
| **Category / keyword match** | `0.5 × software_overlap + 0.5 × min(1, hits / 2)`. `software_overlap` = 1 if any software of the anomaly's tickets or logs is in the change scope. `hits` = category keywords and top log tokens found in the change title or description as **whole words or phrases** (not substrings: the Vietnamese keyword "in" must not match "W**in**dows") | "Logs come from Windows 11, which the change updated" |
| **Anomaly magnitude** | `min(1, (z_peak − k) / (2k))` | "14 tickets against 1.5 expected (z = 10.2)" |
| **Change risk** | Base by type (SOFTWARE_UPGRADE 0.8, PATCH 0.7, CONFIG_CHANGE 0.6), +0.2 if `FAILED`, −0.3 if `ROLLED_BACK`, +0.1 if no rollback plan, +0.1 if rollback risk is HIGH, clamped to [0, 1] | "Patch, completed, rollback plan available" |

### 4.3 Score and level

```text
raw   = Σ weightᵢ × factorᵢ / Σ weightᵢ
score = round(100 × raw)
if scope match = 0 and category/keyword match = 0:  score = min(score, 39)    (relevance gate)
level = HIGH if score ≥ 70, MEDIUM if score ≥ 40, otherwise LOW
rank  = 1..n by score descending; ties → the change that started later ranks higher
```

**Why the relevance gate:** magnitude is the same for every candidate of one anomaly, and risk depends only on the change, so without the gate an unrelated but risky change can reach Medium. In the prototype, an ERP upgrade in another branch scored 53 before the gate and 39 after it.

### 4.4 When ranking runs again

- The anomaly is extended (new tickets or logs).
- A change is created or updated later with `start_at` inside an open anomaly's tracing window.
- Settings that affect ranking (weights, tracing window) change: open anomalies are re-ranked.

Re-ranking replaces the suspects of the anomaly in one transaction and enqueues suggestion jobs for new suspects only.

## 5. Worked example — the printer case

**Baseline** (Wednesday 08:00, Printing × Accounting, last 8 Wednesdays: 1, 2, 1, 3, 1, 2, 1, 1 tickets):

| Value | Result |
|---|---|
| mean | 1.500 |
| std_dev | 0.756 |
| sigma (floor √1.5 applies) | 1.225 |
| Limit `mean + 3 × sigma` | 5.17 |

**Detection** (run at 09:00, window 08:00–09:00 = the 08:00 cell): actual 14 → z = 10.21 → **HIGH**. The run at 08:15 already fires: with an illustrative 07:00 cell of mean 0.25, the blended expected is 0.56 and z ≈ 13.

**Ranking** (anomaly start Wed 08:00, three candidates):

| Change | Δ | Time | Scope | Keyword | Magnitude | Risk | Score | Level |
|---|---|---|---|---|---|---|---|---|
| **Windows patch KB-123** (Accounting, Windows 11, Tue 22:00–22:30) | 9.5 h | 0.80 | 1.00 (14/14) | 0.50 (software) | 1.00 | 0.70 | **80** | **HIGH** (#1) |
| ERP upgrade v5 (HCM branch, Tue 18:00–20:00, no rollback plan) | 12 h | 0.75 | 0.00 | 0.00 | 1.00 | 0.90 | 39 (gate; 53 without) | LOW (#2) |
| Mail server config (IT, Mon 14:00–15:00) | 41 h | 0.15 | 0.00 | 0.00 | 1.00 | 0.60 | 35 | LOW (#3) |

The patch is ranked first for the right reasons: closest in time, same department, and the error logs come from the software it updated.

## 6. Edge cases

| Case | Behavior |
|---|---|
| Fewer than 3 weeks of history | Cell not stored; fall back to category-only cell; otherwise not evaluated |
| Cell that never has tickets | Needs ≥ 4 tickets in 60 minutes (floor) |
| Mild rise (4 vs mean 1.5) | Not abnormal (z = 2.04) |
| Spike spans two hour cells | Expected and variance are blended by minutes |
| Department and category-only both fire | Only the department anomaly is kept (≥ 80% rule) |
| Change recorded after the spike with an earlier `start_at` | Triggers re-ranking |
| All weights 0 | Rejected by settings validation (BR-019) |
| Change rolled back before the spike | Risk −0.3; still listed so the user sees it was considered |
| Ticket reported in another time zone | Stored in UTC; weekday/hour computed in the organization time zone |

## 7. Evaluation and tuning

- **Metric:** share of anomalies with a `CORRECT_CAUSE` verdict whose confirmed change is in the top 3 suspects (target ≥ 70%, NFR-AI-004), plus precision of detection (share of anomalies not marked as noise).
- **Back-test:** replay past tickets and changes with known causes through the algorithms before go-live; adjust `anomaly_threshold` and weights.
- **V1 tuning is manual:** an Administrator changes weights in Settings based on the monthly report; there is no automatic learning in V1.

## 8. Where the code lives

| Algorithm | Class ([class diagrams](architecture/uml/01-class-diagrams.md)) | Tables |
|---|---|---|
| Baseline | `BaselineService` (module `baseline`) | `baseline_runs`, `baseline_cells` |
| Detection, extend/close, linking | `AnomalyDetectionService` (module `anomalies`) | `anomalies`, `anomaly_tickets`, `anomaly_logs` |
| Factors, score, gate, level | `SuspectScorer` (pure, unit-tested) | — |
| Candidates, ranking, re-ranking | `SuspectRankingService` | `suspects`, `suspect_factors` |
