# SentinelOps AI Architecture

## Purpose and scope

SentinelOps AI is a reliability intelligence and failure-prevention engineering platform. It turns local, generated observability artifacts into evidence-grounded investigation and controlled sandbox remediation decisions. It is not connected to production infrastructure.

The implemented lifecycle is:

```text
Sense
→ Detect
→ Predict
→ Correlate
→ Diagnose
→ Challenge RCA
→ Simulate
→ Prioritize
→ Plan
→ Guard
→ Human Authorization
→ Controlled Execution
→ Verify
→ Investigate
```

This order is a reasoning and safety model. It does not mean every stage is a continuously running production service.

## Implemented architecture

| Lifecycle stage | Implemented responsibility | Current boundary |
| --- | --- | --- |
| Sense | Local service environment emits metrics, logs, traces, and change/failure-mode signals; telemetry schemas and ingestion utilities model these inputs. | Demo/generated telemetry is not production telemetry. |
| Detect | Z-score, EWMA, Isolation Forest, and ensemble anomaly components identify abnormal service states. | Development pipeline; no production detection claim. |
| Predict | Leakage-conscious early-warning and Logistic Regression prediction pipelines use temporal splits and historical features. | Measurements are development/synthetic, not production performance. |
| Correlate | Temporal and dependency-graph relationships group anomalies into incidents. | Artifact-driven local processing. |
| Diagnose | RCA ranks candidate services from anomaly, change, graph, and incident evidence. | Candidates are hypotheses, not confirmed root cause. |
| Challenge RCA | Causal disposition and challenger logic seek contradictory evidence and alternative explanations. | A supported candidate remains unconfirmed. |
| Simulate | Counterfactual engine estimates risk reduction, operational risk, and net benefit for candidate actions. | Simulated decision support only; no execution authority. |
| Prioritize | SLO/business-impact and incident-priority modules rank operational attention. | Uses configured/local artifacts, not measured production impact. |
| Plan | Remediation planner proposes allowlisted actions when configured evidence thresholds are met. | A plan is not execution permission. |
| Guard | SentinelGuard applies fail-closed evidence, confidence, causal, benefit, priority, rollback, and approval requirements. | Guard approval is still insufficient without a human authorization and final gate. |
| Human Authorization | Phase 14 records an explicit approved human decision for a local execution request. | Approval records do not directly execute an action. |
| Controlled Execution | `execute_local_sandbox` validates a local target, the final gate, and a configured sandbox adapter, then probes `/live` and `/ready`. | Current mode is `local_sandbox`; production infrastructure is not connected. |
| Verify | Runtime verifies post-action liveness/readiness and attempts the configured rollback path when recovery fails. | Verification is against the local sandbox target. |
| Investigate | RAG retrieval over local runbooks, deterministic grounded generation, and four constrained investigation agents assemble an evidence-backed report. | Current provider is `DeterministicGroundedProvider`; agents cannot confirm RCA or execute remediation. |

## Components and boundaries

### Local service and observability environment

`services/`, `infra/docker-compose.phase2.yml`, and `monitoring/` define a local seven-service environment with Docker Compose, Prometheus, Grafana, and an OpenTelemetry Collector configuration. The collector exports to its debug exporter, and the repository contains local service failure-mode endpoints. These files establish a development/test environment; they do not establish a live production integration.

### Reliability intelligence pipeline

The `src/sentinelops/` packages implement telemetry handling, feature construction, anomaly detection, service graph/risk propagation, incident correlation, RCA and challenger analysis, prediction, counterfactual modeling, impact/prioritization, and remediation planning. Scripts construct artifacts under `data/processed/` and phase-specific tests exercise module contracts. This is a batch/artifact-oriented implementation rather than evidence of a continuously deployed operations control plane.

### Safety-controlled remediation

`configs/remediation.yaml` and `configs/execution.yaml` define allowlists, mandatory rollback, SentinelGuard and human-approval requirements, and fail-closed behavior. The execution runtime rejects a request unless all of the following are true:

- The execution configuration is fail-closed.
- The request is preapproval-ready and SentinelGuard-passed.
- Rollback is available.
- The target is local.
- The action is allowlisted and has a configured sandbox adapter.
- A human approval record is explicitly approved and identifies an approver.
- The target passes `/live` and `/ready` pre-checks.

The only configured sandbox action adapter is `rollback`, implemented as `POST /failure-mode/reset`. `traffic_shift` and `restart` occur in remediation/execution allowlists and planning/counterfactual configuration, but no corresponding sandbox adapter is configured; runtime tests demonstrate that a missing adapter blocks execution. They must not be represented as validated execution adapters.

When an attempted local action does not verify recovery, the runtime uses the configured rollback path, also `/failure-mode/reset`, then rechecks liveness and readiness. Thus rollback is both a required plan attribute and the currently configured sandbox execution adapter/recovery action.

### Investigation layer

Phase 15 reads evidence artifacts and local Markdown runbooks, retrieves with a deterministic local TF-IDF implementation, then invokes `DeterministicGroundedProvider` through a provider abstraction. The investigator, challenger, remediation, and verifier agents return evidence-oriented summaries only. Code and tests set their RCA-confirmation and execution authority to false; the API capability response also reports no SentinelGuard or human-approval bypass.

## Authority model

```text
Evidence artifacts + runbooks
        ↓
RCA hypotheses / challenger disposition / simulations / plans
        ↓
SentinelGuard (fail closed)
        ↓
Explicit human authorization
        ↓
Final local-only execution gate
        ↓
Configured rollback sandbox adapter and recovery checks
```

The LLM provider and agents are outside this authority path. They cannot independently confirm root cause, authorize or execute remediation, bypass SentinelGuard, or bypass human approval.

## Provenance and release boundary

Git history contains phase certification tags through `sentinelops-v0-phase15-certified` and a `sentinelops-v1.0.0` tag. The tagged and current `pyproject.toml` version is `0.1.0`, so the package version and release tag do not match. This documentation describes the current working tree, not a claim that all local files are release-tracked or production-deployed.

In particular, `frontend/` exists locally but is ignored/untracked in Git. It is local UI evidence only and is not part of the public/release implementation described here.
