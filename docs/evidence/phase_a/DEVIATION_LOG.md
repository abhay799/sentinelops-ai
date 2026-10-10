# Phase A Deviation Log

## D1 — CIRCA RE2-TT per-case runtime ceiling

- **Date set:** 2026-10-05
- **Scope:** RE2-TT CIRCA execution only
- **Deviation:** add a fixed 1800-second (30-minute) per-case runtime ceiling and explicit `timeout_unranked` outcome.
- **Timing:** the policy was set after the CIRCA run had already started, but before any CIRCA ranking result was inspected or used for tuning.
- **Circumstances:** CIRCA case 2 was observed running for more than two hours. That was a runtime observation only; no ranking result from the case had been inspected. The run was interrupted before the previously stated three-hour stuck rule was reached or verified, so this log explicitly does not claim that the three-hour condition was satisfied. A uniform 30-minute ceiling was then adopted as a compute-budget methodology rule for subsequent/restarted CIRCA cases.
- **Application:** the same ceiling applied uniformly to every case executed under the amended runner; cached terminal case files were skipped on resume.
- **Scoring:** `timeout_unranked` is a non-`ok` status and therefore receives an all-zero hit vector under the existing all-case scoring rule.
- **What did not change:** CIRCA ranking parameters, topology, SLI, candidate filter, dataset revision, ground-truth handling, metric definitions, bootstrap settings, and SentinelOps ranking logic.
- **Interpretation:** the resulting RE2-TT CIRCA coverage is a compute-budget/runtime result and must not be interpreted as a general statement about CIRCA algorithmic quality.
