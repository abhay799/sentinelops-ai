# Phase A Frozen Evaluation Specification

**Status:** FROZEN BEFORE ANY RCAEval BENCHMARK RUN
**Freeze date:** 2026-10-02
**Scope:** SentinelOps AI Phase A — public-data detection and root-cause-analysis evaluation

This document freezes the evaluation protocol before benchmark results are observed. It may not be silently edited after results are seen. If a change becomes necessary, the original decision remains in Git history and an explicit amendment must state what changed, why it changed, and which datasets/results were already observed.

## 1. Revisions and provenance

- SentinelOps source revision at freeze: `9fd8b0967fbf94607e5e2b5213a7895669d07a4e`
- RCAEval Git revision: `259ea4167160256a74ad30004aa3d96a998c846e`
- Hugging Face RCAEval dataset revision: `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`
- Sock Shop topology source repository: `microservices-demo/microservices-demo`
- Sock Shop topology source revision: `9dff06fae4981921caec6a62393a6ebfce4b3e3f`

RCAEval benchmark code is treated as an external benchmark dependency. Benchmark datasets and caches remain outside the SentinelOps Git repository.

## 2. Dataset order and hold-out policy

Evaluation order is fixed:

1. RE2-OB — development/pilot suite.
2. RE2-SS — held-out suite.
3. RE2-TT — held-out suite.

RE2-SS and RE2-TT must not be inspected for outcome-driven tuning before their final evaluation. If tuning becomes necessary, it may use RE2-OB only. Any such tuning must be documented in a new spec-amendment commit before RE2-SS or RE2-TT is run.

Smoke-test cases are for adapter/runtime validation only. Their outputs must not be used to select thresholds, features, weights, graph settings, or hyperparameters. Smoke-test outputs are discarded; the full RE2-OB run later evaluates all RE2-OB cases, including the smoke-tested cases.

## 3. Fixed seeds and uncertainty

- Master random seed: `42`
- Random-baseline seed: `42`
- Bootstrap seed: `42`
- Bootstrap resamples: `10,000`
- Confidence interval: percentile bootstrap, `95%` (`2.5th` to `97.5th` percentiles)

Bootstrap resampling is clustered at the failure-case level. A sampled case contributes all of its timestamps and outputs. Per-fault-type confidence intervals resample only cases belonging to that fault type. Random-baseline rankings are generated once from the fixed seed and are not rerandomized inside bootstrap iterations.

## 4. RCAEval case parsing

RCAEval metric data is expected as a wide time-series table with a `time` column and metric columns named `<service>_<metric>`.

### 4.1 Service/metric grouping

- Exclude `time` from metric grouping.
- Parse every metric column with a single right split: `column.rsplit("_", 1)`.
- The left component is the service identifier.
- The right component is the metric identifier.
- Service names are preserved exactly except for a documented topology-name normalization where required.
- `_latency-50` columns are excluded to match RCAEval's current evaluation preprocessing.
- `_latency-90` is canonicalized to `_latency`, while the original column name remains in adapter provenance.
- No root-cause label, fault type, directory name, or post-injection result is used to decide how a metric is grouped.

If a metric column cannot be parsed unambiguously under this rule, the adapter must fail loudly for that case rather than guess.

## 5. Time ordering, alignment, and resampling

- Sort metric rows by Unix `time` ascending before any split or scoring.
- The native RCAEval metric timestamps are the evaluation clock.
- No interpolation, frequency conversion, or synthetic timestamp generation is performed in the primary evaluation.
- Metrics in the same wide row are treated as aligned at that row's `time`.
- Exact fully duplicated rows may be deduplicated.
- If the same timestamp occurs more than once with conflicting metric values, the adapter stops and records the case as invalid; it does not average conflicting observations silently.
- Missing timestamps between observed rows are not synthesized.
- Logs and traces are not resampled or joined into Phase A detection features.
- Trace-derived topology uses service relationships, not trace latency/error values as detector features.

## 6. Missing and non-finite values

Processing is chronological and causal:

1. Replace `+inf` and `-inf` with missing values.
2. Forward-fill each metric in timestamp order.
3. Any leading missing value that remains because no prior observation exists is filled with `0.0`.
4. No backward fill is allowed, because it would use a future observation to alter an earlier timestamp.
5. Missing-value handling is performed before the calibration/evaluation split but uses only backward-looking forward-fill state.

The adapter records missing/non-finite counts per case before and after filling.

## 7. Detection calibration and evaluation windows

Let `inject_time` be the RCAEval fault-injection timestamp.

For each case:

- `pre = rows where time < inject_time`
- `fault = rows where time >= inject_time`
- Sort `pre` chronologically.
- The first `50%` of `pre` rows, using floor division for the split index, are the **calibration slice**.
- The remaining `50%` of `pre` rows are the **normal evaluation slice**.
- The entire `fault` portion is the **fault evaluation slice**.
- Calibration rows are excluded from all detection precision/recall/F1 calculations.
- No post-injection sample contributes to means, standard deviations, normalization bounds, model fitting, or threshold calibration.

A case with insufficient calibration or evaluation rows must fail the smoke validation and be investigated before a benchmark run; the adapter must not silently alter the split ratio.

## 8. Metric-level detector semantics

SentinelOps Phase A uses its existing detector families with calibration-only fitting semantics.

### 8.1 Z-score component

For every service/metric pair:

- Calibration mean and population standard deviation are computed from the calibration slice only.
- Evaluation z-score is `abs(x - calibration_mean) / calibration_std`.
- Fixed anomaly threshold: `2.5`.
- If calibration standard deviation is zero:
  - score is `0` while the value equals the calibration constant;
  - a changed value is treated as above threshold and its normalized severity is clipped to `1.0`.

For a service at one timestamp:

- z-score service score = maximum metric z-score for that service.
- z-score service flag = `1` if any metric for that service crosses `2.5`, else `0`.

### 8.2 EWMA component

- Fixed alpha: `0.30`.
- Fixed threshold multiplier: `2.5`.
- EWMA state is initialized and run through the calibration slice chronologically.
- Calibration residual standard deviation is computed only from calibration residuals.
- Evaluation continues causally from the final calibration EWMA state.
- For a service at one timestamp:
  - EWMA service score = maximum standardized EWMA residual across that service's metrics.
  - EWMA service flag = `1` if any metric crosses the fixed threshold, else `0`.
- A zero calibration residual standard deviation uses the same constant-vs-change rule as the z-score component.

### 8.3 Isolation Forest component

One Isolation Forest is fitted per service using that service's multivariate calibration metric vectors only.

Fixed settings:

- `n_estimators = 200`
- `contamination = 0.10`
- `random_state = 42`

No evaluation or post-injection rows are used in fitting.

## 9. Score normalization and service-level anomaly

Component-score normalization must not look at evaluation extrema.

For each detector component, derive `cal_min` and `cal_max` from calibration component scores only:

`normalized = clip((score - cal_min) / (cal_max - cal_min), 0, 1)`

If `cal_max == cal_min`, normalized score is `0` for values not exceeding the calibration constant and `1` for values above it.

For each service/timestamp:

- `anomaly_votes = zscore_flag + ewma_flag + iforest_flag`
- `is_anomaly = 1` when `anomaly_votes >= 2`, otherwise `0`
- `anomaly_score = mean(normalized_zscore, normalized_ewma, normalized_iforest)`

These service-level records are adapted to the existing SentinelOps anomaly contract:

- `service`
- `feature_as_of_time`
- `anomaly_score`
- `anomaly_votes`
- `is_anomaly`

No threshold is tuned from benchmark outcomes.

## 10. Detection metrics

Two detection granularities are reported.

### 10.1 Timestamp-level detection

At each evaluation timestamp, system prediction is positive if **any service** has `is_anomaly == 1`.

Ground truth:

- timestamps in the normal evaluation slice: negative;
- timestamps at or after `inject_time`: positive.

Across cases, report micro-aggregated:

- precision
- recall
- F1
- TP / FP / TN / FN

Confidence intervals are case-cluster bootstraps.

### 10.2 Case-level detection

Because every RCAEval benchmark case is fault-injected, one binary label per case would contain no negative class. Therefore case-level precision is defined over two fixed windows per case:

- normal evaluation window: negative;
- post-injection fault window: positive.

A window prediction is positive if at least one system-level timestamp alert occurs inside that window.

Across these case windows, report:

- precision
- recall
- F1
- TP / FP / TN / FN

This metric is labeled **case-level (normal/fault-window) detection** in reports to avoid implying that RCAEval contains separate healthy cases.

### 10.3 Detection delay

For each case, detection delay is:

`first system-level positive timestamp at or after inject_time - inject_time`

Missed cases remain explicit misses and are not assigned an artificial delay. Report detection rate separately and report delay distribution only among detected cases. At minimum report median delay with a case-level bootstrap confidence interval; raw per-case delays remain in the evidence output.

## 11. Incident correlation

Fixed existing SentinelOps settings:

- correlation window: `120` seconds
- maximum graph hops: `2`
- severity thresholds remain the repository defaults

Correlation receives only the service-level anomaly records and a graph. Benchmark ground-truth root-cause labels are never inputs.

## 12. Dependency graph policy

SentinelOps graph direction remains `caller -> dependency/callee`.

### 12.1 RE2-OB and RE2-TT

Where traces are available:

- use only spans with timestamps before `inject_time`;
- derive parent-service -> child-service edges from parent/child span relationships within the same trace;
- remove self-edges;
- union pre-injection edges across the suite into one label-free static suite graph;
- do not use post-injection trace behavior to create or weight graph edges;
- do not use root-cause labels to alter graph structure.

If the pinned trace schema cannot reliably support parent-child service extraction, stop and document the blocker instead of inventing edges.

### 12.2 RE2-SS

RE2-SS has no distributed traces, so use a frozen static Sock Shop topology sourced from:

`microservices-demo/microservices-demo@9dff06fae4981921caec6a62393a6ebfce4b3e3f`

Primary source files are the Kubernetes network-policy manifests under:

`deploy/kubernetes/manifests-policy/`

Frozen application/service edges:

- `front-end -> carts`
- `orders -> carts`
- `front-end -> catalogue`
- `front-end -> orders`
- `orders -> payment`
- `orders -> shipping`
- `front-end -> user`
- `orders -> user`
- `shipping -> rabbitmq`
- `queue-master -> rabbitmq`
- `carts -> carts-db`
- `catalogue -> catalogue-db`
- `orders -> orders-db`
- `user -> user-db`

The archived `cart-access` policy uses selector `name: cart` while the archived deployment uses service/deployment name `carts`; the adapter normalizes this topology label to `carts`. No benchmark outcome is used for this normalization.

Only nodes that can be mapped to actual RCAEval service identifiers participate in a given evaluation case.

## 13. Deterministic SentinelOps RCA

Fixed existing RCA weights:

- anomaly strength: `0.45`
- change signal: `0.25`
- graph impact: `0.20`
- primary-service bonus: `0.10`
- high-confidence threshold: `0.75`
- medium-confidence threshold: `0.50`
- maximum candidates: `5`

RCAEval does not provide SentinelOps deployment/change telemetry. `change_count_300s` / change evidence therefore remains absent/zero; it must not be fabricated.

The Phase A headline result is deterministic SentinelOps RCA before Challenger effects. Challenger ablation belongs to Phase B.

## 14. RCA metrics

Use RCAEval's pinned evaluation implementation.

Primary service-level metrics:

- AC@1
- AC@3
- AC@5
- Avg@5
- Chance@5
- Lift@5

Also retain raw per-case ranked outputs. Report point estimates, 95% case-bootstrap confidence intervals, and breakdowns by fault type.

Ground-truth labels are used only by the evaluator after rankings have been produced.

## 15. Fixed baselines

### 15.1 RCAEval reproducible baseline set

Primary Python-3.12 comparison set:

- BARO
- CIRCA
- multi-source BARO
- multi-source CIRCA
- RCAEval analytical chance floor

If a pinned baseline cannot install or execute in the pinned environment, report it as unavailable/failed with the exact error. Do not silently replace it with a different method.

RCD/MMRCD/E-Diagnosis/HT are not primary Phase A baselines because their documented environment conflicts with the locked Python-3.12 evaluation environment.

### 15.2 Static-threshold baseline

- calibration statistics use only the first 50% pre-injection calibration slice;
- absolute z-score threshold: `2.5`;
- service score: maximum post-calibration metric z-score;
- service ranking: descending score with deterministic lexical service-name tie-break;
- no tuning.

### 15.3 Random-ranking baseline

- fixed master seed `42`;
- derive a deterministic per-case RNG seed from the master seed plus a stable hash of the case ID;
- rank the full candidate service set once per case;
- lexical service ordering is applied before shuffling to make input order deterministic;
- no repeated draws or cherry-picking.

### 15.4 Graph/PageRank baseline

- graph source follows Section 12;
- PageRank damping factor: `0.85`;
- personalization: normalized service anomaly strength from the deterministic detector;
- if all personalization weights are zero, use uniform personalization;
- rank descending PageRank score with lexical service-name tie-break;
- no tuning.

## 16. Per-fault reporting

Report overall results and separate results for each available RE2 fault type:

- CPU
- memory
- disk
- delay
- packet loss
- socket exhaustion

No fault type may be omitted because performance is poor. Dataset-supported naming is preserved in raw evidence.

## 17. Evidence and reproducibility record

Every benchmark result file must record at least:

- execution timestamp/date
- exact command
- SentinelOps Git commit
- RCAEval Git revision
- Hugging Face dataset revision
- dataset/suite
- case IDs
- fixed seed(s)
- environment/Python version
- detector configuration
- graph source/revision
- raw per-case ranking
- raw detection confusion counts
- raw detection delays
- aggregate metrics and bootstrap intervals
- failed/skipped cases with reasons

Results must be written as machine-readable JSON/CSV under `docs/evidence/` only after they are produced by an actual command.

## 18. Change control

This specification is frozen before any benchmark run.

If an implementation bug prevents the adapter from matching this specification, the bug may be fixed without changing the frozen evaluation choices. The fix and reason must be committed before rerunning.

If an evaluation choice itself must change after results have been observed:

1. do not silently edit history;
2. add an explicit amendment section to this file;
3. state the old rule, new rule, reason, and datasets/results already observed;
4. commit the amendment separately;
5. RE2-SS and RE2-TT remain untouched until the amendment is frozen.

No test-case outcome may be used to tune RE2-SS or RE2-TT.


## Erratum E1 — constant-series floating-point handling (2026-10-02)

This erratum records the implementation correction first committed as
`cefe94d` after the Step 13 smoke diagnostic. It does not change any detector
threshold, EWMA alpha, Isolation Forest setting, ensemble rule, calibration
window, or evaluation window.

For a calibration vector `x`, define a machine-precision-only constant-series
tolerance:

`tol = 8 * eps_float64 * max(1, max(abs(x)))`

where `eps_float64 = np.finfo(np.float64).eps`. The factor 8 is a fixed
round-off allowance for the small sequence of floating-point arithmetic
operations involved; it is not fitted from RCAEval data or benchmark outcomes.

A calibration vector is treated as numerically constant when
`max(x) - min(x) <= tol`. For Z-score and EWMA constant-series branches,
evaluation values within `tol` of the calibration reference receive score
`0`; values outside that tolerance receive a score strictly above the frozen
`2.5` threshold. This preserves the original constant-vs-change rule while
preventing floating-point residual noise from creating false alerts.

Z-score already had an explicit zero-variance branch; this erratum makes its
constant-series comparison use the same precision rule as EWMA. Isolation
Forest accepts zero-variance calibration features without numerical failure and
returns finite scores. A fully constant multivariate calibration matrix may be
non-informative to Isolation Forest, so no synthetic fallback or special
outcome-driven rule is added; its frozen sklearn settings remain unchanged.


## Erratum E2 — exact trace-row duplicate handling (2026-10-02)

This erratum is triggered by RCAEval trace data quality discovered during
Phase A Step 16 and recorded in commit `314cdbd`. It was not triggered by
RCA ranking results: ranking did not run because topology validation stopped
first.

The affected RE2-OB cases observed before this erratum were:

- `re2ob_recommendationservice_loss_1`: 48 duplicated
  `(traceID, spanID)` keys, 96 duplicate rows total.
- `re2ob_recommendationservice_loss_2`: 99 duplicated
  `(traceID, spanID)` keys, 198 duplicate rows total.

All duplicate rows observed in those two cases were exact full-row duplicates.
This rule applies uniformly to every evaluated RCAEval suite:
RE2-OB, RE2-SS, and RE2-TT. It must not be re-decided after held-out suites
are inspected.

Before trace-key validation, rows sharing the same `(traceID, spanID)` key
may be deduplicated only when every field in every row for that key matches.
For this equality check:

- ordinary values must compare equal field by field;
- null matches null;
- NaN matches NaN;
- null does not match NaN;
- any other field difference makes the duplicate conflicting.

For an all-identical duplicate-key group, retain one row and remove only the
additional identical copies. A duplicate-key group containing any conflicting
row remains a hard failure. No partial deduplication of a conflicting group is
permitted.
Every per-case topology evidence record must include:

- duplicate key count;
- duplicate row count;
- removed row count;
- whether any conflicting duplicate was found.

The aggregate results must list every affected case and its counts.

Any RCAEval baseline that reads traces, including multi-source BARO
(`mmBARO`) and multi-source CIRCA (`mmCIRCA`), must receive data under a
single documented policy for the full evaluation. The harness must explicitly
record whether each such baseline received raw traces or the same exact-row
cleaned traces used for SentinelOps topology construction. That policy must be
kept consistent across cases and suites.

This erratum changes only trace data-quality handling. It does not change any
detector threshold, ranking weight, graph direction, graph-hops setting,
PageRank damping, model parameter, random seed, calibration rule, or
evaluation metric.


## Erratum E3 — post-hoc RCA candidate allowlists (2026-10-02)

**Status: POST-HOC.** This amendment was added after inspecting the RE2-OB
trace-derived graph and candidate membership. Phase A Step 16 had already
produced unscored rankings at this point, but no AC@1, AC@3, AC@5, Avg@5,
Lift@5, or other RCA accuracy metric had been computed from those rankings.
Earlier diagnostics computed candidate-set sizes and analytical chance only;
they did not score any ranking against ground truth.

The reason for this amendment is benchmark design rather than any observed RCA
accuracy: service-mesh, proxy, health-check, load-generator, database, message
broker, and other infrastructure-only nodes are not admissible application
fault targets. Therefore every RCA method must be compared on the same frozen
application-service candidate set.
### E3.1 Uniform candidate filtering rule

Each suite has a frozen allowlist derived from its official demo-system
repository at the pinned revision listed below. For every method, the headline
ranking is obtained by a deterministic, order-preserving filter of the native
ranking to this allowlist.

The filter:
- preserves the relative order of all retained candidates;
- does not recompute scores, graphs, anomaly strengths, or model outputs;
- does not re-tune any threshold or parameter;
- does not use case-level outcomes;
- applies identically to SentinelOps, static threshold, random, PageRank,
  BARO, CIRCA, mmBARO, and mmCIRCA;
- leaves PageRank computation on the full frozen graph unchanged, then filters
  its ranking afterward.

Unfiltered/native rankings are retained and reported as a secondary table.
For RCAEval baselines, native results are also retained for the published-number
reproduction sanity check; the filtered ranking is used for the headline
cross-method comparison.
### E3.2 RE2-OB allowlist

Official system repository:
`GoogleCloudPlatform/microservices-demo@38e7348eb289eb5b87c0c6e8cb19ced0449dc389`
(Online Boutique v0.10.7 snapshot).

Frozen RE2-OB candidate labels are the 11 application/system services present
in every one of the 90 RE2-OB metric cases and mappable to the official
Online Boutique deployment:

- `adservice`
- `cartservice`
- `checkoutservice`
- `currencyservice`
- `emailservice`
- `frontend`
- `paymentservice`
- `productcatalogservice`
- `recommendationservice`
- `redis`
- `shippingservice`

Explicitly excluded observed mesh/infrastructure labels include
`InboundPassthroughClusterIpv4`, `PassthroughCluster`, `frontend-check`,
`frontend-external`, and `istio-init`. The official repo's
`loadgenerator` is also excluded because it is workload generation rather
than an admissible application root-cause target.
### E3.3 RE2-SS allowlist frozen before RE2-SS data access

Official system repository:
`microservices-demo/microservices-demo@9dff06fae4981921caec6a62393a6ebfce4b3e3f`.

Frozen Sock Shop application-service allowlist:

- `front-end`
- `carts`
- `catalogue`
- `orders`
- `payment`
- `queue-master`
- `shipping`
- `user`

Database and infrastructure deployments such as `carts-db`,
`catalogue-db`, `orders-db`, `user-db`, `session-db`, and
`rabbitmq` are excluded from RCA candidates. This allowlist is frozen here
without reading RE2-SS benchmark cases or labels.
### E3.4 RE2-TT allowlist frozen before RE2-TT data access

Official system repository:
`FudanSELab/train-ticket@313886e99befb94be6cd45f085c98e0019f59829`.

The frozen Train Ticket application-service allowlist is the set of top-level
official service modules at that revision:

`ts-admin-basic-info-service`, `ts-admin-order-service`,
`ts-admin-route-service`, `ts-admin-travel-service`,
`ts-admin-user-service`, `ts-assurance-service`, `ts-auth-service`,
`ts-avatar-service`, `ts-basic-service`, `ts-cancel-service`,
`ts-config-service`, `ts-consign-price-service`, `ts-consign-service`,
`ts-contacts-service`, `ts-delivery-service`, `ts-execute-service`,
`ts-food-delivery-service`, `ts-food-service`, `ts-gateway-service`,
`ts-inside-payment-service`, `ts-news-service`,
`ts-notification-service`, `ts-order-other-service`, `ts-order-service`,
`ts-payment-service`, `ts-preserve-other-service`,
`ts-preserve-service`, `ts-price-service`, `ts-rebook-service`,
`ts-route-plan-service`, `ts-route-service`, `ts-seat-service`,
`ts-security-service`, `ts-station-food-service`, `ts-station-service`,
`ts-ticket-office-service`, `ts-train-food-service`, `ts-train-service`,
`ts-travel-plan-service`, `ts-travel-service`, `ts-travel2-service`,
`ts-user-service`, `ts-verification-code-service`, `ts-voucher-service`,
`ts-wait-order-service`.

Database, tracing, monitoring, ingress/service-mesh, message-broker, and other
infrastructure-only components are excluded. This allowlist is frozen here
without reading RE2-TT benchmark cases or labels.
### E3.5 Chance and reporting

For RE2-OB, analytical Chance@k is recomputed using the frozen allowlist size
`N = 11`: `Chance@k = min(k, 11) / 11`.

The random sanity check compares empirical random AC@1/3/5 against those
analytical values using the frozen random seed policy and sampling uncertainty.
A disagreement beyond sampling noise remains a stop condition.

Primary RCA tables use filtered rankings. Secondary tables preserve the
unfiltered/native rankings for transparency. No threshold, ranking weight,
topology direction, PageRank damping, detector parameter, graph-construction
rule, or model parameter is changed by E3.


## Amendment A4 — POST-HOC static Online Boutique topology sensitivity (2026-10-02)

**Status: POST-HOC SENSITIVITY ONLY.** This amendment was added after the
RE2-OB trace-derived graph had been inspected. It does not replace or modify
the primary trace-derived RCA result. The primary Phase A RE2-OB graph remains
the frozen union of pre-injection trace edges.

The sensitivity graph is derived from the official Online Boutique repository:

`GoogleCloudPlatform/microservices-demo@38e7348eb289eb5b87c0c6e8cb19ced0449dc389`

Source: `release/kubernetes-manifests.yaml` service-address environment
variables at that revision. Only E3 RE2-OB allowlist nodes participate in this
sensitivity graph. The deployment name `redis-cart` is deterministically
mapped to the benchmark label `redis`. Optional `shoppingassistantservice`
and workload generator traffic are excluded because they are outside the E3
candidate allowlist.
Frozen static sensitivity edges, preserving the same caller -> dependency
direction as the primary graph:

- `frontend -> productcatalogservice`
- `frontend -> currencyservice`
- `frontend -> cartservice`
- `frontend -> recommendationservice`
- `frontend -> shippingservice`
- `frontend -> checkoutservice`
- `frontend -> adservice`
- `checkoutservice -> productcatalogservice`
- `checkoutservice -> shippingservice`
- `checkoutservice -> paymentservice`
- `checkoutservice -> emailservice`
- `checkoutservice -> currencyservice`
- `checkoutservice -> cartservice`
- `recommendationservice -> productcatalogservice`
- `cartservice -> redis`

This variant changes only the graph source for a separately labeled
sensitivity analysis. It does not change detector outputs, candidate allowlist,
ranking weights, primary-service bonus, PageRank damping, thresholds, random
seed, graph direction, RCA metrics, or any baseline parameter.

The variant must be reported separately as
`POST-HOC static-topology sensitivity`; it must never be substituted for the
primary trace-derived result or used to tune the primary method.

## Erratum E4 — RCAEval unranked fallback handling (2026-10-02)

**Status: PRE-SCORING ERRATUM.** This erratum was added after observing the pinned
RCAEval CIRCA wrapper emit an explicit failure warning and return an unranked
column-order fallback. No AC@1, AC@3, AC@5, Avg@5, Chance@5, Lift@5, bootstrap
confidence interval, or per-fault RCA score for the RCAEval baselines had been
computed before this erratum.

RCAEval method fallbacks that explicitly return an unranked/native column order
because graph construction or another algorithmic step failed are not valid RCA
rankings. The Phase A harness must detect such fallbacks from an explicit RCAEval
warning or method-specific fallback signal and record the per-case status as
fallback_unranked, together with a machine-readable fallback flag and reason.
A fallback must never be silently relabeled as ok merely because a list of
column names was returned.

For each RCAEval baseline, reporting must include valid-ranking coverage as both
a count and fraction of all 90 RE2-OB cases, plus counts of
fallback_unranked, hard failures, and any other skipped cases.

Primary RCA accuracy reporting uses the full fixed denominator of 90 RE2-OB
cases. Every fallback_unranked case counts as a miss at AC@1, AC@3, AC@5 and
Avg@5 rather than contributing its unranked column order. This preserves the
end-to-end failure cost of a baseline.

Secondary sensitivity reporting computes the same accuracy metrics over valid
rankings only, with the reduced denominator stated explicitly. It is labeled
valid-rankings-only and must not replace the primary all-90 result.

This erratum changes only failure classification and reporting. It does not
change candidate allowlists, input data, time windows, preprocessing, model or
algorithm parameters, graph construction, ranking logic for successful cases,
random seeds, ground truth, or the frozen SentinelOps method.


## Erratum E5 — preserve complete native RCA ranking before E3 filtering (2026-10-03)

**Status: PRE-SCORING FOR SENTINELOPS AND ALL NON-RANDOM BASELINES;
AC@k HAD BEEN OBSERVED FOR THE RANDOM BASELINE ONLY.** This erratum records implementation commit
`f0e1f4184486804889b5a6f9dab2f6424fe0e69f` and evidence refresh commit
`6de02601bfa8d60f154b1480e0768f0a3c08e754`. It is being committed before
any additional AC@k computation in this continuation.

The old Step 16 harness requested `max_candidates=5` when saving the native
SentinelOps ranking. E3 requires an order-preserving candidate-allowlist filter
before headline top-k selection. Saving only five native services could let an
excluded infrastructure service consume a saved slot and hide the next eligible
application service. The fix requests `max_candidates=len(strengths)` and
preserves the complete native ranking; E3 filtering precedes headline top-k
selection. The production engine default remains five. This explicitly corrects
Section 13's five-candidate limit for benchmark evidence retention only.

The reason is conformance to E3's filtering rule, not improved accuracy.
The implementation diff changes only the output-length argument and its
explanatory comment. The refresh records all 90 complete rankings without
changing detector inputs, topology, candidate allowlists, or the scoring
function. No weights, thresholds, score formula, score rounding, primary-service
selection, or tie-breaking changed. The existing descending rounded score and
lexical service-name tie-break remain intact.

The reproducible comparison uses `f0e1f41^` as the before revision and
`6de0260` as the after revision:
- [All 90 case comparisons](phase_a/re2ob/E5_RANK_COMPARISON.md).
- [Full before/after rows and audit summary](phase_a/re2ob/e5_rank_comparison.json).
- Command: `.venv/bin/python scripts/phase_a_e5_rank_comparison.py`.

All 90 native saved five-row prefixes match the new prefixes exactly, including
every score component and original rank number. The old E3-filtered saved ranking
contained five services in 83 cases and four in seven cases. All refreshed
E3-filtered rankings contain all 11 allowlisted services; seven filtered top-five
lists gain the previously hidden fifth service. Native lengths are 11 in two
cases, 12 in 85, 13 in two, and 14 in one. The comparison reads no ground-truth
labels and computes no accuracy metrics.

### E5.1 Observed-results disclosure and stop condition

The requested statement "before any AC@k" cannot be made for all methods:
`47a80d6` already committed random AC@1/3/5 in
`random_vs_chance_sanity.json`, and `6a77334` committed an additional
random multi-seed diagnostic before either E5-covered commit. Those artifacts
remain unchanged. The random sanity record has `sanity_pass: false`; its
AC@3 falls outside its recorded 95% sampling interval. The multi-seed artifact
is diagnostic-only and does not itself amend or revoke E3's stop condition.

No SentinelOps or RCAEval-baseline AC@k result artifact was found in the checkout
at this continuation's start; their saved rankings were unscored. The change is
structurally justified by E3 and is not result-motivated, but earlier random
accuracy results were already available and must not be concealed. No RE2-SS
or RE2-TT data is inspected by this audit.

Under the unchanged E3 stop rule, subsequent accuracy scoring and Steps 21–24
remain gated on resolution of the existing random-sanity stop condition and
receipt of the original step checklist. The background CIRCA/mmCIRCA jobs are
left running without restart or termination.

### E5.2 Explicit relative-order and timing clarification (2026-10-03)

The changes in f0e1f41 and 6de0260 were made before AC@k was computed
for SentinelOps or any non-random baseline, according to the available
committed evidence. AC@k had been observed for the random baseline ONLY:
the seed-42 sanity check in 47a80d6. The subsequent random-only multi-seed
diagnostic in 6a77334 had also been observed and is disclosed in E5.1;
it cannot be omitted from the provenance or presented as clearing the stop.

The before/after comparison covers all 90 RE2-OB cases. Projecting the new
E3-filtered ranking onto the candidates present in the old E3-filtered
ranking gives the old order exactly in 90/90 cases: zero relative-order
differences. The native saved prefixes and their scores are also identical
in 90/90 cases. The seven completed fifth slots are additions, not
reordering. The old full tail was not saved, so no claim is made about
comparing unavailable before-tail rows.

No weights, thresholds, scoring, or tie-breaking changed. This audit reads
no ground-truth labels and computes no AC@k. The supplied Steps 21-25
checklist is now available; the E3 random-sanity stop remains unresolved.


## Erratum E6 - pre-registered uncertainty and metric definitions (2026-10-03)

**Status: PRE-REGISTERED BEFORE SENTINELOPS OR NON-RANDOM BASELINE SCORING.**
Committed after E5 and before Steps 21-24. Previously observed random-only
accuracy diagnostics are disclosed in E5. No other accuracy results are used
to choose these definitions or uncertainty rules.

### E6.1 Metrics and denominators

For a case with one ground-truth root service, service-level AC@k is the
indicator that the root service occurs in the first k distinct services of
the ranking. Aggregate AC@k is the mean of those case indicators.
Apply the same E3 order-preserving candidate filter before every top-k
selection, for SentinelOps, threshold, random, PageRank, BARO, CIRCA,
mmBARO, and mmCIRCA. Retain the native rankings separately.

Avg@5 = (AC@1 + AC@2 + AC@3 + AC@4 + AC@5) / 5.
Chance@5 = min(5, N) / N, with N = 11 for the frozen RE2-OB allowlist,
so Chance@5 = 5/11. Lift@5 = AC@5 / Chance@5.
This requested ratio is calculated explicitly; it is not the local
RCAEval Evaluator.lift() function, which calculates an additive difference
between average accuracy and average chance. No ranking score changes.

Under E4, primary metrics retain all 90 cases. fallback_unranked is a
miss at every k and therefore contributes zero to Avg@5; its returned
column order is never scored. Coverage and hard failures are reported
separately. A missing, malformed, or unexplained hard-failure record is
a validation stop, not silently removed or converted to success.

Report a secondary valid-rankings-only table for each method, giving its
explicit reduced denominator overall and for every fault type. It never
replaces the all-90 primary table. A group with no valid cases has null
accuracy and interval values, not invented zero-denominator estimates.

### E6.2 Paired case bootstrap

Freeze bootstrap seed 42, 10,000 resamples, and 95% percentile intervals
(the 2.5th and 97.5th percentiles, linear quantile interpolation).
Case IDs are sorted lexically. Use numpy.random.default_rng(42) and draw
a 10,000 by 90 index matrix, sampling 90 cases with replacement in each
row. Each sampled case carries all of its outputs. Use this one matrix
for every primary method, metric, and paired overall comparison.
Random rankings are generated once with their frozen seed 42 and are
never redrawn within a bootstrap.

For each baseline and k in 1, 3, 5, report the point difference
Delta_k = AC@k(SentinelOps) - AC@k(baseline).
For each shared resample b compute Delta_k_b from the two methods on
exactly the same sampled cases, equivalently the mean of their paired
per-case indicator differences. Report the 95% percentile CI of those
10,000 differences. Do not subtract marginal CI endpoints or use
independently resampled methods.

Apply case bootstrap also to individual-method AC@1/3/5, Avg@5, and
Lift@5. Chance@5 is the fixed analytical value. Report point estimates
and CIs overall and separately for CPU, memory, disk, socket, delay,
and loss, preserving native fault names in machine-readable evidence.
For each fault, start a separate default_rng(42), sort that fault's
case IDs, and sample its original case count with replacement 10,000
times. Reuse that fault's index matrix across methods and paired
differences. This avoids changing the overall cohort through stratified
resampling.

Secondary valid-only method intervals resample only that method's
valid cases with the same seed/resample/percentile rules. If secondary
paired differences are reported, both methods must use their common
valid-case intersection, the same sampled indices, and an explicit
denominator; never compare differently selected cohorts.

No significance, superiority, or inferiority claim is made without the
corresponding paired CI. A CI including zero does not establish a
directional difference. These are descriptive unadjusted 95% intervals;
they do not establish family-wise significance over multiple comparisons.

### E6.3 A4 and evidence gates

A4 static Online Boutique topology sensitivity uses the same frozen E3
filter, random seed 42, bootstrap seed 42, and uncertainty rules. Keep it
in separately labeled evidence and never substitute it for the primary
pre-injection trace-derived topology result. All other settings remain
frozen; A4 changes only the documented sensitivity topology.

Steps 21-24 are authorized by the supplied checklist, but remain gated:
E5 and E6 must be committed; CIRCA and mmCIRCA must finish; fallback
counts and coverage must be validated; and existing stop rules must
be satisfied. E3's seed-42 random-sanity stop remains unresolved at
registration. This document does not waive or reinterpret it.
Stop at Step 25 and present RE2-OB results before any RE2-SS/RE2-TT
access. Never push.


## Erratum E7 - agreed random diagnostic gate resolution (2026-10-03)

**Status: COMMITTED BEFORE STEP 21 AND BEFORE NON-RANDOM AC@k SCORING.**
This erratum records the diagnostic acceptance rule agreed after the
seed-42 sanity failure was observed but before the 1000-seed diagnostic
ran. Its timing and authorization are confirmed by the user's gate
resolution instruction in this session. It is a post-failure diagnostic
rule, not a rule frozen before the seed-42 result was observed.

The agreed rule: run 1000 diagnostic master seeds (0-999). The mean
AC@1/3/5 must each be within 3 standard errors of the corresponding
analytical Chance@k; native rankings must be full permutations and E3
must preserve retained order; service mean ranks must be uniform
(the recorded tolerance is 0.10 around the expected rank 6.0).
Otherwise stop. Position chi-square p-values are descriptive, not
an additional acceptance gate.

The previously committed random_multiseed_diagnostic.json records
diagnostic_pass=true, full_permutation_check.pass=true,
e3_filter_check.pass=true and positions_roughly_uniform=true.
All 90,000 case/seed permutations and E3 projections passed.

| Metric | 1000-seed mean | Across-seed SD | SE of mean | Analytical Chance@k | Difference in SE |
|---|---:|---:|---:|---:|---:|
| AC@1 | 0.090167 | 0.029837 | 0.000944 | 0.090909 | -0.786860 |
| AC@3 | 0.270244 | 0.047123 | 0.001490 | 0.272727 | -1.666166 |
| AC@5 | 0.454222 | 0.053410 | 0.001689 | 0.454545 | -0.191376 |

The maximum absolute service mean-rank deviation is
0.015511111111111475 (0.01551), within the recorded 0.10 tolerance.
All three mean differences are within 3 SE. Under the agreed rule,
the random diagnostic gate is resolved and Steps 21-24 may proceed.

The seed-42 sanity_pass=false remains an unchanged historical value.
Seed 42 remains the reported random baseline; its rankings are never
replaced, regenerated, or redrawn in bootstrap resamples. Report its
AC@1/3/5 beside the diagnostic-only 1000-seed means and across-seed SDs.
The diagnostic mean is not a replacement baseline.

Verified git log 6de0260..fdd5d74 contains only fdd5d74, the E5
documentation and label-free rank audit commit. Its four changed paths
are the evaluation specification, E5_RANK_COMPARISON.md,
e5_rank_comparison.json, and phase_a_e5_rank_comparison.py.
The audit explicitly records ground_truth_read=false and
accuracy_metrics_computed=false. The range contains no scoring or
AC@k result output for any non-random method. Existing random-only
observations are disclosed in E5 and remain intact. This is a statement
about committed contents, not proof of every historical shell command.

This explicit gate resolution supersedes the unresolved E3 gate status
recorded at E5/E6 registration and in PRE_STEP21_STOP.md; those records
remain historical. No weights, thresholds, scoring, tie-breaking,
candidate allowlist, seed, or baseline method changes. E4 fallback
treatment, E6 uncertainty rules and all other stop rules remain in force.
RE2-SS and RE2-TT remain untouched. Never push. Stop at Step 25.
