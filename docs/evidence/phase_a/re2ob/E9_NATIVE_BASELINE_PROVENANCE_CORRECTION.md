# Erratum E9 - Native baseline provenance correction

Date: 2026-10-03

**Status: POST-HOC PROVENANCE CORRECTION.**

E5/E6/E7 contain wording that can be read as saying the only accuracy/scoring
results observed before E5 were random-baseline results. That wording is too
broad. Two native RCAEval aggregate scoring logs existed before the E5 commit:

- `logs/step20_native_baro.log` — mtime `2026-10-02T18:41:30.282246038Z`
- `logs/step20_native_mmbaro.log` — mtime `2026-10-02T18:43:50.814244744Z`

E5 commit `fdd5d74` was created at `2026-10-02T18:46:14Z`.
Therefore native BARO and native mmBARO aggregate scoring had been observed
before E5 was committed.

The narrower historical statement remains supported: before E5, no committed
Phase A Step 21-24 AC@k result artifact for SentinelOps or the non-random
baselines was found in the repository checkout, while random seed-42 AC@k and
the random multi-seed diagnostic had been observed. E9 corrects only the
broader provenance wording; it does not alter any ranking, score, metric,
filter, threshold, weight, tie-break, seed, bootstrap result, or denominator.
