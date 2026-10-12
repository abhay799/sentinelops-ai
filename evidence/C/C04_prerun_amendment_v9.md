# Phase C Pre-Run Amendment 9

## Purpose

Amendment 9 addresses a launcher-only failure created while attempting
to resume the registered TRAIN schedule at:

`C-TRAIN-LAT-11`

Registered identity:

- run ID: `C-TRAIN-LAT-11`
- scenario: `latency`
- seed: `693336793`
- partition: `TRAIN`

The first launch attempt failed before the registered executor began.

## Observed launcher defect

The attempted launch passed `run_registered_train` directly as the
`_execute_once()` executor override.

`_execute_once()` invokes custom executors as:

`executor(entry, replacement_for)`

but `run_registered_train()` requires its replacement argument as a
keyword-only argument.

The resulting exception was:

`TypeError: run_registered_train() takes 1 positional argument but 2 were given`

The frozen default execution path itself was already correct:

`_execute_once(..., executor=None)`

uses `_default_executor()`, which invokes:

`run_registered_train(..., replacement_for=replacement_for)`

## Evidence boundary

The failed launcher attempt produced:

`evidence/C/C06_train_runs/C-TRAIN-LAT-11/run_summary.json`

with:

- status: `harness_defect`
- registered_result_eligible: `false`
- counted_in_analysis_denominator: `false`
- harness_defect_reason:
  `non_environmental_exception:TypeError`

Critically:

- no `execution_state.json` exists;
- no injection began;
- no registered executor runtime state was persisted;
- no registered result was observed;
- control state returned to `active_run = null`.

The preserved base summary SHA-256 is:

`a05396aab92e3b3a54491b2d7dbba5259b149b25b8fd134383ed6abf1398fde8`

The base summary must not be deleted, renamed, or overwritten.

## Retry rule

Amendment 9 permits one same-identity, same-seed execution under the
new artifact namespace:

`C-TRAIN-LAT-11__launcher_retry_01`

This retry is permitted only when all of the following hold:

1. the base `run_summary.json` exists;
2. base status is `harness_defect`;
3. `registered_result_eligible = false`;
4. `counted_in_analysis_denominator = false`;
5. no base `execution_state.json` exists;
6. the preserved traceback contains the exact launcher call pattern:
   `result = executor(entry, replacement_for)`;
7. the preserved traceback contains the exact argument mismatch:
   `TypeError: run_registered_train() takes 1 positional argument but 2 were given`.

Any unrelated harness `TypeError` is not retry-eligible.

## Resume behavior

When the narrow launcher-defect predicate is satisfied:

- the original base summary remains immutable;
- the train loop checks
  `C-TRAIN-LAT-11__launcher_retry_01/run_summary.json`;
- if the retry summary already exists, it is reused;
- otherwise `_execute_once()` is invoked once with:
  `attempt_label="launcher_retry_01"`;
- no second launcher retry namespace is authorized.

## TDD evidence

Initial RED:

- 5 tests failed because
  `preexecutor_launcher_retry_eligible()` did not exist.

Eligibility GREEN:

- 5 passed.

Resume behavior RED:

- 5 passed, 2 failed because the train loop still stopped on the base
  launcher-defect summary.

After implementing retry resolution, the two remaining failures were
test-fixture/status-snapshot assertion issues only.

Final Amendment 9 test result:

- 7 passed.

Focused A5-A9/C6 regression:

- 97 passed.

## Real evidence eligibility check

Read-only verification against the actual LAT-11 evidence showed:

- eligible: `true`
- base summary exists: `true`
- execution state exists: `false`
- retry namespace exists: `false`
- base status: `harness_defect`
- registered result eligible: `false`
- counted in denominator: `false`
- control active run: `null`

No retry execution occurred during this verification.
