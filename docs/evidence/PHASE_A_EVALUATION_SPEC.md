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
