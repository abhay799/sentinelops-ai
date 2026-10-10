# SentinelOps AI Chaos Harness v1 — Design Specification

**Status:** DESIGN ONLY — not implemented  
**Scope:** LOCAL / SYNTHETIC / NOT CONNECTED TO PRODUCTION  
**Version:** v1

## 1. Purpose

This document defines the first reproducible chaos/fault-injection harness for SentinelOps AI.

The harness is intended to create repeatable local runs that exercise the lifecycle:

```text
baseline
-> inject fault
-> detect
-> correlate
-> RCA
-> SentinelGuard
-> remediation
-> verify recovery
```

The harness must produce timestamped ground-truth records and evidence artifacts so later prediction, RCA, remediation, and recovery evaluation can be performed without inferring fault timing from detector output.

The harness is limited to the current local synthetic service environment. It does not represent production chaos engineering.

---

## 2. Scenarios

v1 contains exactly three preregistered scenarios:

1. latency
2. errors
3. bad-deployment -> rollback

No additional scenario may be added to v1 results after evaluation has begun without a versioned protocol change.

### 2.1 Latency

**Target service:** `payment-service`

**Injection mechanism**

Use the existing local service failure-control surface:

```text
POST /failure-mode
```

with failure mode `latency`.

**Parameters**

- `mode: latency`
- `latency_ms: 300`
- `error_rate: 0.0`
- target: `payment-service`
- harness seed recorded for the run

The first v1 design fixes the latency magnitude at 300 ms to match the existing Phase 4 synthetic failure exercise.

**Injection duration**

- 120 seconds

The harness records the actual UTC start and end timestamps, rather than assuming the configured duration was achieved exactly.

**Expected detection signal**

Expected observable effects include:

- elevated request latency
- increased rolling latency features
- anomaly score increase
- anomaly/detection event for `payment-service`
- possible correlated downstream/upstream incident evidence depending on observed telemetry

The expected signal is a preregistered expectation, not a guarantee that the detector must fire.

**Correct remediation**

```text
POST /failure-mode/reset
```

The expected outcome is removal of the injected latency mode and successful post-action `/live` and `/ready` verification.

---

### 2.2 Errors

**Target service:** `payment-service`

**Injection mechanism**

Use the existing local service failure-control surface:

```text
POST /failure-mode
```

with failure mode `errors`.

**Parameters**

- `mode: errors`
- `latency_ms: 0`
- `error_rate: 1.0`
- target: `payment-service`
- harness seed recorded for the run

The error rate is fixed at 1.0 in v1 to match the existing Phase 4 synthetic error scenario.

**Injection duration**

- 120 seconds

The actual injection start and end UTC timestamps must be recorded.

**Expected detection signal**

Expected observable effects include:

- HTTP 503 responses
- elevated rolling error-rate features
- anomaly score increase
- anomaly/detection event for `payment-service`
- possible correlated incident evidence

A missing detector response remains a valid experimental outcome and must not be rewritten as a successful detection.

**Correct remediation**

```text
POST /failure-mode/reset
```

The expected outcome is restoration to normal service behavior followed by `/live` and `/ready` verification.

---

### 2.3 Bad deployment -> rollback

**Target service:** `payment-service`

**Injection mechanism**

v1 models a bad deployment using the existing synthetic local controls rather than a real deployment platform.

The run records a deployment change event and applies a synthetic degraded state to `payment-service`.

The design sequence is:

1. emit a deployment change event identifying `version_before: 2.7` and `version_after: 2.8`
2. activate a synthetic failure mode representing the degraded release
3. maintain that degraded state for the configured injection duration
4. evaluate detection, RCA, SentinelGuard, and remediation
5. perform the configured local rollback adapter

For v1, the degraded release is represented by the same local failure-control API already supported by the service runtime. This is a synthetic deployment-failure model, not a real application deployment.

**Parameters**

The bad-deployment profile is frozen in:

`configs/chaos_bad_deployment_v1.yaml`

SHA-256:

`62e22a74c6714b505e4c8f91e707ba0b94fada5559b253ac3a62d2a01d291c2e`

The frozen profile is:

- at `injection_start`, emit a deployment change event for `payment-service`
- `version_before: "2.7"`
- `version_after: "2.8"`
- first degradation stage: 90 seconds of `mode: latency`, `latency_ms: 300`, `error_rate: 0.0`
- second degradation stage: 90 seconds of `mode: errors`, `latency_ms: 0`, `error_rate: 1.0`
- rollback action: `POST /failure-mode/reset`
- rollback semantics: restore the prior normal failure mode
- harness seed recorded for the run

This two-stage profile is fully expressible with the current `/failure-mode` mechanism.

The current mechanism cannot inject latency and errors simultaneously because the service runtime has one active `failure_state.mode` at a time: `normal`, `latency`, or `errors`. Supporting a simultaneous latency-and-error profile would require a runtime change that permits both effects to be active in one failure state. v1 therefore freezes a deterministic sequential latency-then-error shift instead.

The profile file and its hash are part of the preregistered protocol and must not be changed after the first scored run begins.

**Injection duration**

- 180 seconds total: 90 seconds latency shift followed by 90 seconds error shift

The actual injection start and end UTC timestamps must be recorded.

**Expected detection signal**

Expected evidence includes:

- deployment/change telemetry
- elevated failure signal from the synthetic degraded release
- anomaly detection
- incident correlation
- RCA candidate involving `payment-service`
- challenger/counterfactual evidence where available
- remediation proposal for rollback

The RCA result is evaluated as a hypothesis/ranking result and is not treated as confirmed root cause merely because the scenario ground truth is known to the harness.

**Correct remediation**

`rollback`, using the currently configured local sandbox adapter:

```text
POST /failure-mode/reset
```

Recovery must be checked independently after the action.

---

## 3. Ground-truth record schema

Every harness run must create one immutable ground-truth record.

All timestamps are UTC and serialized as ISO 8601 with timezone information.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `run_id` | string | Unique immutable run identifier |
| `seed` | integer | Run seed used for randomized ordering and any seeded harness choices |
| `scenario` | enum | `latency`, `errors`, or `bad_deployment_rollback` |
| `injection_start` | UTC timestamp | Time the fault/degraded state was successfully activated |
| `injection_end` | UTC timestamp | Time the planned injection period ended or remediation began |
| `recovery_time` | UTC timestamp or null | First time recovery criteria are satisfied after remediation |
| `detection_time` | UTC timestamp or null | First qualifying SentinelOps detection attributable to the run |
| `rca_output_time` | UTC timestamp or null | Time the RCA output for the run is produced |
| `guard_decision_time` | UTC timestamp or null | Time SentinelGuard records its technical decision |
| `remediation_time` | UTC timestamp or null | Time the remediation action is actually attempted |
| `verification_time` | UTC timestamp or null | Time post-remediation verification completes |

Null is a valid value when a stage does not occur.

The harness must not fabricate timestamps for missed stages.

### 3.1 Derived timing metrics

Derived metrics may be computed later from the immutable timestamps, including:

- prediction/detection lead time relative to `injection_start`
- detection latency
- RCA latency
- Guard decision latency
- time to remediation
- time to verified recovery

Derived values are not stored as replacements for the source timestamps.

---

## 4. Run protocol

### 4.1 Repetitions

v1 uses:

- 20 repetitions per scenario
- 3 scenarios
- 60 registered runs total

This registered count is fixed before evaluating aggregate results.

Any runs beyond these 60 are optional exploratory runs. They must be labeled `post_registered_optional`, stored separately from the registered result set, and must not be included in the preregistered aggregate result.

A run that fails operationally remains part of the run ledger and is assigned an explicit status rather than silently repeated until successful.

If a replacement run is required because the harness itself failed before fault injection began, the original run record remains preserved and the replacement receives a new `run_id`.

### 4.2 Baseline period

Before each injection:

- 120 seconds of baseline operation
- service `/live` and `/ready` must pass before injection
- failure mode must be reset to normal
- baseline telemetry must be captured

If baseline health is not established, the run is marked invalid-before-injection and no fault is injected.

### 4.3 Injection period

The scenario-specific configured duration is:

- latency: 120 seconds
- errors: 120 seconds
- bad-deployment -> rollback: 180 seconds

The harness records actual timestamps for all transitions.

### 4.4 Cool-down

After recovery verification:

- minimum 120-second cool-down
- failure mode must be normal
- `/live` and `/ready` must pass
- no previous-run remediation state may remain active

The next run must not begin until cool-down criteria are satisfied.

### 4.5 Randomization and execution order

The 60 registered run identities and their train/validation/test assignments are generated from a preregistered master seed before the first run.

Execution is partition-constrained because the anomaly detector must be fitted and frozen before any validation or test run starts:

1. execute all 36 TRAIN runs first, randomized within the TRAIN partition
2. fit and freeze the anomaly detector from TRAIN-run baseline periods only
3. record the frozen detector artifact SHA-256
4. execute the 12 VALIDATION runs, randomized within the VALIDATION partition
5. execute the 12 TEST runs, randomized within the TEST partition

The master seed is stored in the harness manifest.

Each run also receives its own deterministic run seed derived from the master schedule.

Randomization affects run ordering within each partition only in v1. Scenario parameters remain fixed.

The complete partition-constrained 60-run execution schedule must be generated before the first registered run and stored unchanged.

### 4.6 Storage layout

Proposed evidence layout:

```text
docs/evidence/chaos/v1/
  manifest.json
  run_schedule.json
  runs/
    <run_id>/
      ground_truth.json
      injection.json
      detection.json
      incident.json
      rca.json
      guard.json
      remediation.json
      verification.json
      telemetry_manifest.json
      run_summary.json
```

Large raw telemetry may remain under the existing ignored local data directories, but each run evidence directory must include a manifest identifying the telemetry source, time range, and integrity hash where practical.

The run ledger must preserve failed, blocked, missed-detection, and incomplete outcomes.

No run may be deleted merely because the result is unfavorable.

---

## 5. Split-by-run rule for later prediction evaluation

Prediction evaluation must split by `run_id`, never by individual telemetry row.

All rows/events/windows originating from the same chaos run must remain in exactly one partition.

Required rule:

```text
train runs ∩ validation runs = empty
train runs ∩ test runs = empty
validation runs ∩ test runs = empty
```

No temporal windows, labels, feature rows, or post-injection observations from one run may be distributed across multiple partitions.

### 5.1 Proposed v1 partitioning

With 60 registered runs:

- 36 train runs
- 12 validation runs
- 12 test runs

The split is stratified by scenario.

Per scenario:

- 12 train
- 4 validation
- 4 test

The assignment is created from the preregistered master seed before model training.

The test-run identities remain frozen for final evaluation.

With 12 held-out test runs, the result supports only an existence/consistency claim under this local synthetic protocol, reported with bootstrap intervals; it does not support a general performance claim.

### 5.2 Temporal leakage rule

Within each run, a feature at time `t` may use only information available at or before `t`.

Ground-truth fields such as `injection_start`, future anomaly status, recovery outcome, and future timestamps may be used by the evaluator but may not enter predictor features.

### 5.3 Frozen anomaly-detector fit rule

The anomaly detector used for registered evaluation must be fit using **baseline periods from TRAIN runs only**.

Before any validation or test run starts:

1. complete the registered TRAIN runs
2. collect the registered baseline periods from TRAIN runs only
3. fit the anomaly detector only on those TRAIN-run baseline observations
4. freeze the resulting detector artifact
5. record the detector artifact SHA-256 in the evidence manifest
6. record the exact detector-fit procedure, source run IDs, feature schema, configuration, and software revision

No validation or test run may start until the frozen detector artifact and its hash have been recorded.

After any validation or test result becomes visible, the detector must not be refit, recalibrated, or otherwise changed for the registered v1 result.

Validation/test telemetry, injected periods, recovery periods, and their labels may not be used to fit the frozen detector.

Any later detector refit belongs to a new versioned evaluation and cannot replace the registered v1 result.

---

## 6. Preregistered exit criteria

The v1 harness is considered **execution-complete** only when the following evidence exists.

### 6.1 Run-count criteria

Required registered runs:

- latency: 20
- errors: 20
- bad-deployment -> rollback: 20
- total registered: 60

Any additional runs are optional exploratory runs and are not part of the preregistered v1 result.

Every scheduled run must have a run ledger entry.

The harness report must disclose separately:

- completed runs
- invalid-before-injection runs
- injection failures
- missed detections
- missing RCA outputs
- Guard blocks
- remediation not attempted
- remediation failures
- verification failures
- successfully verified recoveries

There is no requirement that every run succeed.

### 6.2 Required global evidence artifacts

The final v1 evidence package must contain:

- protocol/design document
- frozen scenario configuration
- master seed
- randomized run schedule
- run manifest
- one ground-truth record per scheduled run
- per-run evidence manifests
- aggregate status-count table
- timing table derived from recorded UTC timestamps
- detection outcome table
- RCA outcome table
- SentinelGuard decision table
- remediation/verification outcome table
- explicit list of excluded/invalid runs and reasons
- hashes or equivalent integrity references for frozen protocol and run schedule

### 6.3 Required per-run evidence

For every run that reaches injection:

- injection activation evidence
- `injection_start`
- `injection_end`
- telemetry time range or telemetry manifest
- detection result, including explicit missed-detection outcome
- RCA result or explicit missing-RCA outcome
- SentinelGuard decision or explicit missing decision
- remediation record or explicit not-attempted reason
- verification result
- recovery timestamp when recovery is verified

### 6.4 Exit statement

Completing the evidence package means:

> SentinelOps Chaos Harness v1 executed the preregistered local synthetic protocol and preserved the resulting evidence.

It does not mean that SentinelOps is production-ready.

---

## 7. Claims the harness will NOT make

Chaos Harness v1 must not claim any of the following:

- production chaos engineering
- production fault tolerance
- production incident detection performance
- production failure-prediction performance
- production RCA accuracy
- production remediation safety
- production rollback reliability
- production SLO compliance
- production authorization integration
- real customer traffic
- real production service dependencies
- real deployment-platform rollback
- Kubernetes, cloud, database, Kafka, or network fault coverage unless such mechanisms are separately implemented and versioned later
- autonomous production remediation
- that a known synthetic ground truth proves the RCA engine independently discovered a confirmed cause

All v1 runs use synthetic/local services and controlled fault mechanisms.

---

## 8. SentinelGuard participation in each run

SentinelGuard remains a separate decision stage and must not be bypassed by the harness.

The run sequence is:

1. fault injected
2. SentinelOps detection/correlation runs
3. RCA candidate is produced
4. challenger/counterfactual stages run where available
5. remediation planner proposes an action
6. SentinelGuard evaluates the proposal
7. Guard decision and timestamp are recorded
8. explicit human-authorization policy is applied
9. final execution gate evaluates the request
10. only then may the configured local sandbox remediation adapter run
11. recovery verification follows

The harness itself must not directly call the remediation endpoint as the scored remediation path before Guard/final-gate evaluation.

Emergency harness cleanup after an operationally failed run is allowed only as test-fixture cleanup. Such cleanup must be recorded separately and must not be counted as SentinelOps remediation success.

### 8.1 SentinelGuard evidence captured per run

Capture:

- recommended action
- candidate service
- RCA disposition
- causal score
- priority score
- projected failure risk
- recommended net benefit
- rollback availability
- traceable-evidence status
- individual Guard checks
- failed checks
- Guard technical approval
- Guard decision
- human approval state
- execution allowed state
- Guard decision UTC timestamp

---

## 9. SentinelGuard configuration consolidation proposal

The repository currently has overlapping SentinelGuard policy in:

- `configs/sentinelguard.yaml`
- `configs/remediation.yaml`

The runtime Phase 13 Guard implementation currently consumes the `sentinelguard` section of `configs/remediation.yaml`, while `configs/sentinelguard.yaml` contains a broader policy vocabulary.

This duplication should be removed before Chaos Harness v1 becomes executable.

### 9.1 Proposed single source of truth

Make:

```text
configs/sentinelguard.yaml
```

the canonical SentinelGuard policy file.

Move all active Guard thresholds and requirements into that file, including:

- fail-closed mode
- supported-RCA requirement
- counterfactual-recommendation requirement
- minimum causal score
- minimum priority score
- minimum net benefit
- maximum projected failure risk
- evidence requirement
- rollback requirement
- human-approval requirement
- action allowlist policy
- execution-authority policy
- verification requirements
- audit requirements

Keep remediation-planner-specific configuration in:

```text
configs/remediation.yaml
```

including:

- planner thresholds
- planner output paths
- remediation plan generation settings

The remediation config should reference SentinelGuard logically rather than duplicate its policy values.

### 9.2 Migration requirements

Before removing duplicated keys:

1. enumerate every SentinelGuard-related key currently consumed by source code
2. map each current key to its canonical location
3. add configuration-schema/contract tests
4. update Phase 13 preflight to verify the canonical policy file
5. update documentation and evidence manifest paths
6. confirm there is no behavior change from configuration consolidation alone

The merge must be treated as a configuration refactor, not as an opportunity to change thresholds.

Any threshold change requires a separately documented protocol revision.

---

## 10. Pre-run checklist

Before the first registered run starts, all preregistered inputs must be committed, immutable for v1, and have SHA-256 hashes recorded in the harness manifest.

Required pre-run items:

- scenario configuration files for latency, errors, and bad-deployment -> rollback
- the frozen bad-deployment profile at `configs/chaos_bad_deployment_v1.yaml`
- master seed
- per-run seeds or the deterministic seed-derivation rule
- complete randomized 60-run order
- fixed 36/12/12 train/validation/test run assignment
- detector-fit procedure
- exact TRAIN-run baseline IDs used for detector fitting
- detector feature schema and detector configuration
- frozen detector artifact hash after TRAIN-baseline fitting and before validation/test evaluation
- canonical SentinelGuard configuration
- remediation/execution configuration referenced by the registered protocol
- scorer scripts
- bootstrap/statistical analysis scripts
- evidence-schema/manifest definitions
- this design specification

The preregistration record must include the Git commit containing these items and the content hashes needed to reproduce the registered protocol.

No registered run may begin while any required preregistration item is uncommitted or unhashed.

---

## 11. Version-control and methodology rule

This design must be frozen before the first scored Chaos Harness v1 run.

After execution begins:

- scenario definitions may not be changed based on results
- run counts may not be reduced because runs are slow or unsuccessful
- thresholds may not be tuned against test-run outcomes
- failed or blocked runs may not be deleted
- split assignments may not be changed after model evaluation begins

Any necessary methodology change must create a new documented revision and preserve the original evidence.

---

## 12. Current design boundary

At design time, the repository already provides:

- local synthetic services
- latency/error failure-mode controls
- deployment change telemetry
- anomaly detection
- incident correlation
- RCA/challenger pipeline
- counterfactual decision support
- remediation planning
- SentinelGuard
- human-authorization gating
- local rollback adapter
- post-action recovery verification

Chaos Harness v1 is intended to connect these existing pieces into a repeatable, timestamped, preregistered experimental protocol.

It does not expand the current production boundary. SentinelOps remains LOCAL / SYNTHETIC / NOT CONNECTED for this harness.
