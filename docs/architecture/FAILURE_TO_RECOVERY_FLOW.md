# Failure to Recovery Flow

## Purpose

This scenario-neutral flow shows the implemented engineering path from a local service degradation signal to a verified recovery or a reported recovery failure.

```mermaid
flowchart TD
    normal[Normal local service]
    signal[Degradation or failure signal]
    detect[Anomaly detection]
    correlate[Incident correlation]
    candidate[RCA candidate hypothesis]
    challenge[RCA challenger and causal disposition]
    counterfactual[Counterfactual evaluation]
    proposal[Remediation proposal]
    safety[Safety gate]
    approval[Human approval]
    action[Local sandbox action]
    verify[Health and readiness verification]
    recovered[Recovery verified]
    rollback[Rollback]
    reverify[Re-verify health and readiness]
    failed[Recovery failure recorded]
    blocked[No action]

    normal --> signal --> detect --> correlate --> candidate --> challenge --> counterfactual --> proposal --> safety --> approval --> action --> verify
    verify -->|recovery verified| recovered
    verify -->|recovery not verified| rollback --> reverify
    reverify -->|recovery verified| recovered
    reverify -->|recovery not verified| failed

    candidate -. remains a hypothesis .-> candidate
    safety -->|fail closed| blocked
    approval -->|not approved| blocked
```

## Explanation

Detection and correlation produce an incident context, followed by an RCA candidate and challenger/causal assessment. The candidate is never shown as a confirmed root cause. Counterfactual evaluation is simulated decision support for a remediation proposal; it cannot command an action.

Only a plan that survives safety controls and explicit human approval may enter local sandbox execution. Runtime health/readiness probes determine whether recovery is verified. If not, the configured rollback path is attempted and health/readiness is rechecked; remaining failure is recorded rather than treated as successful remediation.

## Provenance and runtime boundary

- **LOCAL:** Service, action, rollback, and verification paths refer to the local sandbox environment.
- **SIMULATED:** Counterfactual evaluation does not perform the depicted action.
- **DEVELOPMENT/SYNTHETIC DATA:** The upstream signal path is not evidence of production monitoring performance.
- **NOT CONNECTED:** No production deployment or production recovery claim is implied.
