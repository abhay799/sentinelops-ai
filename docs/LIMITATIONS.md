# SentinelOps AI Limitations and Claim Boundaries

## Status vocabulary

| Label | Meaning |
| --- | --- |
| **IMPLEMENTED** | Code, configuration, scripts, or tests in this repository provide evidence of the capability. |
| **LOCAL** | Runs against the repository’s local service/sandbox environment. |
| **SIMULATED** | A modelled decision-support result; it does not perform a real-world action. |
| **SYNTHETIC** | Generated/development data or scenario inputs; not production telemetry. |
| **DETERMINISTIC** | Uses the repository’s deterministic local implementation, including `DeterministicGroundedProvider` and local TF-IDF retrieval. |
| **NOT CONNECTED** | No production infrastructure integration is established by this repository. |
| **NOT MEASURED** | No production performance, impact, or reliability measurement is established. |
| **PLANNED** | Mentioned as a future extension or available in planning/allowlist configuration, without a validated runtime implementation. |

## Current boundaries

- **IMPLEMENTED / LOCAL:** Phase 14 controlled remediation runs in `local_sandbox` mode and requires SentinelGuard, explicit human approval, local-target validation, rollback, a configured adapter, and recovery verification.
- **IMPLEMENTED / LOCAL:** The currently configured sandbox execution adapter is `rollback`, mapped to `POST /failure-mode/reset`. The configured rollback path is also `/failure-mode/reset`.
- **IMPLEMENTED / PLANNED:** `traffic_shift` and `restart` appear in allowlists, remediation planning, and counterfactual configuration. They are not configured sandbox adapters and are not validated execution adapters.
- **IMPLEMENTED / SIMULATED:** Counterfactual results estimate projected failure risk, benefit, and operational risk. They are not live experiments and cannot authorize execution.
- **IMPLEMENTED / SYNTHETIC / NOT MEASURED:** Failure prediction is implemented with development/synthetic artifacts and temporal evaluation logic. Its metrics are not production performance claims.
- **IMPLEMENTED / DETERMINISTIC:** Phase 15 uses `DeterministicGroundedProvider` and local retrieval over `docs/runbooks/`. No hosted model-provider connection is established.
- **IMPLEMENTED / NOT CONNECTED:** Production infrastructure is not connected. The repository contains local Compose services and local URLs only.
- **IMPLEMENTED / LOCAL:** Agents investigate evidence but cannot independently confirm RCA, execute remediation, bypass SentinelGuard, or bypass human approval.
- **LOCAL / NOT RELEASED:** `frontend/` exists locally but is ignored/untracked; it is not public/release UI evidence.

## Provenance and validation limitations

Git contains certification tags through Phase 15 and a `sentinelops-v1.0.0` tag. `pyproject.toml` remains version `0.1.0`, including at the tagged version, so package and tag versions differ.

The current tree lacks `scripts/phase15_preflight.py` and `tests/test_phase15_final.py`. Existing Phase 15 evidence is `scripts/build_phase15_final.py` and `tests/test_phase15_investigation.py`; missing files must not be represented as completed validation assets.

The current runbook directory contains the evidence-based RCA and SentinelGuard safety runbooks; it does not contain the payment-service reliability runbook previously named by the README. The local infrastructure files are Docker Compose and monitoring configuration; no Kubernetes or Helm manifests were found in `infra/` or `deployments/`.

## Explicit non-claims

SentinelOps does not claim production telemetry ingestion, production infrastructure access, autonomous production remediation, independently confirmed RCA by agents, production-grade traffic shifting/restart execution, production failure-prediction performance, or a released frontend from this repository evidence.
