# Step 26 dcb02f8 implementation provenance

Date: 2026-10-03
Status: retrospective disclosure committed before RE2-SS aggregate scoring.

Commit `dcb02f8fc26880a52ec52ea77f4bbe93fc558e57`, originally titled
`fix:`, was committed at 2026-10-03T12:15:36Z
(17:45:36 Asia/Calcutta), after RE2-SS raw-data access and smoke validation.
Its parent is `1b058a362d62faeccb58a0e9e5eb7146f73e2284`.

It changed only `scripts/phase_a_step26_run.py` and
`scripts/phase_a_step26_score.py`:
- remove mmBARO/mmCIRCA from the numerical runnable-method set and paired
  comparison matrix, implementing the previously committed pre-scoring
  input-contract exclusion;
- retain all V2a unclipped service strengths and enforce finiteness;
- require cached successful V2a records to contain those strengths, so a cache
  without them is incomplete and may be recomputed by the existing runner;
- report finite V2a strength distributions and per-case maxima;
- represent mm methods as n/a, excluded from numerical comparisons, rather
  than scoring their unavailable inputs as 90 misses.

This is an execution/evidence-completeness change after held-out access, not a
preregistration before SS access. The cache requirement can cause repeated
computation of a V2a case with the same frozen algorithm; it does not select or
change its ranking rule. Numeric method settings, topology, E3 allowlist, E4
fallback policy, seed 42, 10,000 resamples, and the metric definitions are
unchanged. The mm decision was documented before SS accuracy scoring and was
based on the pinned input contract, not method performance.

At this documentation checkpoint CIRCA and V2a are still running, the aggregate
`step26_results.json` and `STEP26_RESULTS.md` do not exist, and the frozen
scorer has not been executed by this cleanup. This records the available
repository/file evidence; it does not claim an exhaustive history of shell
commands. No SS ranking or accuracy output was used to choose a parameter,
variant, topology, filter, or scoring rule in this documentation cleanup.

No code is changed by this note. No job is started or killed. RE2-TT is not
accessed. Never push.
