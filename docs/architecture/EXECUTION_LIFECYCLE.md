# Execution Lifecycle

## Purpose

This diagram represents the exact local safety path implemented for a remediation request. It is intentionally narrower than the remediation allowlist.

```mermaid
flowchart TD
    plan[Remediation plan]
    guard[SentinelGuard]
    eligible[Technical eligibility pending human]
    approval[Explicit human approval]
    finalgate[Final execution gate]
    local[Local target validation]
    rollback[Rollback availability validation]
    adapter[Configured sandbox adapter validation]
    action[Controlled local sandbox action]
    health[Health and readiness verification]
    success[Executed and recovery verified]
    rollbackaction[Rollback and re-verify]
    failure[Recovery failed]
    blocked[Blocked fail closed]

    plan --> guard --> eligible --> approval --> finalgate
    finalgate --> local --> rollback --> adapter --> action --> health
    health -->|recovery verified| success
    health -->|recovery not verified| rollbackaction --> health
    rollbackaction -->|recovery still not verified| failure

    guard -->|requirements missing| blocked
    approval -->|missing or not approved| blocked
    finalgate -->|gate failure| blocked
    local -->|non local target| blocked
    rollback -->|rollback unavailable| blocked
    adapter -->|adapter unavailable| blocked

    configured[rollback is the configured sandbox execution adapter]
    adapter -. current adapter .-> configured
```

## Explanation

SentinelGuard can make a plan technically eligible, but that does not execute it. A separate human approval record and final gate are required. The runtime validates fail-closed configuration, prior Guard readiness, rollback availability, local target status, an allowlisted action, an implemented adapter, and an identified human approver. It then probes `/live` and `/ready` before and after action.

`rollback` is the only currently configured sandbox execution adapter, mapped to `POST /failure-mode/reset`. `traffic_shift` and `restart` are planning/allowlist concepts only; without sandbox adapters, they block at the final gate.

## Provenance and runtime boundary

- **LOCAL:** Current execution mode is `local_sandbox`.
- **NOT CONNECTED:** No production target can pass the local-target gate.
- **IMPLEMENTED:** Recovery failure triggers the configured rollback path and re-verification attempt.
