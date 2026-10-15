# Phase C C6 Amendment 10 Run Deviations

## C6-DEV-010 — Registered spare exhaustion

The TRAIN loop stopped after:

`C-TRAIN-BDR-04`

with:

- scenario: `bad_deployment_rollback`
- seed: `1926564664`
- status: `infrastructure_invalid_before_injection`
- invalid reason: `baseline_health_failed`

Both registered BDR spares were already consumed by the earlier
`C-TRAIN-BDR-12` replacement sequence:

- `C-SPARE-TRAIN-BDR-01`
- `C-SPARE-TRAIN-BDR-02`

No third registered BDR spare exists.

Amendment 10 does not authorize a new spare and does not reuse a spare
already assigned to another primary.

Instead, when all registered scenario spares are exhausted by other
primaries, the current infrastructure-invalid primary remains preserved and
unreplaced, and the TRAIN loop continues to the next registered primary.

For the observed case the next primary is:

`C-TRAIN-ERR-10`

This rule is applied uniformly to equivalent exhausted-spare conditions.
