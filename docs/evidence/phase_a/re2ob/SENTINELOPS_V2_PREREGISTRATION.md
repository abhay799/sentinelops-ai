# SentinelOps v2 Post-hoc Preregistration

Date: 2026-10-03
Status: **PREREGISTERED BEFORE ANY v2 CODE OR v2 RUN**

This document defines a post-hoc SentinelOps RCA diagnostic variant after the
frozen v1 RE2-OB result was observed. It is not a replacement for v1 and must
not be presented as if it were pre-registered before v1 evaluation.

At this commit, no SentinelOps v2 implementation has been written or executed.
No RE2-SS or RE2-TT raw data may be downloaded, opened, scored, or used for
variant selection until a v2 variant is selected on RE2-OB and frozen in a
separate commit.

## 1. Verified source of the 1.0 saturation

The saturation occurs before RCA weighting, in the continuous detector-score
path:

1. `normalize_scores_from_calibration` derives calibration `low` and `high`.
   For non-degenerate calibration ranges it computes
   `(score - low) / (high - low)` and then applies `np.clip(..., 0.0, 1.0)`.
   For `high == low`, the frozen rule returns exactly 0.0 or 1.0.
2. `ensemble_two_of_three` averages the three calibration-normalized component
   scores (z-score, EWMA, Isolation Forest). Because each component is bounded
   at 1.0, the service continuous score is bounded at 1.0.
3. `summarize_detection_case` records `fault_max_anomaly_strength` as the
   maximum service continuous score over the entire fault window.
4. Step 16 passes that value directly to `sentinelops_continuous_ranking` as
   the service `anomaly_strength`.

Saved RE2-OB evidence shows that 86/90 cases have at least one E3-eligible
service with `anomaly_strength == 1.0`; 78/90 cases have a top-strength tie.
Thus the exact-1 saturation originates in normalization/clipping plus the
fault-window maximum, not in RCA-score rounding or E3 filtering.

## 2. V2a - unclipped continuous strength

V2a changes only the continuous strength used by RCA. Detector parameters,
binary detector flags, the 2-of-3 vote, calibration split, graph construction,
RCA weights, candidate allowlist, E3 filtering, seeds, bootstrap settings, and
all baseline methods remain unchanged.

For each detector component with a non-degenerate calibration range
`high > low`, define the RCA-only continuous normalized score as:

`u = (score - low) / (high - low)`

with **no lower or upper clipping**. Values below 0 or above 1 are retained.
For the degenerate case `high == low`, retain the frozen constant-calibration
rule: 0.0 when the score does not exceed the calibration constant and 1.0 when
it does. No new scale or epsilon is introduced for this case.

At each timestamp, V2a service continuous score is the arithmetic mean of the
three component `u` values. V2a service strength is the maximum of this score
over the frozen fault window, exactly where v1 currently takes the maximum of
the clipped ensemble score.

The RCA anomaly-strength weight remains `0.45`; graph-impact weight remains
`0.20`; primary-service-bonus weight remains `0.10`; change signal remains 0.
RCA score rounding remains six decimals. V2a preserves the current v1
primary-bonus selection rule, including its existing service-name fallback,
so V2a isolates the effect of removing continuous-score clipping.

## 3. V2b - V2a plus non-name primary-bonus tie resolution

V2b uses exactly the V2a continuous strength and the same frozen RCA weights.
It changes only how the existing primary-service bonus is assigned when the
v1 clipped strength produces a tied maximum group.

For a case:
1. Form the tied primary-candidate group using the frozen v1 clipped
   `anomaly_strength` maximum.
2. If the group has one service, primary-bonus behavior is unchanged.
3. If the group has multiple services, choose the service with the highest
   full-precision V2a unclipped continuous strength (`raw strength`) rather
   than using service name.
4. If two or more tied services also have exactly equal full-precision raw
   strength, assign the primary bonus to none of those services. Do not use
   service name, candidate order, graph impact, ground truth, or any new
   heuristic to break that remaining tie.

The final RCA row ordering rule remains descending six-decimal `rca_score` and,
only for exact final score equality, service name ascending. V2b removes the
name-based decision specifically from **primary-bonus assignment**; it does not
change the existing deterministic presentation/order fallback for equal final
RCA scores.

## 4. Evaluation and selection rule frozen before any v2 run

Both V2a and V2b will be evaluated only on the same 90 RE2-OB cases already
used by v1, with the frozen E3 11-service allowlist and the same ground-truth
service labels used by Step 21 scoring. No case may be added, removed, or
reweighted after seeing v2 results.

For each variant report AC@1, AC@2, AC@3, AC@4, AC@5 and
`Avg@5 = mean(AC@1..AC@5)`, plus the existing Chance@5 and Lift@5 definitions.
Also report per-fault breakdowns and the raw per-case ranking evidence.

Variant selection is based on the **all-90 primary RE2-OB Avg@5 point estimate**:
- if V2a Avg@5 > V2b Avg@5, select V2a;
- if V2b Avg@5 > V2a Avg@5, select V2b;
- if the Avg@5 point estimates are exactly equal, select V2a as the simpler
  variant.

A paired 95% case-bootstrap CI for `Avg@5(V2b) - Avg@5(V2a)` must be reported
using the frozen bootstrap seed 42, 10,000 resamples, the same sorted 90 cases,
and the same sampled case indices for both variants. Per case, Avg@5 contribution
is the mean of that case's AC@1..AC@5 indicators. The CI is descriptive and must
be shown regardless of which variant is selected; it is not an additional
selection gate and must not be used to change the rule after results are seen.

For transparency, paired comparisons of each v2 variant against frozen v1 may
also be reported using the same shared-resample procedure. They do not affect
which v2 variant is selected.

If either variant fails implementation validation, changes a frozen input or
parameter outside the definitions above, reads held-out data, or cannot be
recomputed deterministically, stop rather than silently redefining the variant.

## 5. Reporting status and held-out gate

Frozen v1 remains the **primary Phase A result**. Any selected v2 result is
post-hoc and must be reported beside v1 with an explicit `post-hoc v2` label;
it may not replace, overwrite, or relabel the v1 RE2-OB result.

After V2a and V2b are run and the selection rule above is applied, the selected
v2 definition, implementation commit, RE2-OB results, and validation evidence
must be frozen in a separate commit **before any RE2-SS or RE2-TT raw data is
accessed**. Until that freeze commit exists, RE2-SS and RE2-TT remain untouched.

No detector threshold, EWMA alpha, Isolation Forest contamination, detector
vote rule, calibration split, RCA weight, graph setting, E3 allowlist, random
seed, bootstrap seed, fallback policy, or baseline method may be changed as part
of v2. No push is authorized.

## Addendum A - numerical handling, diagnostics, and comparison scope

Date: 2026-10-03
Status: **COMMITTED BEFORE ANY v2 CODE OR v2 RUN.**

This addendum is part of the v2 preregistration and is frozen before implementation.
It does not create a third variant. Exactly two variants are permitted: V2a and V2b.
No additional v2 variant, threshold, transform, clipping rule, tie heuristic, or
selection criterion may be introduced after any v2 result is observed.

### A1. V2a non-finite and extreme-value handling

Raw RCAEval metric preprocessing is unchanged from v1: NaN and +/-inf metric
values are converted to missing, chronologically forward-filled, and any leading
missing values are filled with 0 before the frozen calibration/evaluation split.
No v2-specific imputation is added.

For each detector component's calibration-score vector, the existing E1
machine-precision constant/min-range rule remains authoritative:

`tol = 8 * eps_float64 * max(1, max(abs(calibration_scores)))`

If `max(calibration_scores) - min(calibration_scores) <= tol`, V2a treats the
calibration score range as numerically constant and retains the frozen
constant-series rule: normalized RCA-only strength is 0.0 when the evaluated
score is within the tolerated calibration reference and 1.0 when it exceeds
that reference. No epsilon denominator or fitted floor is introduced.

For a non-constant calibration-score range, V2a computes the unclipped finite
value `(score - low) / (high - low)`. Finite values are retained exactly even if
they are negative or very large; there is no clipping, winsorization, capping,
log transform, rescaling, or post-hoc outlier rule.

All calibration component scores and all derived V2a component, timestamp,
service, and case strengths must be finite. If any NaN or +/-inf is produced
after preprocessing/arithmetic, the case is a hard validation failure and the
v2 run stops; the value must not be replaced, capped, dropped, or silently
excluded.

V2a strength distribution will be reported before interpretation over all
E3-eligible service strengths across all 90 RE2-OB cases, including: count,
finite count, min, p01, p05, p25, median, p75, p95, p99, max, count/fraction <0,
count/fraction exactly 0, count/fraction exactly 1, and count/fraction >1. The
same summary will also be reported for each case's maximum V2a service strength.

### A2. Effective balance disclosure

Although the numerical RCA weights are unchanged, V2a changes the scale of the
anomaly-strength input by removing clipping. Therefore V2a can change the
**effective balance** between the anomaly term and the graph-impact/primary-bonus
terms even with weights fixed at 0.45, 0.20, and 0.10. This is an intended,
explicit consequence of V2a and must be disclosed with results; unchanged
weights must not be described as unchanged effective contribution.

### A3. Required tie and top-1 diagnostics

For frozen v1, V2a, and V2b, report beside Avg@5:
- AC@1 overall;
- top-tie case count;
- AC@1 among cases with a top tie;
- AC@1 among cases without a top tie.

For this table, a `top tie` means more than one E3-eligible service has exactly
the maximum full-precision anomaly strength used in that variant's RCA anomaly
term. V1 uses its frozen clipped anomaly strength. V2a and V2b use the same
unclipped V2a anomaly strength, so their top-tie case counts are expected to be
identical even though primary-bonus assignment may differ. For V2b, additionally
report the number of cases in which the frozen v1 clipped primary-candidate
group contains more than one service, because that is the group on which V2b's
raw-strength primary-bonus rule operates.

The already-frozen variant-selection rule remains unchanged: all-90 RE2-OB
Avg@5 point estimate selects between V2a and V2b, with exact ties selecting the
simpler V2a. AC@1 and tie diagnostics are descriptive only and cannot alter the
selection.

### A4. Development-result and paired-comparison scope

All v1/V2a/V2b scores on RE2-OB are development-suite results. RE2-OB has already
been used for diagnosis, preregistration, and variant selection and must not be
called held-out. Only RE2-SS and RE2-TT remain held-out for later evaluation,
and neither may be accessed before the selected v2 is frozen.

Using the same sorted 90 RE2-OB cases, bootstrap seed 42, 10,000 shared paired
case resamples, and 95% percentile intervals, report paired differences for
AC@1, AC@3, AC@5, and Avg@5 for:
- V2a minus frozen v1;
- V2b minus frozen v1;
- V2a minus the frozen static-threshold baseline;
- V2b minus the frozen static-threshold baseline;
- V2b minus V2a (including the preregistered Avg@5 selection comparison).

All paired CIs are descriptive. No significance threshold, CI-crossing rule, or
baseline-comparison result may override the frozen V2a/V2b selection rule.

### A5. Variant-count lock

There are exactly two post-hoc SentinelOps v2 variants: V2a and V2b. Once any
v2 result is computed, no V2c, alternate transform, alternate tie policy,
parameter sweep, weight change, detector change, or additional candidate variant
may be introduced in this Phase A selection exercise. If both variants expose a
problem not covered by this preregistration, record the limitation and stop; do
not create another variant using RE2-OB outcomes.
