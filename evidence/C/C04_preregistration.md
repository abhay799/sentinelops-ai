# Phase C C4/C5 — Prerun Registration

**Status:** frozen before any registered Phase C run.

## Master seed and schedule

Master seed: `42`.

The registry contains exactly 60 registered runs:

- TRAIN: 36 total = 12 per scenario
- VALIDATION: 12 total = 4 per scenario
- TEST: 12 total = 4 per scenario

Scenarios:

- latency
- errors
- bad_deployment_rollback

Execution is partition-constrained:

1. all TRAIN registered runs;
2. fit and freeze the registered detector from TRAIN baseline only;
3. all VALIDATION registered runs;
4. all TEST registered runs.

Within each partition, order is randomized deterministically from the frozen master seed using the hash-based order rule embedded in the registry.

The seed derivation rule and exact per-run seeds are committed in:

`evidence/C/C04_run_registry.json`

## Reserved spares

Exactly two spare seeds are reserved for each scenario/partition cell, for 18 reserved spares total.

They may replace only infrastructure-invalid runs under:

`evidence/C/C04_invalid_run_policy.md`

Algorithmic outcomes are never replaced.

## Analysis freeze

Registered analysis is implemented in:

- `src/sentinelops/chaos/analysis.py`
- `scripts/phase_c_registered_analysis.py`

It reports:

- detection delay;
- detection rate;
- correlation correctness;
- RCA Hit@1/Hit@3/Hit@5 against the injected service;
- SentinelGuard decision counts and proportions;
- remediation success;
- recovery time;
- run-level bootstrap 95% confidence intervals with seed 42 and 10,000 resamples.

Before any registered run, the analysis was exercised only on synthetic fixtures and the non-registry C03 dry-run artifacts.

## Ground-truth persistence rule

Injection ground truth is constructed in memory at injection time but is not persisted until after the verification stage returns.

Detection, correlation, RCA, challenger, and SentinelGuard modules are prohibited by test from importing or reading the injection-ground-truth source.

Registered run records must use:

`approver: scripted_approver_v1`

## Windows-side Phase 5 / Phase 10 data check

Read-only inspection found:

- `C:\Users\DELL\sentinelops-ai\data`: does not exist.
- `C:\Users\DELL\Projects\sentinelops-ai\data`: exists.
- its `data\processed` tree contains only `.gitkeep`;
- no `temporal_features_v1.parquet`;
- no `anomaly_scores_v1.parquet`;
- no `early_warning_v1.parquet`;
- no matching Isolation Forest model under the checked Windows-side project models tree.

Therefore the legacy Phase 5 saved-input byte regression remains unavailable and is recorded as code-identity-only evidence in `evidence/C/DEVIATION_LOG.md`.

## Estimated sequential wall-clock by partition

The estimate combines the fixed protocol sleep durations with the observed C03 dry-run control-path overhead. It excludes detector-fit time, service startup/restart delays, invalid-run replacements, and operator pauses.

Observed dry-run control overhead:

- latency: 0.009211505 s
- errors: 0.012962106 s
- bad-deployment rollback: 0.014557697 s

Estimated per-run sequential wall-clock:

- latency: 360.009 s = 120 s baseline + 120 s injection + 120 s cool-down + dry-run control overhead;
- errors: 360.013 s = 120 + 120 + 120 + overhead;
- bad-deployment rollback: 420.015 s = 120 s baseline + 180 s injection + 120 s cool-down + overhead.

Estimated partition totals:

- TRAIN: 13,680.441 s ≈ **3 h 48 m 00.4 s**
- VALIDATION: 4,560.147 s ≈ **1 h 16 m 00.1 s**
- TEST: 4,560.147 s ≈ **1 h 16 m 00.1 s**
- registered run execution total: 22,800.735 s ≈ **6 h 20 m 00.7 s**, plus detector fit and operational overhead.

No registered run has been started.
