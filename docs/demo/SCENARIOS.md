# Deterministic Demo Scenarios

All scenarios are deterministic local UI data. They are **LOCAL**, **SYNTHETIC**, **DETERMINISTIC**, and **NOT CONNECTED** unless otherwise stated. They do not claim production incidents, production telemetry, or production remediation.

| ID | Purpose and lifecycle stage | Engineering behavior | Does not claim |
| --- | --- | --- | --- |
| `normal-operation` | Sense | Seven healthy local demo services; no incident, RCA, plan, execution, or recovery event. | That SentinelOps invents an incident without evidence. |
| `early-degradation` | Predict | Cautious payment-service deterioration and development-data early warning. | Confirmed RCA or remediation authority. |
| `correlated-multi-signal` | Correlate | Anomaly, temporal, graph, and change evidence create an incident. | Root-cause confirmation. |
| `competing-rca-hypotheses` | Diagnose | Payment and order candidates are ranked hypotheses with evidence. | A confirmed root cause. |
| `adversarial-rca-challenge` | Challenge | Challenger evaluates alternatives and may weaken a candidate. | Agent RCA confirmation. |
| `sentinelguard-rejection` | Guard | Missing rollback availability blocks a planner proposal. | Human approval or execution after Guard rejection. |
| `human-authorization-pending` | Authorize | `eligible_pending_human`; technical checks pass while `execution_allowed` remains false. | Automatic authorization or execution. |
| `safe-local-recovery` | Investigate | Deterministic local rollback adapter execution, post-live/post-ready checks, and verified recovery. | Production remediation. Rollback is the configured sandbox adapter. |
| `failed-verification-safe-failure` | Verify | **LOCAL / SYNTHETIC / SIMULATED** failed verification, rollback attempt, and re-verification path. | A production rollback or verified recovery. |

`traffic_shift` and `restart` appear only as simulated planning/allowlist concepts. Neither is represented as a validated execution adapter. Investigation agents cannot confirm RCA, execute remediation, bypass SentinelGuard, or bypass human authorization.
