# Step 27 RE2-TT Preflight

Date: 2026-10-03
Status: **FROZEN BEFORE ANY RE2-TT RAW-DATA ACCESS**

Repository checkpoint at entry: `bdc9dc0dbc72caf1348c2dd948acce59656bbcea`.
The working tree was clean and no Phase A benchmark worker was running.
No `re2tt_*` raw case directory existed in the pinned Hugging Face checkout.

## Train Ticket revision and E3 allowlist

Frozen official system repository:
`FudanSELab/train-ticket@313886e99befb94be6cd45f085c98e0019f59829`.
The exact commit resolves upstream (commit title `Hotfix (#243)`).

At that revision there are 47 top-level `ts-*` directories. The frozen E3.4
allowlist contains 45 application services and matches the upstream service
modules exactly after excluding the two support/non-candidate modules
`ts-common` and `ts-ui-dashboard`. No frozen allowlist entry is missing from
that upstream revision.

After TT download, comparing benchmark ground-truth service labels with this
already-frozen allowlist is a validity/mapping check only. It may detect a
schema/name mismatch and stop the run; it may not add, remove, rename, tune, or
reweight candidates based on held-out outcomes.

## Frozen Step 27 method set

The numerical comparison methods are:
1. frozen SentinelOps v1;
2. frozen selected post-hoc V2a from commit `d840a5a`;
3. static-threshold baseline;
4. random baseline, master seed 42 with the frozen stable per-case seed rule;
5. PageRank, damping 0.85, using the frozen TT suite topology and v1 anomaly
   strength personalization;
6. BARO;
7. CIRCA.

`mmBARO` and `mmCIRCA` remain `n/a (outside pinned input contract)` for Step 27.
The pinned Phase A input contract is the exact Hugging Face dataset revision
`afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`; no held-out raw-to-`logts.csv`/
`tracets_*.csv` preprocessing will be invented or substituted from an external
archive after the evaluation has begun. This is an input-contract decision,
not a result-dependent exclusion.

## Frozen TT topology rule

RE2-TT follows Section 12.1 of the frozen spec:
- build one static suite graph from the union of parent-service -> child-service
  edges observed only in timestamps before each case's `inject_time`;
- exact duplicate trace rows follow Erratum E2;
- remove self-edges;
- never use post-injection trace behavior or root-cause labels to create or
  weight edges;
- if the pinned TT trace schema cannot support unambiguous extraction, stop
  rather than inventing topology.

## Frozen scoring and uncertainty

Use the same E3/E4/E6 rules as prior suites:
- deterministic order-preserving E3 filtering to the 45-service TT allowlist;
- `fallback_unranked` counts as a miss in the primary all-case denominator and
  is excluded only from the valid-only secondary view;
- AC@1..AC@5, Avg@5, Chance@5, Lift@5;
- paired differences for numerical methods;
- overall and per-fault 95% percentile case-bootstrap intervals;
- bootstrap seed 42, 10,000 resamples, shared case-index draws for paired
  comparisons;
- random rankings are drawn once and never redrawn inside bootstrap;
- report coverage, fallbacks, hard failures, per-fault results, and V2a strength
  distribution.

No method, threshold, graph rule, detector parameter, RCA weight, candidate
rule, fallback rule, seed, or bootstrap rule may change after TT results are
seen. Any necessary protocol change requires a dated amendment and an explicit
stop before rerun.

Step 28 is reserved for final Phase A consolidation/certification after Step 27
is frozen. Never push.
