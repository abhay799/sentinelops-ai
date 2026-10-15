# Phase C Pre-Run Amendment 10

## Purpose

Amendment 10 defines deterministic continuation behavior when a TRAIN
primary is infrastructure-invalid and all registered scenario spares are
already consumed by other primaries.

Observed case:

- run ID: `C-TRAIN-BDR-04`
- scenario: `bad_deployment_rollback`
- seed: `1926564664`
- status: `infrastructure_invalid_before_injection`
- invalid reason: `baseline_health_failed`

Both registered BDR spares were already consumed while replacing:

`C-TRAIN-BDR-12`

No third BDR spare exists in the frozen registry.

## Existing frozen behavior

Before Amendment 10, `_replacement_complete()` raised:

`STOP: both reserved TRAIN spares are used/invalid ... no ad-hoc replacement is permitted`

This correctly prevented creation of an unregistered spare, but it also
prevented execution of all later independent registered TRAIN rows.

## Amendment 10 rule

When a primary is infrastructure-invalid:

1. inspect only the registered spares for the same scenario;
2. if an unused registered spare exists, preserve the existing replacement
   workflow;
3. if a registered spare already belongs to this same primary, preserve the
   existing replacement/accounting workflow;
4. if every registered scenario spare already exists and is assigned to a
   different primary, classify the registered replacement capacity as
   exhausted for this primary;
5. do not create, invent, reuse, or renumber a spare;
6. preserve the infrastructure-invalid primary exactly as recorded;
7. continue to the next registered primary in the frozen TRAIN schedule.

This is a continuation/accounting rule only.

It does not transform the invalid primary into a valid result and does not
place it into the analysis denominator.

## New helper

Amendment 10 adds:

`registered_spares_exhausted_for_primary(...)`

It returns true only when all registered scenario spares already have
summaries and none is available or already assigned to the current primary.

## TDD evidence

Initial RED:

- 3 tests failed because
  `registered_spares_exhausted_for_primary()` did not exist.

Fixture correction:

- Amendment 10 synthetic reserved-spare rows were updated to include the
  required `spare_ordinal` field used by the frozen registry sorter.

Helper GREEN:

- 3 passed.

Continuation RED:

- 3 passed, 2 failed at the existing `_replacement_complete()` hard stop.

Continuation GREEN:

- 5 passed.

Focused A5-A10/C6 regression:

- 102 passed.

## Real evidence verification

Read-only verification against the real registered evidence showed:

- primary: `C-TRAIN-BDR-04`
- registered-spares-exhausted: `true`
- `C-SPARE-TRAIN-BDR-01` belongs to `C-TRAIN-BDR-12`
- `C-SPARE-TRAIN-BDR-02` belongs to `C-TRAIN-BDR-12`
- no ad-hoc spare was created
- control `active_run` is null
- next registered TRAIN primary:
  `C-TRAIN-ERR-10`

No registered execution occurred during Amendment 10 verification.
