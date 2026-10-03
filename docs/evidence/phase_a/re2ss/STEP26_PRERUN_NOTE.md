# Step 26 RE2-SS Pre-run Note

Date: 2026-10-03
Status: **COMMITTED BEFORE RE2-SS DOWNLOAD OR RAW-DATA ACCESS**

Step 26 evaluates the held-out RE2-SS suite at the already pinned RCAEval code
and Hugging Face dataset revisions. No RE2-SS result may be used to tune a
method, alter the candidate allowlist, change topology, change detector/RCA
parameters, or create another v2 variant.

## Frozen method set

The only methods to run are:
1. frozen SentinelOps v1;
2. frozen selected post-hoc V2a from commit `d840a5a` (V2b is not run);
3. static-threshold baseline;
4. random ranking with frozen master seed 42 and stable per-case derivation;
5. PageRank on the frozen static Sock Shop topology;
6. BARO;
7. CIRCA;
8. mmBARO;
9. mmCIRCA.

No method may be added, removed, tuned, or substituted after RE2-SS results are
seen. If a necessary protocol or implementation change is discovered, stop and
record a dated amendment before any rerun; do not silently continue.

## Frozen evaluation rules

- Apply the E3 frozen RE2-SS allowlist as an order-preserving candidate filter
  before headline top-k scoring; preserve native/full rankings separately.
- Apply E4 fallback classification exactly: `fallback_unranked` is not scored as
  its returned column order; primary all-case scoring counts it as a miss, and
  valid-ranking-only secondary coverage is reported separately.
- Apply E6 metric definitions and uncertainty rules unchanged.
- Case IDs are sorted lexically for scoring/bootstrap.
- Bootstrap seed = 42; resamples = 10,000; percentile CI = 95%.
- One shared 10,000 x 90 case-index matrix is used for primary overall method
  intervals and paired differences. Random rankings are generated once and are
  never redrawn inside bootstrap iterations.
- Per-fault intervals use the same E6 separate-fault resampling rule.
- Report AC@1, AC@3, AC@5, Avg@5, Chance@5, Lift@5, paired method differences,
  per-fault breakdowns, raw ranking evidence, coverage, fallbacks and hard
  failures.
- RE2-SS is held-out evaluation data. Smoke-test output may validate adapter and
  runtime behavior only and may not select thresholds, weights, features,
  mapping rules, topology, or algorithm settings.

RE2-TT remains untouched throughout Step 26. Never push.
