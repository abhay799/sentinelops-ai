# Phase C C6 Amendment 9 Run Deviations

## C6-DEV-009 — LAT-11 pre-executor launcher defect

Registered row:

- run ID: `C-TRAIN-LAT-11`
- scenario: `latency`
- seed: `693336793`

A manual invocation attempted to pass `run_registered_train` directly
as the `_execute_once()` executor override.

The wrapper calls custom executors positionally, while
`run_registered_train` requires the replacement argument as
keyword-only.

This caused:

`TypeError: run_registered_train() takes 1 positional argument but 2 were given`

The registered executor did not begin.

Observed evidence:

- base `run_summary.json` exists;
- status: `harness_defect`;
- no `execution_state.json`;
- no injection;
- no registered result;
- `registered_result_eligible = false`;
- `counted_in_analysis_denominator = false`;
- control state returned to `active_run = null`.

Preserved base summary SHA-256:

`a05396aab92e3b3a54491b2d7dbba5259b149b25b8fd134383ed6abf1398fde8`

Amendment 9 authorizes exactly one same-seed retry under:

`C-TRAIN-LAT-11__launcher_retry_01`

The historical base summary must remain byte-identical.

No `launcher_retry_02` is authorized.

The retry must use the frozen default executor path rather than passing
`run_registered_train` directly as a custom executor.
