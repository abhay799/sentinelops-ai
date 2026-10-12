# Phase C Pre-Run Amendment 6

## Scope

Amendment 6 addresses one narrow case discovered after the Amendment 5 freeze:

An Amendment 5 re-execution attempt may fail for a recognized environmental
HTTPX exception before injection begins, leaving a partial attempt directory
with no registered outcome summary.

This amendment defines how that partial evidence is preserved and how one
subsequent attempt is isolated under a distinct artifact namespace.

## Observed case

Registered identity:

- run_id: `C-SPARE-TRAIN-BDR-02`
- seed: `300872472`
- scenario: `bad_deployment_rollback`
- replacement_for: `C-TRAIN-BDR-12`

First Amendment 5 rerun artifact:

`C-SPARE-TRAIN-BDR-02__a5_rerun`

Observed interruption:

- exception: `httpx.ReadTimeout`
- stage: `pre_injection_reset`
- injection_start: null
- run_summary.json: absent
- registered outcome visible: no

The first rerun artifact is preserved unchanged.

## Classification

Recognized environmental HTTPX exceptions for this rule are:

- `ReadTimeout`
- `ConnectTimeout`
- `ConnectError`

A partial attempt is eligible for environmental retry only when:

1. an execution_state.json exists;
2. the interruption is one of the recognized environmental HTTPX exceptions;
3. `injection_start` is null;
4. no registered result is being overwritten;
5. the prior attempt directory remains preserved.

Generic or non-environmental exceptions are not eligible under this rule.

## Retry namespace

The subsequent attempt uses the same registered identity and seed:

- run_id remains `C-SPARE-TRAIN-BDR-02`
- seed remains `300872472`

Only the artifact namespace changes.

The authorized second attempt namespace is:

`C-SPARE-TRAIN-BDR-02__a5_rerun_02`

The prior namespace:

`C-SPARE-TRAIN-BDR-02__a5_rerun`

must not be deleted, renamed, or overwritten.

This rule does not consume another spare and does not authorize seed changes.

## Execution boundary

No second registered attempt may run until Amendment 6 is committed and frozen
under:

`freeze/C-prerun-v6`

No `--detach` execution is authorized.
