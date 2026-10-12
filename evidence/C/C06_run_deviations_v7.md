# Phase C C6 Amendment 7 Run Deviations

This file is an Amendment 7 addendum. It does not rewrite any previous
run record, interruption record, amendment, freeze manifest, or
historical evidence.

## C6-DEV-007 — Post-injection orphaned attempt finalization policy

### Registered identity

- Run ID: `C-SPARE-TRAIN-BDR-02`
- Partition: `TRAIN`
- Scenario: `bad_deployment_rollback`
- Seed: `300872472`
- Replacement for: `C-TRAIN-BDR-12`
- Artifact namespace:
  `C-SPARE-TRAIN-BDR-02__a5_rerun_02`

### Preserved state

The second authorized re-execution persisted:

- `current_stage = injection`
- `injection_start = 2026-10-12T19:59:52.267600+00:00`
- no `run_summary.json`
- no persisted ground-truth result file
- no matching active train-loop control record

Pre-finalization SHA-256:

`execution_state.json`

`40684966fe819b0c34eab060debb2e7fe991212b0949535ff278a56c325a5779`

### Operational finding

The attempt was started by direct invocation of
`run_registered_train()` instead of `_execute_once()`.

As a result, the train-loop exception wrapper did not create the normal
interruption summary/control record when the process terminated.

The registered artifact collision guard subsequently prevented another
execution in the same namespace.

No qualifying host/container restart or stop event was observed during
the relevant interruption window.

### Classification

Because persisted `injection_start` is non-null, the frozen classification
rule requires:

`run_failed_after_injection`

unless a recorded host event overrides it.

Therefore this attempt:

- is a registered result;
- remains in the analysis denominator;
- is not infrastructure-invalid;
- is not replaceable;
- must not be rerun;
- consumes no additional spare beyond the already-selected registered
  identity.

### Amendment 7 remedy

After Amendment 7 is frozen, the preserved `_02` artifact may be
finalized in-place by writing only its missing `run_summary.json`.

The existing `execution_state.json` must retain the exact pre-finalization
SHA-256 shown above.

No `_03` execution is authorized.
