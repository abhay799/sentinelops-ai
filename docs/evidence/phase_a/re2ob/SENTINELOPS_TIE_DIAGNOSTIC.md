# SentinelOps RCA Strength-Tie Diagnostic

Date: 2026-10-03
Scope: RE2-OB only; diagnostics only; no ranking or scoring changes.

Top tie is defined as more than one E3-eligible service sharing the maximum saved
`anomaly_strength` in a case. The diagnostic reads the full saved Step 16 RCA
evidence for strengths and the E3-filtered SentinelOps ranking actually scored
in Step 21. Ground truth is used only after ranking for diagnostic accuracy.

## Frozen tie-breaking behavior

- `primary_service = max(sorted(service_strengths), key=(strength, service))`.
- Therefore equal maximum strengths select the lexicographically largest service
  for the frozen primary-service bonus.
- Final rows are ordered by descending rounded `rca_score`; exact score ties are
  broken by service name ascending.
- No weights, rounding, bonus, graph impact, filtering, or tie-breaking changed.

## Findings

- 78/90 cases have a top-strength tie; 12/90 do not.
- AC@1 on no-top-tie cases: 7/12 = 58.33%.
- AC@1 on top-tie cases: 12/78 = 15.38%.
- Exact strength 1.0 occurs in 0 to 10 eligible services depending on case.
- The full per-case JSON records the exact count, tied services in final-ranking
  order, true-service final rank, and true-service position within the top tie.
- The true service belongs to the maximum-strength group in 73/90 cases.
- Among those 73, its position within that group in final-ranking order is:
  position 1: 18; 2: 29; 3: 15; 4: 9; 5: 1; 6: 1.

The diagnostic supports the interpretation that score saturation/ties materially
reduce top-1 discrimination under the frozen RCA design. It is descriptive only:
no causal or significance claim is made, and no post-hoc tie fix is introduced.

Machine-readable evidence: `sentinelops_tie_diagnostic.json`.
