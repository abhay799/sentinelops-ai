# Phase C — C2/C3 Implementation Report

**Scope:** C2 schema/ground-truth isolation and C3 harness implementation/dry runs only.

**Explicitly not done:** no registered run, no run registry/schedule, no registered detector fit, and no registered result scoring.

## C2 — per-run schema

Implemented in `src/sentinelops/chaos/schema.py`.

Required fields:

- `run_id`
- `seed`
- `scenario`
- `injection_start`
- `injection_end`
- `recovery_time`
- `detection_time`
- `rca_output_time`
- `guard_decision_time`
- `remediation_time`
- `verification_time`

Every timestamp field must be present in the record. Stage timestamps may be explicitly `null` when a stage did not occur, but omitted fields are rejected. Non-null timestamps must be timezone-aware UTC. Ordering is validated across the observed chain.

All chaos timestamps use the single `utc_now()` implementation in `src/sentinelops/chaos/stage_events.py`, backed by the host UTC clock (`datetime.now(timezone.utc)`). The harness imports this same clock function rather than maintaining a second clock implementation.

Unit coverage validates valid ordered UTC records, non-UTC rejection, naive timestamp rejection, out-of-order rejection, missing required timestamp rejection, and missing nullable-stage field rejection.

## Ground-truth isolation

Injection ground truth is written only by `src/sentinelops/chaos/ground_truth.py` under:

`evidence/C/C03_dry_runs/_ground_truth_injection_only/`

The pipeline isolation test scans:

- `src/sentinelops/anomaly/detectors.py`
- `src/sentinelops/incidents/correlator.py`
- `src/sentinelops/rca/engine.py`
- `src/sentinelops/rca/challenger.py`
- `src/sentinelops/remediation/sentinelguard.py`

It fails if any imports `sentinelops.chaos.ground_truth`, references `_ground_truth_injection_only`, or imports `write_injection_record`.

Stage timestamps are written by stage adapters in `src/sentinelops/chaos/dry_run_stages.py`. The harness receives the timestamps returned by detection, RCA, guard, remediation, and verification stages; it does not fabricate those stage timestamps after the fact.

## Detector fit/score split

Added explicit baseline-fit/freeze support:

- `src/sentinelops/anomaly/frozen_detector.py`
- `scripts/phase5_frozen_detector.py`

Supported modes:

- `fit-baseline-freeze`: fits Isolation Forest only to the supplied baseline matrix, saves a joblib artifact, computes its SHA-256, and saves a sidecar manifest containing the hash, row/column counts, and frozen detector parameters.
- `score-frozen`: loads the saved artifact and scores a separate supplied matrix without refitting.

A synthetic unit test verifies deterministic load/score behavior and that the saved manifest contains a SHA-256. This is development-only test evidence, not the registered detector fit.

### Existing-mode byte regression — BLOCKED BY MISSING SAVED INPUT

The requested byte-identical before/after regression on the **saved Phase 5 input** could not be run because `data/processed/features/temporal_features_v1.parquet` is not present in this workspace, is not present elsewhere under `/home/dell/work`, was not found under the searched Windows user tree, and has no Git history in this repository. The corresponding saved Phase 5 output/model are also absent.

The existing script `scripts/train_phase5_anomaly.py` was not modified. Its working-tree Git blob and `HEAD` blob are identical:

`9782a8d8fba0c4cfd8de19be1450bd271c0752da`

This proves the legacy implementation itself was untouched, but it is **not** a substitute for the requested empirical byte-identical output regression. That regression remains unresolved until the saved Phase 5 input is restored.

No registered detector fit was run.

## C3 — harness implementation

Implemented under `src/sentinelops/chaos/` plus `scripts/phase_c03_dry_run.py`.

Frozen protocol values represented by the implementation:

- seeded run identity
- baseline: 120 s
- latency injection: 120 s, 300 ms latency, error rate 0
- errors injection: 120 s, error rate 1.0
- bad-deployment rollback duration read from `configs/chaos_bad_deployment_v1.yaml`
- bad-deployment config SHA-256 remains `62e22a74c6714b505e4c8f91e707ba0b94fada5559b253ac3a62d2a01d291c2e`
- cool-down: 120 s
- guard remains in the control path
- explicit human authorization remains in the control path
- rollback uses existing `execute_local_sandbox()` with the existing `/failure-mode/reset` adapter
- emergency cleanup is represented separately and is always marked `counted_as_remediation: false`
- per-run resource evidence records wall-clock, user CPU, system CPU, `/proc/meminfo` total/available memory, and whether a service was killed

The development dry-run mode intentionally does not sleep the 120/180/120 configured periods and does not hit a real service. It validates orchestration/evidence plumbing with the existing guard and execution adapter using `httpx.MockTransport`. Therefore dry-run wall-clock values are not chaos-performance measurements and may not be used as registered results.

The host reports `MemTotal: 3,887,732 KiB` (about 3.7 GiB) in the saved dry-run resource evidence. No dry run killed a service.

## C3 dry runs

All committed dry-run artifacts are marked:

- `classification: non_registry`
- `dry_run: true`
- `registered_result_eligible: false`

Final stored artifacts:

| Scenario | Run ID | Schema | UTC/order | Full chain recorded | Rollback/verify | Service killed |
|---|---|---|---|---|---|---|
| latency | `C03-DRY-latency-1001` | PASS | PASS | PASS | `executed_verified` | false |
| errors | `C03-DRY-errors-1002` | PASS | PASS | PASS | `executed_verified` | false |
| bad deployment -> rollback | `C03-DRY-bad_deployment_rollback-1003` | PASS | PASS | PASS | `executed_verified` | false |

For each run, the recorded chain is:

`inject -> detect -> correlate -> RCA -> challenge -> plan -> guard -> human authorization -> rollback -> verify`

Injection evidence is isolated in the ground-truth-only directory; all remaining stage evidence is stored inside the per-run directory.

Dry-run invocation count stayed within the requested maximum. Latency and errors were invoked once each. Bad-deployment was invoked twice under the same non-registry run ID while verifying that duration is read from the frozen YAML; the final stored artifact is from the second invocation.

## Tests

Final C2/C3 test run:

`8 passed in 1.82s`

An earlier pre-final invocation had `7 passed in 3.53s`; after that, the schema was tightened so nullable stage fields must still be present as keys, and the final 8-test run was executed. This means the new-test suite was invoked twice, not once; the second invocation is the final code state.

Existing Guard / Phase 13 / Phase 14 selection was run once:

`21 passed in 1.03s`

No Phase C registered execution was started by these tests.

## Known unresolved item

The only requested item not completed is the empirical byte-identical regression of the legacy Phase 5 output on its saved Phase 5 input, because that input is unavailable in the accessible workspace/history. The legacy script itself is byte-identical to `HEAD`, and no registered fit was substituted for the missing regression.
