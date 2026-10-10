# Step 28 Gap-Closure Audit

**Scope:** documentation/integrity audit only. No certified numerical result, frozen case output, or ranking artifact is changed.

## A15 — Step 27 script integrity proof

Frozen comparison commit: `c4c42241ed9f89ff05b923798078846c57de5e56`.

### Scorer change classification

`scripts/phase_a_step27_score.py` differs only in:

1. **resume/status/reporting:** add `timeout_unranked` as an explicit coverage field and remove it from `other_statuses`;
2. **reporting:** add Timeout to the markdown output table and explanatory text.

The scoring functions `case_hits`, `metrics`, bootstrap CIs, paired-difference math, per-fault math, all-90 denominator, and valid-only rule are unchanged.

### Runner change classification

`scripts/phase_a_step27_rcaeval_run.py` differs only in:

1. **timeout:** add the fixed 1800-second CIRCA wrapper and emit `timeout_unranked`;
2. **other/execution plumbing:** multiprocessing worker and one-way Pipe used to return a CIRCA result from the child process;
3. **resume/status:** recognize cached `timeout_unranked` as terminal and count timeout outcomes in the run summary.

No SentinelOps ranking rule, RCAEval method parameter, topology, SLI, allowlist, or ground-truth use changes in these hunks.

### Metric regression

A temporary regression loaded the scorer at `c4c4224` and the committed scorer, then applied both implementations to the same 90 saved RE2-TT cases for all seven runnable methods.

Canonical metric payload compared:
- overall all-90 metrics
- primary 95% bootstrap CIs
- paired differences
- per-fault metrics
- valid-ranking-only metrics

Result:

- frozen metric bytes: 16,441
- committed metric bytes: 16,441
- byte-identical: **true**
- canonical metrics SHA-256: `461ff2d8ae39733e13d816efde81720971106237d6e243b5d60d66d373483ee0`

The regression was executed from `/tmp`; it did not write any certified output.

### Runner provenance by method

- v1, V2a, threshold, random, PageRank: `scripts/phase_a_step27_run.py`, frozen SHA-256 `f22505e4a522a6a478fa33fbcfcaf67ccc4c79969908a5f6171ac1a2025d9c7a`.
- BARO: native RCAEval path through `scripts/phase_a_step27_rcaeval_run.py`; the timeout amendment is CIRCA-only, so BARO ranking behavior is the frozen native runner behavior.
- CIRCA: native RCAEval path through the amended Step 27 runner recorded at SHA-256 `fdee1bc33ba59a9d70a9cfa566f461110fcb20ebdb5fc9fc81983dbe30ffb9f3`, containing the 1800-second timeout and Queue-to-Pipe execution fix.

## d840a5a versus 9fd8b09 code check

For the pre-existing core detector/RCA implementation:
- `src/sentinelops/anomaly/detectors.py`
- `src/sentinelops/rca/engine.py`
- `src/sentinelops/rca/causal.py`
- `src/sentinelops/rca/challenger.py`
- `src/sentinelops/rca/validation.py`

the diff `d840a5a..9fd8b09` is **empty**.

However, the broader Phase A evaluation detector/ranking layer is **not empty** between those commits: the `src/sentinelops/evaluation/rcaeval_*.py` modules and Phase A evaluation scripts exist at `d840a5a` but not at the older `9fd8b09`. Therefore an unqualified statement that the entire detector/ranking diff is empty would be false.

## Evidence completeness confirmation

Both committed held-out result files contain:
- six per-fault tables (`per_fault`);
- valid-ranking-only secondary results for all seven runnable methods (`valid_rankings_only_secondary`);
- V2a strength distributions for all E3 service strengths and per-case maxima (`v2a_strength_distribution`).

Files:
- `docs/evidence/phase_a/re2ss/step26_results.json`
- `docs/evidence/phase_a/re2tt/step27_results.json`

## OB topology sensitivity disclosure

The RE2-OB headline result uses the original trace-derived primary topology; the later A4 static topology is explicitly a post-hoc sensitivity analysis and never replaces the primary score. Its purpose is to test how topology choice affects conclusions while preserving the original result and labeling the alternative topology as secondary evidence.

## Held-out burn state

Explicit burn entries are maintained in `docs/evidence/phase_a/BURN_LOG.md` for RE2-SS and RE2-TT.

## Claim-interval interpretation

RE2-SS V2a minus threshold Avg@5 is +0.002222 with 95% CI [-0.008889, 0.015556]; this supports a **comparable / no clear difference** description, not superiority.

RE2-TT V2a minus threshold Avg@5 is -0.037778 with 95% CI approximately [-0.080000, 0.000000]; V2a has a lower point estimate and the interval reaches approximately zero. RE2-TT V2a minus BARO Avg@5 is -0.064444 with 95% CI [-0.122222, -0.006667], supporting the narrower statement that V2a is below BARO on this registered Avg@5 comparison.

## Additional provenance caveats

- Run-summary JSON files do not embed runner SHA-256 values; runner provenance is established by the freeze and integrity records.
- BARO and CIRCA ran through `scripts/phase_a_step27_rcaeval_run.py`; v1, V2a, threshold, random, and PageRank ran through `scripts/phase_a_step27_run.py`.

## Cross-suite comparability correction

Raw top-k accuracy is lower on RE2-TT, but RE2-TT has a much larger effective candidate set than RE2-SS (39 versus 8; Chance@5 0.128205 versus 0.625000), so the suites are not directly comparable. For V2a, SS AC@5/Lift@5 is 0.977778/1.564444 while TT AC@5/Lift@5 is 0.877778/6.846667; raw accuracy and chance-normalized lift therefore tell different parts of the story.
