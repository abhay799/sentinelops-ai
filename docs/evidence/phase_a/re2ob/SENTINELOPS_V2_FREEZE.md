# SentinelOps v2 RE2-OB Freeze

Date: 2026-10-03
Status: **POST-HOC V2 FROZEN AFTER RE2-OB DEVELOPMENT EVALUATION**

Preregistration commits:
- `cd296da` - initial post-hoc SentinelOps v2 preregistration.
- `cfccd10` - numerical/tie/comparison addendum committed before any v2 code/run.

Exactly two variants were implemented and evaluated: V2a and V2b. No third
variant was created. Frozen v1 remains the primary Phase A result; this v2 is a
post-hoc development result reported beside it.

## Exact implementation and commands

V2-only implementation files in this freeze commit:
- `src/sentinelops/evaluation/rcaeval_v2.py`
- `scripts/phase_a_v2_re2ob.py`
- `scripts/phase_a_v2_report.py`
- `tests/test_phase_a_v2.py`

V1 detector/RCA implementation paths were not modified for v2.

Commands used:
- `.venv/bin/python scripts/phase_a_v2_re2ob.py --variant v2a --workers 4`
- `.venv/bin/python scripts/phase_a_v2_re2ob.py --variant v2b --workers 4`
- `.venv/bin/python scripts/phase_a_v2_report.py`

Both V2a and V2b completed 90/90 RE2-OB cases with no non-finite validation
failure. The report used bootstrap seed 42, 10,000 shared paired case resamples,
and 95% percentile intervals exactly as preregistered.

## Overall RE2-OB development results

| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Top ties | AC@1 with tie | AC@1 without tie |
|---|---:|---:|---:|---:|---:|---:|---:|
| frozen v1 | 0.211111 | 0.744444 | 0.966667 | 0.682222 | 78 | 0.153846 | 0.583333 |
| V2a | 0.844444 | 0.966667 | 1.000000 | 0.946667 | 0 | n/a | 0.844444 |
| V2b | 0.844444 | 0.966667 | 1.000000 | 0.946667 | 0 | n/a | 0.844444 |
| threshold baseline | 0.866667 | 0.966667 | 1.000000 | 0.955556 | n/a | n/a | n/a |

V2b's frozen-v1 clipped primary-candidate group still had multiple services in
78/90 cases, but V2a and V2b produced identical AC@k/Avg@5 outcomes.

## Frozen selection

V2a and V2b have exactly equal all-90 RE2-OB Avg@5 point estimates:
`0.9466666667`. Under the preregistered exact-tie rule, **V2a is selected** as
the simpler variant. AC@1 and tie diagnostics do not affect this selection.

## Paired comparisons

V2a minus frozen v1:
- AC@1: +0.633333, 95% CI [0.533333, 0.733333]
- AC@3: +0.222222, 95% CI [0.133333, 0.311111]
- AC@5: +0.033333, 95% CI [0.000000, 0.077778]
- Avg@5: +0.264444, 95% CI [0.213333, 0.317778]

V2a minus threshold baseline:
- AC@1: -0.022222, 95% CI [-0.055556, 0.000000]
- AC@3: 0.000000, 95% CI [-0.033333, 0.033333]
- AC@5: 0.000000, 95% CI [0.000000, 0.000000]
- Avg@5: -0.008889, 95% CI [-0.026667, 0.006667]

V2b minus V2a is exactly 0.0 for AC@1, AC@3, AC@5, and Avg@5, with
95% CIs [0.0, 0.0] for all four. V2b-versus-v1 and V2b-versus-threshold are
therefore numerically identical to the V2a comparisons above.

## V2a strength distribution and scale limitation

All 990 E3-eligible service strengths are finite. None are negative, zero, or
exactly 1.0. 774/990 = 78.18% are greater than 1.0.

All-service V2a strengths:
- min 0.309699
- p01 0.502578
- p05 0.751949
- p25 1.040571
- median 1.638322
- p75 12.375055
- p95 1098.324942
- p99 20315.627619
- max 1493742.221593

Per-case maximum V2a strengths (90 values):
- all 90 are finite and >1.0
- min 3.712877
- median 693.805179
- p95 29105.523814
- p99 458995.404204
- max 1493742.221593

This heavy tail is retained exactly under the preregistration. No clipping,
winsorization, log transform, rescaling, or third variant is introduced after
seeing these values. It also confirms the preregistered disclosure that, despite
unchanged numerical RCA weights, removing clipping materially changes the
effective balance of the anomaly-strength term relative to graph/bonus terms.

## Validation

Fresh validation after the completed v2 runs:
- `.venv/bin/ruff check .` -> PASS.
- `.venv/bin/python -m pytest -q` -> 142 passed, 1 skipped.
- the skip is the existing live-local-infrastructure integration test requiring
  PostgreSQL, Redis, and Kafka.
- `git diff --check` -> PASS.
- `tests/test_phase_a_v2.py` contains the regression that reconstructs all 90
  frozen v1 Step-16 RCA JSON payloads through the original v1 ranking function
  and compares serialized bytes; all 90 are byte-identical.

The only post-result code edit was a report-rendering fix that displays `n/a`
when a tie subgroup is empty; it did not alter metrics, bootstraps, rankings,
variant definitions, or selection logic.

## Held-out gate

RE2-OB is development data. Only RE2-SS and RE2-TT remain held out. No held-out
raw suite was started as part of v2. After this freeze commit, any later held-out
run must use the selected frozen V2a implementation without further RE2-OB-driven
variant creation or tuning. Never push.
