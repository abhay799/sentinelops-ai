# Erratum E8 - Post-scoring diagnostic provenance and freeze

Date: 2026-10-03

**Status: POST-SCORING DIAGNOSTIC ERRATUM.**

E8 records provenance for diagnostics performed after the frozen RE2-OB Step 21-24
results already existed. It does not amend the benchmark scoring protocol and
cannot be used to retune or replace any reported RE2-OB result.

The post-scoring diagnostics currently covered are:
- Amendment A5 / `STEP13_RESOLUTION.md`: explains detector-v1's always-alert-like
  window behavior and retains v1 unchanged as a negative baseline.
- `SENTINELOPS_TIE_DIAGNOSTIC.md` and `sentinelops_tie_diagnostic.json`: quantify
  saturation/ties in saved SentinelOps RCA strengths and their descriptive
  association with AC@1.

These diagnostics may explain limitations, disclose provenance, and identify
future model-design work. They may not alter saved rankings, AC@k values,
weights, thresholds, tie-breaking, candidate sets, detector settings, seeds,
bootstrap draws, fallback handling, or primary/secondary denominators.

No significance claim is created by these diagnostics. The tie-group AC@1 split
is descriptive and was not pre-registered as a hypothesis test. Detector-v1's
negative result remains a limitation rather than a basis for post-hoc tuning.

RE2-SS and RE2-TT remain held out. No raw held-out case content may be opened,
downloaded, scored, or used to choose changes under E8. Catalog-level metadata
handling is documented separately. Never push.
