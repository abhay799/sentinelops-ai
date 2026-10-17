# Phase C C6 TRAIN Analysis Methodology

## Scope

Post-TRAIN analysis for the frozen Phase C C6 registered TRAIN corpus.

No registered TRAIN case was rerun.

## Frozen closeout

- Commit: 379c43895fac1e7b3ff8a58a08cfeee2c764cb3c
- Tag: freeze/C-train-closeout
- Registered TRAIN primaries: 36
- Authoritative denominator: 34

## Analyzer compatibility

The analyzer was updated to support the current execution_result schema while preserving legacy execution support.

Current C6 summaries without a structured guard-decision field are reported as not_recorded. Guard decisions are not inferred from console output or run status.

## Authoritative selection

Excluded:
- C-TRAIN-BDR-04
- C-TRAIN-ERR-03

Authorized replacements:
- C-TRAIN-BDR-12 -> C-SPARE-TRAIN-BDR-02__a5_rerun_02
- C-TRAIN-LAT-11 -> C-TRAIN-LAT-11__launcher_retry_01

Historical spare and retry namespaces are not independently counted.

## Final denominator

- Total: 34
- bad_deployment_rollback: 11
- errors: 11
- latency: 12

Status counts:
- executed_verified: 8
- no_executable_rollback_request: 22
- plan_or_guard_stage_failed: 3
- run_failed_after_injection: 1

Guard evidence:
- not_recorded: 33
- run_failed_after_injection: 1

## Verification

- Focused C6 tests: 4 passed
- Phase C regression: 7 passed
- Full regression: 276 passed, 1 expected integration skip
- Real TRAIN denominator reconciliation: PASS
- Official JSON validation: PASS

## Output

- evidence/C/C06_train_analysis.json
