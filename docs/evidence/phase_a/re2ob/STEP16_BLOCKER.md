# Phase A Step 16 — RCA topology blocker

**Date:** 2026-10-02  
**Dataset:** RE2-OB only  
**Status:** STOPPED before RCA ranking

The frozen suite-graph build processed all 90 RE2-OB trace files. Eighty-eight
cases passed the existing trace-key validation. Two cases failed because the
same `(traceID, spanID)` key occurs more than once:

- `re2ob_recommendationservice_loss_1`: 299,508 trace rows; 96 rows belong
  to 48 duplicated keys; all 96 duplicate rows are exact full-row duplicates;
  maximum multiplicity is 2.
- `re2ob_recommendationservice_loss_2`: 370,911 trace rows; 198 rows belong
  to 99 duplicated keys; all 198 duplicate rows are exact full-row duplicates;
  maximum multiplicity is 2.

The committed adapter-validation policy states that duplicate
`(traceID, spanID)` identifiers are a hard failure. Therefore the evaluator
did not silently deduplicate these trace rows, did not construct a partial
suite graph, and did not produce SentinelOps RCA rankings.

Allowing exact trace-row deduplication would require an explicit policy/spec
amendment before rerunning Step 16. No such amendment was made in this run.

Phase A Step 15 completed successfully on all 90 RE2-OB cases. Steps 17–25 were
not run after this blocker. RE2-SS and RE2-TT remain untouched.
