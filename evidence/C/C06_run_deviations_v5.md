# Phase C C6 Amendment 5 Run Deviations

This file is an Amendment 5 addendum. It does not rewrite any prior
C6 run record, interruption record, frozen v4 file, or historical
deviation entry.

## C6-DEV-005 — Harness defect classification and rerun rule

### C-SPARE-TRAIN-BDR-02

- **Run:** `C-SPARE-TRAIN-BDR-02`
- **Partition / scenario:** `TRAIN` / `bad_deployment_rollback`
- **Original seed:** `300872472`
- **Replacement for:** `C-TRAIN-BDR-12`
- **Persisted stage:** `injection_activation`
- **Persisted injection_start:** `null`
- **Observed exception:** `KeyError: 'change_event'`
- **Root cause:** the registered bad-deployment executor read stale
  configuration keys (`change_event` and `degradation_stages`) while
  the frozen YAML defines `deployment_change` and
  `degraded_profile.stages`.
- **Amendment 5 classification:** `harness_defect`.
- **Environmental classification:** not applicable. The exception is
  neither an `httpx` timeout/connect error nor a recorded host event.
- **Result visibility:** no injected fault or registered algorithmic
  outcome was visible before the exception.
- **Analysis eligibility:** false.
- **Spare accounting:** the failed attempt does not consume a spare
  under Amendment 5 because it was stopped by a harness defect before
  `injection_start`.
- **Record preservation:** the existing
  `C-SPARE-TRAIN-BDR-02/run_summary.json`, `execution_state.json`,
  preflight evidence, and interruption record remain unchanged.
- **Re-execution authorization rule:** after the Amendment 5 fix is
  frozen and verified, this run may be executed again using its
  original run ID and original seed `300872472`, because the harness
  defect occurred before `injection_start` and no registered outcome
  was exposed. This exception applies only to a preserved
  pre-injection harness-defect attempt; it is not a general seed reuse
  rule.
- **Post-injection rule:** a harness defect discovered after
  `injection_start` is not eligible for original-seed re-execution,
  because fault/outcome visibility may already exist.

### Amendment 5 classification rule

1. Recorded host event -> infrastructure-invalid.
2. `httpx` timeout/connect exception before injection -> infrastructure-invalid.
3. `httpx` timeout/connect exception at/after injection -> run failed after injection.
4. Any other executor exception -> `harness_defect`.
5. `harness_defect` stops the loop immediately and consumes no spare.
6. Only `harness_defect` attempts with `injection_start = null` and no
   visible registered outcome may be re-executed with their original seed
   after the harness fix is frozen.

### Additional reserved spares

Amendment 5 derives two additional spare seeds per
scenario/partition cell using the unchanged frozen derivation rule:

`seed = first 8 bytes of SHA256('42|seed|partition|scenario|kind|ordinal')
interpreted unsigned big-endian, modulo 2147483646, plus 1`

The additional spares use `kind=spare` and ordinals `3` and `4`.

Validation produced:

- additional spare count: `18`
- collisions with all existing registered/spare seeds: `0`
- duplicate seeds among the 18 additions: `0`

These additions do not alter any existing registered run seed,
existing spare seed, execution order, scenario definition, or
algorithmic threshold.
