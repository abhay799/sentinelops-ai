# Phase C C6 TRAIN Closeout

## Completion

The registered TRAIN partition completed with:

- registered TRAIN primaries: 36
- accounted primaries: 36
- remaining primaries: 0
- active run: null
- TRAIN loop process: not running
- registered TRAIN spares used: 4
- infrastructure-invalid primaries observed: 3

## Authoritative analysis denominator

The final authoritative TRAIN analysis denominator is:

34

Scenario denominator:

- bad_deployment_rollback: 11
- errors: 11
- latency: 12

## Authoritative status breakdown

- executed_verified: 8
- no_executable_rollback_request: 22
- plan_or_guard_stage_failed: 3
- run_failed_after_injection: 1

Total:

34

## Excluded primaries

Two registered primaries are excluded from the analysis denominator because
no valid authoritative registered result exists for them.

### C-TRAIN-BDR-04

- scenario: bad_deployment_rollback
- status: infrastructure_invalid_before_injection
- invalid reason: baseline_health_failed
- valid replacement: none
- denominator inclusion: excluded

### C-TRAIN-ERR-03

- scenario: errors
- status: infrastructure_invalid_before_injection
- invalid reason: baseline_health_failed

Both registered ERR spares were also infrastructure-invalid before injection:

- C-SPARE-TRAIN-ERR-01
- C-SPARE-TRAIN-ERR-02

No ad-hoc spare was created.

Denominator inclusion:

excluded

## Special authoritative mappings

### C-TRAIN-BDR-12

The base primary was infrastructure-invalid/interrupted.

The authoritative registered result is:

C-SPARE-TRAIN-BDR-02__a5_rerun_02

Status:

run_failed_after_injection

The authoritative summary explicitly records:

- registered_result_eligible: true
- counted_in_analysis_denominator: true

This result is counted once in the TRAIN denominator.

### C-TRAIN-LAT-11

The base namespace contains the preserved pre-executor launcher defect and is
not denominator eligible.

The authoritative registered result is:

C-TRAIN-LAT-11__launcher_retry_01

Status:

no_executable_rollback_request

This result is counted once in the TRAIN denominator.

## Denominator reconciliation

The final reconciliation produced:

- authoritative denominator: 34
- excluded primaries: 2

Scenario counts:

- bad_deployment_rollback: 11
- errors: 11
- latency: 12

Status counts:

- executed_verified: 8
- no_executable_rollback_request: 22
- plan_or_guard_stage_failed: 3
- run_failed_after_injection: 1

The reconciliation assertions passed.

## Closeout conclusion

Phase C C6 registered TRAIN execution is complete.

No registered TRAIN case should be rerun as part of closeout.

Subsequent work must consume the frozen authoritative TRAIN evidence and
proceed to TRAIN analysis / selection and the next held-out evaluation stage.
