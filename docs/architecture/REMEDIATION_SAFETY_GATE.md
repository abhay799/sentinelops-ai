# Remediation Safety Gate

## Purpose

This diagram separates planning, Guard assessment, human authorization, and execution. Each is a distinct state transition.

```mermaid
flowchart TD
    recommendation[Planner recommendation]
    supported[Supported RCA requirement]
    causal[Minimum causal score]
    priority[Priority threshold]
    benefit[Positive net benefit]
    risk[Projected risk constraint]
    evidence[Traceable evidence]
    rollback[Rollback available]
    allowlist[Allowlisted action]
    guard[SentinelGuard technical decision]
    human[Human approval record]
    target[Known local target]
    adapter[Sandbox adapter available]
    finalgate[Final execution gate]
    execution[Controlled local sandbox execution]
    blocked[Blocked]

    recommendation --> guard
    supported --> guard
    causal --> guard
    priority --> guard
    benefit --> guard
    risk --> guard
    evidence --> guard
    rollback --> guard
    allowlist --> guard
    guard --> human --> finalgate --> execution
    target --> finalgate
    rollback --> finalgate
    allowlist --> finalgate
    adapter --> finalgate

    guard -->|not technically eligible| blocked
    human -->|not explicitly approved| blocked
    target -->|unknown or non local| blocked
    rollback -->|unavailable| blocked
    allowlist -->|not allowlisted| blocked
    adapter -->|unavailable| blocked
    finalgate -->|any requirement fails| blocked

    note1[Planner recommendation is not SentinelGuard approval]
    note2[SentinelGuard approval is not human authorization]
    note3[Human authorization is not execution]
    recommendation -.-> note1
    guard -.-> note2
    human -.-> note3
```

## Explanation

The planner may recommend an action after its own thresholds. SentinelGuard independently applies its stricter technical decision requirements. Even a technically eligible result is pending explicit human authorization. The final gate then rechecks local targeting, rollback, allowlisting, and configured adapter availability before an action can be attempted.

The repository configures a sandbox adapter only for `rollback`. `traffic_shift` and `restart` can be present in planning and allowlist data, but are blocked because no sandbox adapter is available for them.

## Provenance and runtime boundary

- **LOCAL:** Known targets must be local for execution.
- **NOT CONNECTED:** Production targets are outside the configured execution boundary.
- **IMPLEMENTED:** Guard and final-gate logic are fail-closed.
