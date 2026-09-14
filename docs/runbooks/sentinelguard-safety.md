# SentinelGuard Remediation Safety Runbook

No remediation action should execute merely because it has been
recommended by an AI or ranking model.

Before execution verify:

- RCA candidate survived challenger review
- counterfactual simulation predicts benefit
- business impact justifies intervention
- action is allowlisted
- target is known
- rollback is available
- SentinelGuard passes
- human approval exists

Execution must fail closed when any required safety condition
cannot be verified.

After execution, service recovery must be independently verified.
