# Phase C Pre-Run Amendment 8

## Purpose

Amendment 8 fixes a resume-accounting gap discovered after Amendment 7.

The authoritative registered result for:

- primary: `C-TRAIN-BDR-12`
- spare: `C-SPARE-TRAIN-BDR-02`
- seed: `300872472`

is stored in:

`C-SPARE-TRAIN-BDR-02__a5_rerun_02`

with status:

`run_failed_after_injection`

However, the existing replacement logic only inspected the historical
base path:

`C-SPARE-TRAIN-BDR-02/run_summary.json`

That historical base summary remains
`infrastructure_invalid_interrupted`.

Without Amendment 8, resume accounting could ignore the authoritative
Amendment 7 result and incorrectly continue spare replacement logic.

## Methodology constraint

Amendment 8 does not authorize any new registered execution.

It is accounting/resolution logic only.

The frozen registered identity, seed, result, and denominator decision
remain unchanged.

No `_03` attempt is authorized.

## Change

Amendment 8 adds:

`authoritative_reexecution_summary(...)`

For a spare run ID and its specific replacement primary, the helper:

1. searches only suffixed re-execution artifact namespaces matching
   `<run_id>__*/run_summary.json`;
2. requires matching base `run_id`;
3. requires matching `replacement_for`;
4. requires `registered_result_eligible = true`;
5. requires `counted_in_analysis_denominator = true`;
6. returns the single authoritative matching summary;
7. returns `None` if no authoritative result exists;
8. fails closed if more than one authoritative result exists.

Replacement accounting now checks this authoritative re-execution result
before deciding whether an infrastructure-invalid base summary requires
another spare.

Historical base evidence is not overwritten.

## TDD evidence

RED:

- 4 Amendment 8 tests failed because
  `authoritative_reexecution_summary` did not exist.

GREEN:

- `4 passed`

Focused C6 regression:

- `90 passed`

## Real evidence resolution check

Read-only resolution against the actual evidence showed:

- `C-SPARE-TRAIN-BDR-01`:
  no authoritative re-execution result;
- `C-SPARE-TRAIN-BDR-02`:
  authoritative artifact
  `C-SPARE-TRAIN-BDR-02__a5_rerun_02`;
- authoritative status:
  `run_failed_after_injection`;
- registered-result eligible:
  `true`;
- counted in analysis denominator:
  `true`.

The next scheduled TRAIN primary after the resolved BDR-12 row is:

`C-TRAIN-LAT-11`

No spare execution occurred during this verification.
