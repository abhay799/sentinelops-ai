# Phase C Pre-Run Amendment 7

## Purpose

Amendment 7 addresses a narrow evidence-finalization gap discovered after
the Amendment 6 authorized re-execution attempt for:

- registered run ID: `C-SPARE-TRAIN-BDR-02`
- seed: `300872472`
- scenario: `bad_deployment_rollback`
- replacement for: `C-TRAIN-BDR-12`
- artifact namespace:
  `C-SPARE-TRAIN-BDR-02__a5_rerun_02`

The attempt crossed the persisted `injection_start` boundary and then
terminated without producing `run_summary.json`.

No third execution attempt is authorized.

## Preserved observed state

The preserved `_02/execution_state.json` records:

- current stage: `injection`
- injected service: `payment-service`
- injection start:
  `2026-10-12T19:59:52.267600+00:00`
- registered run ID: `C-SPARE-TRAIN-BDR-02`
- registered seed: `300872472`
- replacement for: `C-TRAIN-BDR-12`

SHA-256 of the preserved execution state before Amendment 7 finalization:

`40684966fe819b0c34eab060debb2e7fe991212b0949535ff278a56c325a5779`

The original historical attempt and the first Amendment 5 re-execution
attempt remain immutable.

## Classification rule

The already-frozen interruption rule remains unchanged:

1. a recorded host event may classify an interruption as
   infrastructure-invalid;
2. otherwise, an executor interruption at or after a persisted
   `injection_start` is `run_failed_after_injection`;
3. `run_failed_after_injection` is a registered result;
4. it remains in the analysis denominator;
5. it is not replaceable and is not eligible for original-seed
   re-execution.

No qualifying host/container restart or stop event was observed for the
`_02` interruption window.

## Evidence-finalization gap

The `_02` attempt was invoked directly through `run_registered_train()`
rather than through the train-loop `_execute_once()` wrapper.

Therefore:

- no train-loop `active_run` control record was established for `_02`;
- after termination, `active_run` was `null`;
- the frozen restart recovery path could not safely finalize the
  attempt;
- the artifact namespace already existed, preventing accidental rerun;
- the persisted post-injection state remained available and immutable.

## Amendment 7 change

Amendment 7 adds a narrowly scoped helper:

`finalize_orphaned_post_injection_attempt(...)`

The helper may only finalize an existing attempt directory when:

- `execution_state.json` exists;
- `injection_start` is non-null;
- `run_summary.json` does not already exist.

It writes only `run_summary.json` in the same artifact namespace.

The helper:

- preserves the registered run ID and registered seed;
- records the artifact namespace separately;
- classifies the result as `run_failed_after_injection`;
- sets `registered_result_eligible = true`;
- sets `counted_in_analysis_denominator = true`;
- does not create a replacement run;
- does not consume another spare;
- does not rewrite `execution_state.json`;
- refuses pre-injection attempts;
- refuses overwrite of an existing summary.

## Execution prohibition

Amendment 7 does not authorize:

- `_03`;
- another execution of seed `300872472`;
- another spare for `C-TRAIN-BDR-12`;
- deletion or renaming of `_02`;
- mutation of historical evidence;
- result-dependent tuning.

## Verification

TDD sequence:

- RED: 4 tests failed because
  `finalize_orphaned_post_injection_attempt` did not exist.
- GREEN: 4 Amendment 7 tests passed.
- focused C6 regression: `86 passed`.
- full Amendment 7 regression: `118 passed`.

The Amendment 6 test file also received a test-loader-only correction so
that it imports the standalone train-loop script by path in the same way
as Amendment 7. This does not change production behavior or methodology.
