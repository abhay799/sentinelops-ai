# SentinelOps AI Safety Invariants

## Core rule

```text
NO REMEDIATION WITHOUT
EVIDENCE

- CONFIDENCE
- SAFETY
- AUTHORIZATION
- ROLLBACK
- VERIFICATION
```

This is enforced as a set of fail-closed engineering boundaries. A recommendation, model score, counterfactual result, provider output, or agent response cannot independently cause remediation.

## Invariants

1. **Evidence is mandatory.** Investigation orchestration rejects an evidence bundle with no evidence sources. SentinelGuard configuration requires traceable evidence, and its runbook requires evidence before execution.
2. **RCA remains a hypothesis.** RCA produces ranked candidates; the challenger may support, weaken, reject, or leave them inconclusive. A supported candidate is not an independently confirmed root cause.
3. **Agents and the provider cannot confirm RCA.** The Phase 15 provider sets `root_cause_confirmed` to false. Investigator and challenger outputs retain non-confirmation, and validation rejects unsafe confirmation fields.
4. **Simulation is not execution.** Counterfactual outputs estimate projected risk, benefit, and operational risk. They are simulated decision-support results and have no execution authority.
5. **Planning is not authorization.** Planner output and SentinelGuard eligibility do not grant runtime execution permission.
6. **SentinelGuard fails closed.** Guard configuration requires supported RCA, causal confidence, priority, projected benefit, rollback, human approval, and traceable evidence. Missing conditions block progression.
7. **Human authorization is mandatory.** The final execution gate requires a record with `approval_status == approved` and a non-empty approver identity. Recording approval does not itself execute an action.
8. **Execution is local-only.** The final gate rejects non-local targets. Current execution mode is `local_sandbox`; production infrastructure is not connected.
9. **Execution requires an implemented adapter.** An action must be allowlisted *and* present in `sandbox_actions`. The currently configured adapter is `rollback` using `POST /failure-mode/reset`. Although `traffic_shift` and `restart` are allowlisted/plannable, no adapter is configured for either and they are not validated execution adapters.
10. **Rollback is required and operationally configured.** A request without rollback availability fails the final gate. The configured rollback path is `/failure-mode/reset`, the same local sandbox adapter used for the configured `rollback` action.
11. **Verification is mandatory.** Local runtime probes `/live` and `/ready` before action; successful action requires post-action recovery verification. Failed recovery triggers a rollback attempt and another recovery check.
12. **No agent bypass exists.** The provider, all four agents, final report safety fields, and `/capabilities` declare no agent execution authority, no SentinelGuard bypass, and no human-approval bypass.

## Negative authority matrix

| Actor or artifact | May independently confirm RCA? | May execute remediation? | May bypass Guard/human approval? |
| --- | ---: | ---: | ---: |
| RCA/challenger output | No | No | No |
| Counterfactual output | No | No | No |
| Remediation planner | No | No | No |
| SentinelGuard | No | No | No |
| `DeterministicGroundedProvider` | No | No | No |
| Investigation agents | No | No | No |
| Human approval record | No | No; it enables final-gate evaluation only | No |
| Local execution runtime | No | Only after every final-gate condition passes | No |

## Scope of these controls

These invariants are evidenced by repository configuration, source, scripts, and tests in a local environment. They do not prove production authorization integration, external change control, production telemetry coverage, or production recovery performance.
