# SentinelOps AI

### Reliability Intelligence & Failure Prevention Engineering Platform

SentinelOps AI is an end-to-end AIOps and reliability intelligence platform designed to detect, predict, diagnose, challenge, simulate, prioritize, and safely respond to failures in distributed systems.

Rather than stopping at anomaly detection, SentinelOps follows the complete reliability lifecycle:

**Sense → Detect → Predict → Correlate → Diagnose → Challenge RCA → Simulate → Prioritize → Plan → Guard → Human Authorization → Controlled Execution → Verify → Investigate**

The system combines observability, machine learning, graph intelligence, causal reasoning, failure prediction, counterfactual simulation, SLO-aware prioritization, safety-controlled remediation, RAG, and multi-agent investigation. Current remediation is local sandbox execution; production infrastructure is not connected.

---

## Core Principle

SentinelOps follows one strict engineering rule:

> SentinelOps must never claim root cause or execute remediation without traceable evidence, confidence, safety constraints, and rollback/recovery capability.

The LLM and agent layers have no direct execution authority.

## Implementation Status & Provenance

- **IMPLEMENTED:** Repository code and tests cover Phases 0–15.
- **LOCAL:** Controlled remediation is a local sandbox path, not production execution.
- **SIMULATED:** Counterfactual outputs are decision-support simulations, not infrastructure actions.
- **SYNTHETIC:** Demo/generated telemetry and development evaluation data are not production telemetry.
- **DETERMINISTIC:** The Phase 15 provider is `DeterministicGroundedProvider`; retrieval is local and deterministic.
- **NOT CONNECTED:** Production infrastructure is not connected by this repository.
- **NOT MEASURED:** Failure-prediction metrics are development/synthetic measurements, not production performance.
- **PLANNED:** `traffic_shift` and `restart` are configured for planning/allowlisting but are not validated sandbox execution adapters. The configured sandbox adapter is `rollback` (`POST /failure-mode/reset`).

Git contains certification tags through Phase 15 and `sentinelops-v1.0.0`; `pyproject.toml` declares version `0.1.0`, so tag and package versions differ. The local `frontend/` directory is ignored/untracked and is not a public/release UI claim.

See [project architecture](docs/architecture/PROJECT_ARCHITECTURE.md), [phase index](docs/architecture/PHASE_INDEX.md), [safety invariants](docs/architecture/SAFETY_INVARIANTS.md), [validation scope](docs/VALIDATION.md), and [limitations](docs/LIMITATIONS.md).

---

# Architecture

```text
Distributed Services
        │
        ▼
Metrics / Logs / Traces / Changes
        │
        ▼
Telemetry Platform
        │
        ▼
Feature Platform
        │
        ▼
Anomaly Detection
        │
        ▼
Service Dependency Graph
        │
        ▼
Incident Correlation
        │
        ▼
Evidence-Based RCA
        │
        ▼
RCA Challenger / Disproof Engine
        │
        ▼
Failure Prediction
        │
        ▼
Counterfactual Simulation
        │
        ▼
SLO + Business Impact Intelligence
        │
        ▼
Remediation Planner
        │
        ▼
SentinelGuard
        │
        ▼
Human Approval
        │
        ▼
Controlled Sandbox Remediation
        │
        ▼
Recovery Verification / Rollback
        │
        ▼
Evidence Bundle + RAG
        │
        ▼
Multi-Agent Investigation
        │
        ▼
Investigation API
```

---

# Major Capabilities

### Observability

SentinelOps collects and processes:

* Metrics
* Structured logs
* Distributed traces
* Deployment/change events
* Service health signals
* Dependency information

OpenTelemetry, Prometheus, Kafka, and structured telemetry form the observability foundation.

---

### Feature Platform

The feature platform builds point-in-time-safe service features including:

* Request rate
* Request-rate change
* Error rate
* Mean latency
* P95 latency
* P99 latency
* Trace count
* Change-event count
* Dependency count
* CPU consumption
* Memory usage
* Memory growth
* Temporal historical features

Feature validation includes leakage protection.

---

### Anomaly Detection

SentinelOps combines multiple detection techniques:

* Z-score
* EWMA
* Isolation Forest
* Ensemble anomaly voting

Outputs include anomaly scores and detected abnormal service states.

---

### Service Dependency Intelligence

A graph representation models dependencies between services.

Graph intelligence supports:

* Upstream impact analysis
* Downstream dependency analysis
* Shortest paths
* Failure-propagation paths
* Graph-aware risk propagation
* Blast-radius reasoning

---

### Incident Correlation

Related anomalies are grouped into incidents using:

* Temporal proximity
* Dependency-graph relationships
* Service relationships
* Anomaly strength

Each incident receives evidence and confidence information.

---

# Evidence-Based Root Cause Analysis

SentinelOps produces ranked RCA hypotheses instead of immediately declaring a root cause.

Evidence may include:

* Anomaly strength
* Recent changes
* Graph impact
* Incident correlation
* Primary-service evidence

A candidate remains:

```text
unconfirmed
```

until later safety and human-review stages.

---

# RCA Challenger

The Challenger actively attempts to disprove the leading RCA hypothesis.

It checks:

* Weak anomaly evidence
* Missing change evidence
* Graph inconsistencies
* Stronger alternative hypotheses
* Causal consistency
* Contradictory evidence

Possible outcomes include:

```text
supported
weakened
rejected
inconclusive
```

Even a supported hypothesis is not independently confirmed by an AI agent.

---

# Failure Prediction

SentinelOps includes a leakage-safe early-warning pipeline.

It predicts future failure using historical signals such as:

* Latency degradation
* Error-rate growth
* Request-rate shifts
* Change activity

A supervised Logistic Regression baseline is also trained using temporal splitting.

Example evaluation from the development dataset:

```text
Precision: 0.2778
Recall:    1.0000
F1:        0.4348
Lead time: 1.8 events
```

The current dataset is intentionally small and synthetic, so these metrics demonstrate pipeline behavior rather than production performance.

---

# Counterfactual Simulation

Before recommending remediation, SentinelOps asks questions such as:

> What happens to failure risk if payment-service is rolled back?

Supported simulated actions include:

* Rollback
* Traffic shift
* Restart
* No action

The simulator estimates:

* Baseline failure risk
* Projected failure risk
* Risk reduction
* Operational risk
* Net benefit

Counterfactual simulation has no execution authority.

---

# SLO and Business Impact Intelligence

SentinelOps prioritizes incidents using both technical and business impact.

Signals include:

* Service criticality
* Latency SLO burn
* Error-rate SLO burn
* Anomaly risk
* Predicted failure probability
* Blast radius

This produces a remediation-priority score and priority ranking.

---

# Remediation Planner

The planner combines:

* RCA disposition
* Causal-consistency score
* Counterfactual recommendation
* Incident priority
* Predicted remediation benefit
* Rollback availability

Plans may progress to:

```text
proposed_pending_guard
```

but are still not executable.

---

# SentinelGuard

SentinelGuard is an independent remediation safety layer.

It verifies:

* Planner readiness
* Action allowlist
* Supported RCA
* Minimum causal confidence
* Business priority
* Positive expected benefit
* Projected post-action risk
* Rollback capability
* Traceable evidence

SentinelGuard operates fail-closed.

A technically valid plan may become:

```text
eligible_pending_human
```

This still does not provide execution permission.

---

# Human-Controlled Execution

Phase 14 introduces controlled remediation inside the local SentinelOps sandbox. The configured sandbox execution adapter is rollback; `traffic_shift` and `restart` may be planned or allowlisted but are not validated execution adapters.

Execution requires:

1. SentinelGuard approval
2. Explicit human approval
3. Local-target validation
4. Allowlisted remediation adapter
5. Rollback availability
6. Health/readiness pre-check
7. Final execution gate

Example lifecycle:

```text
SentinelGuard Approved
        ↓
Execution Request
        ↓
Human Approval
        ↓
Final Safety Gate
        ↓
Controlled Action
        ↓
Recovery Verification
        ↓
Success
     or
Automatic Rollback
```

The certified development execution successfully produced:

```text
final_gate_passed = true
recovery_verified = true
execution_status = executed_verified
```

---

# Recovery Verification

After remediation SentinelOps independently verifies:

* `/live`
* `/ready`
* Recovery status
* Action response
* Rollback status

If recovery fails, SentinelOps attempts rollback to the safe state.

---

# RAG Investigation Layer

SentinelOps contains an evidence-grounded reliability knowledge base.

Current runbooks include:

* Evidence-based RCA
* SentinelGuard remediation safety

TF-IDF retrieval provides deterministic local retrieval during the certified build.

External embedding/vector databases can later replace the retrieval backend.

---

# Multi-Agent Investigation

The final investigation workflow includes:

### Investigator Agent

Examines incident evidence and leading RCA candidates.

### Challenger Agent

Looks for contradictions and alternative explanations.

### Remediation Agent

Reviews safe remediation recommendations and SentinelGuard decisions.

### Verification Agent

Reviews whether system recovery was actually verified.

Agents operate using traceable evidence.

They cannot:

* Independently confirm RCA
* Execute remediation
* Bypass SentinelGuard
* Bypass human approval

---

# Grounded LLM Provider Architecture

The LLM layer uses a provider abstraction.

The certified implementation uses:

```text
DeterministicGroundedProvider
```

This allows future integration with providers such as:

* Mistral
* Cohere
* OpenAI
* Local models

without changing the core SentinelOps safety contracts.

---

# Investigation API

SentinelOps exposes a FastAPI investigation service.

Start it with:

```powershell
python scripts\run_phase15_api.py
```

Server:

```text
http://127.0.0.1:8200
```

Swagger:

```text
http://127.0.0.1:8200/docs
```

Endpoints:

```text
GET /live
GET /ready
GET /investigation/latest
GET /capabilities
```

The capabilities endpoint explicitly reports that agents cannot execute remediation or bypass safety controls.

---

# Distributed Test Environment

The local reliability environment contains seven services:

| Service              | Port |
| -------------------- | ---: |
| API Gateway          | 8100 |
| User Service         | 8101 |
| Order Service        | 8102 |
| Payment Service      | 8103 |
| Inventory Service    | 8104 |
| Notification Service | 8105 |
| Auth Service         | 8106 |

Failure modes can be injected to validate SentinelOps end-to-end.

---

# Infrastructure

SentinelOps uses:

* PostgreSQL
* Redis
* Kafka
* Prometheus
* Grafana
* OpenTelemetry Collector
* Docker

---

# Technology Stack

### Core

* Python
* SQL
* FastAPI
* Pydantic
* YAML

### Data

* Polars
* PyArrow
* NumPy

### Machine Learning

* scikit-learn
* Isolation Forest
* Logistic Regression
* Statistical anomaly detection

### Graph Intelligence

* NetworkX

### Streaming / Infrastructure

* Kafka
* Redis
* PostgreSQL

### Observability

* OpenTelemetry
* Prometheus
* Grafana

### Platform

* Docker

### AI / RAG

* TF-IDF retrieval
* Evidence-grounded agent architecture
* LLM provider abstraction
* Multi-agent investigation

### Testing / Quality

* Pytest
* Ruff
* Compile checks
* Phase-specific preflight certification

---

# Repository Structure

```text
sentinelops-ai/
│
├── configs/
│   ├── anomaly.yaml
│   ├── counterfactual.yaml
│   ├── execution.yaml
│   ├── failure_prediction.yaml
│   ├── features.yaml
│   ├── incident_correlation.yaml
│   ├── incident_priority.yaml
│   ├── investigation.yaml
│   ├── rca.yaml
│   ├── rca_challenger.yaml
│   ├── remediation.yaml
│   └── slo_business_impact.yaml
│
├── data/
│   ├── processed/
│   └── telemetry/
│
├── docs/
│   └── runbooks/
│
├── infra/
│
├── models/
│   ├── anomaly/
│   └── prediction/
│
├── scripts/
│
├── services/
│
├── src/
│   └── sentinelops/
│       ├── anomaly/
│       ├── counterfactual/
│       ├── execution/
│       ├── features/
│       ├── graph/
│       ├── impact/
│       ├── incidents/
│       ├── investigation/
│       ├── rca/
│       ├── remediation/
│       └── telemetry/
│
├── tests/
│
├── README.md
├── pyproject.toml
└── requirements-lock.txt
```

---

# Development Phases

| Phase | Capability                                     |
| ----- | ---------------------------------------------- |
| 0     | Architecture, prerequisites and infrastructure |
| 1     | Platform foundation                            |
| 2     | Distributed-system test environment            |
| 3     | Telemetry and observability                    |
| 4     | Feature platform                               |
| 5     | Anomaly detection                              |
| 6     | Service dependency graph                       |
| 7     | Incident correlation                           |
| 8     | Evidence-based RCA                             |
| 9     | Causal RCA + challenger                        |
| 10    | Failure prediction                             |
| 11    | Counterfactual simulation                      |
| 12    | SLO and business-impact intelligence           |
| 13    | Remediation planner + SentinelGuard            |
| 14    | Controlled remediation + recovery verification |
| 15    | RAG + multi-agent investigation platform       |

---

# Safety Architecture

```text
No evidence
    ↓
No RCA claim

No challenger
    ↓
No remediation progression

No positive counterfactual
    ↓
No remediation recommendation

No SentinelGuard approval
    ↓
No execution request

No rollback
    ↓
No execution

No human approval
    ↓
No execution

Failed recovery
    ↓
Rollback

LLM / Agent
    ↓
No direct execution
No SentinelGuard bypass
No human-approval bypass
```

---

# Testing Philosophy

Each major SentinelOps phase follows:

```text
Prerequisite
   ↓
Contract
   ↓
Implementation
   ↓
Smoke Test
   ↓
Validation
   ↓
Integration Test
   ↓
Preflight
   ↓
Regression
   ↓
Certification
```

This prevents an implementation from being treated as complete merely because the code exists.

---

# Current Status

SentinelOps AI has repository implementation evidence through all **15 phases**.

Git release tag:

```text
sentinelops-v1.0.0
```

The current system demonstrates a local, evidence-grounded path from generated/development telemetry through investigation and human-controlled sandbox remediation. It does not establish production connectivity or production performance.

---

# Future Work

Potential extensions include:

* Production-scale telemetry datasets
* Kafka streaming feature computation
* Graph Neural Networks
* Temporal Graph Networks
* Advanced forecasting models
* Learned causal discovery
* Bayesian RCA
* Kubernetes-native remediation adapters
* Service-mesh traffic shifting
* Real deployment rollback controllers
* Vector-database RAG
* Mistral/Cohere/OpenAI provider adapters
* React operations console
* Cloud deployment
* MLflow model registry
* Airflow orchestration
* Continuous drift monitoring
* Reinforcement learning for remediation policy evaluation

These additions would extend the platform without weakening its existing safety contracts.

---

## Author

**Abhay Kumar**

Artificial Intelligence & Machine Learning
Data Science / Machine Learning / AI Engineering
