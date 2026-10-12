# Phase C Pre-Run Amendment 5

## Scope

Amendment 5 is a pre-result methodology correction. No registered result is
authorized by this document itself.

The amendment fixes the registered bad-deployment executor contract, introduces
an explicit harness-defect classification, preserves pre-injection failed
attempt evidence, permits narrowly-scoped re-execution after a corrected
harness, and reserves two additional deterministic spare seeds per
scenario/partition.

## 1. Registered executor configuration defect

The frozen bad-deployment profile uses:

- `deployment_change`
- `degraded_profile.stages`

The registered executor previously attempted to read:

- `change_event`
- `degradation_stages`

The latency and errors scenario contracts already matched their frozen
configuration keys.

The executor was corrected to consume the actual frozen bad-deployment keys.
No frozen scenario YAML was edited.

Frozen bad-deployment YAML SHA-256:

`62e22a74c6714b505e4c8f91e707ba0b94fada5559b253ac3a62d2a01d291c2e`

## 2. Why the previous non-registry dry run did not expose the defect

The prior non-registry validation used the synthetic `run_dry_run()` path in
the non-registered harness.

The registered TRAIN path uses `run_registered_train()` and
`_activate_scenario()`.

The synthetic dry-run did not dereference the stale bad-deployment keys, so it
could pass while the registered executor still contained the contract defect.

Amendment 5 therefore validates all three scenarios through the exact
registered executor code path using seeds absent from both the registry and
reserved-spare sets.

## 3. Harness-defect classification

Recognizable environmental interruption is restricted to:

- recorded host events;
- `httpx` timeout exceptions;
- `httpx` connection exceptions.

A non-environmental exception raised by the harness is classified:

`harness_defect`

A harness defect:

- stops the loop immediately;
- consumes no spare;
- replaces no registered run;
- preserves the failed-attempt record;
- is excluded from the analysis denominator;
- is not registered-result eligible.

Post-injection environmental interruption remains a failed registered run
under the previously frozen post-injection rule.

## 4. Re-execution rule

A run stopped by `harness_defect` may be re-executed with its original seed
only when all of the following are true:

1. the defect occurred before `injection_start`;
2. no registered outcome became visible;
3. the harness defect has been corrected;
4. the original attempt record is preserved unchanged;
5. the re-execution is written under a distinct artifact namespace.

The registered identity and seed remain unchanged. Amendment 5 re-execution
artifacts use an explicit attempt suffix, e.g.:

`C-SPARE-TRAIN-BDR-02__a5_rerun`

This is not a general seed-reuse permission.

## 5. C-SPARE-TRAIN-BDR-02

The preserved attempt:

- run: `C-SPARE-TRAIN-BDR-02`
- original seed: `300872472`
- replacement target: `C-TRAIN-BDR-12`
- scenario: `bad_deployment_rollback`
- failed stage: `injection_activation`
- `injection_start`: null
- observed exception: `KeyError: 'change_event'`
- registered result eligible: false
- analysis denominator: false

Amendment 5 classifies this preserved attempt as `harness_defect`.

The original record is not rewritten. Its Amendment 5 interpretation is
documented in `evidence/C/C06_run_deviations_v5.md`.

After the v5 freeze, this specific attempt is eligible for narrowly-scoped
re-execution using its original seed and the separate `__a5_rerun` artifact
namespace.

## 6. Additional deterministic spares

Two additional spare ordinals, 3 and 4, are reserved for every
scenario/partition cell using the already frozen derivation rule:

`seed = (uint64_be(SHA256("42|seed|partition|scenario|spare|ordinal")[0:8]) mod 2147483646) + 1`

The reservations are recorded in:

`evidence/C/C04_additional_spares_v5.json`

Summary:

- additional spares: 18
- collisions with existing registered/reserved seeds: 0
- duplicates within new reservations: 0

The original frozen registry file is not rewritten.

## 7. Test evidence

Amendment 5 focused suite:

- 59 passed before the final stop-rule addition;
- subsequent TDD covered preserved harness-defect stop behavior and no-spare
  consumption.

Final requested combined regression:

- C6 Amendment 4
- C6 Amendment 5
- registered harness
- TRAIN loop
- Phase 13 remediation
- Phase 13 validation
- Phase 14 execution gate
- Phase 14 runtime

Result:

`104 passed in 8.55s`

## 8. Execution boundary

No registered row may be executed until Amendment 5 is committed and frozen
under annotated tag:

`freeze/C-prerun-v5`

No `--detach` execution is authorized.
