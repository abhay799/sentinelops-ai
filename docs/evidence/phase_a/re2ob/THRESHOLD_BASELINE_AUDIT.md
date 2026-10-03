# Static-Threshold Baseline Audit

Date: 2026-10-03
Scope: RE2-OB diagnostics only; no fixes or reruns.

The static-threshold baseline calls `prepare_metrics`, fits each metric's z-score
statistics on the frozen first-half pre-injection calibration slice, then ranks
each service by its maximum z-score over rows after calibration. Threshold is
fixed at 2.5. The ranking function receives metrics plus injection time only; it
does not receive root-cause service, fault label, or a parsed service from the
case path. `case_id` is used by the runner to locate the case files and save
output, not as a ranking feature.

Across all 90 saved cases:
- `ground_truth_used_for_ranking=false`: 90/90.
- raw duplicate-service rankings: 0.
- E3 duplicate-service rankings: 0.
- true service missing after E3 filtering: 0.
- raw top-score ties: 0.
- native candidate counts: 11 in 2 cases, 12 in 85, 13 in 2, 14 in 1.
- true-service E3 rank distribution: rank 1 = 78, rank 2 = 7, rank 3 = 2,
  rank 4 = 3; no true service ranks below 4.

This yields AC@1 = 78/90 = 0.8667 and AC@5 = 90/90 = 1.0000. The
perfect AC@5 is therefore a genuine saved benchmark result under the frozen
baseline, not a duplicate, fallback, E3, or denominator artifact.

The baseline does use post-calibration observations, including the injected
fault period, to rank root causes; that is its intended post-event RCA design,
not calibration leakage. The unusually strong result should nevertheless be
reported as RE2-OB development-suite performance only and not as evidence of
held-out generalization.

Machine-readable evidence: `threshold_baseline_audit.json`.
No thresholds, rankings, candidate sets, or scores changed. Never push.
