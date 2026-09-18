# System Overview

## Purpose

This diagram shows the implemented SentinelOps AI path from the local distributed demo environment through reliability intelligence, safety-controlled local execution, and grounded investigation.

```mermaid
flowchart TD
    services[Distributed demo services]
    signals[Metrics logs traces and change events]
    telemetry[Telemetry handling]
    features[Point in time feature platform]
    anomaly[Anomaly detection]
    graph[Service dependency graph]
    incidents[Incident correlation]
    rca[Evidence based RCA hypotheses]
    challenger[RCA challenger]
    causal[Causal disposition]
    prediction[Failure prediction]
    counterfactual[Counterfactual simulation]
    impact[SLO and business impact intelligence]
    planner[Remediation planner]
    guard[SentinelGuard]
    approval[Human approval]
    gate[Final execution gate]
    sandbox[Controlled local sandbox execution]
    verify[Recovery verification]
    evidence[Evidence bundle]
    rag[Local RAG retrieval]
    agents[Grounded multi-agent investigation]
    api[Investigation API]

    services --> signals --> telemetry --> features --> anomaly --> graph --> incidents
    incidents --> rca --> challenger --> causal --> prediction --> counterfactual --> impact --> planner
    planner --> guard --> approval --> gate --> sandbox --> verify --> evidence --> rag --> agents --> api

    kafka[Kafka]
    postgres[PostgreSQL]
    redis[Redis]
    prometheus[Prometheus]
    otel[OpenTelemetry Collector]

    services -. local telemetry .-> otel
    services -. metrics .-> prometheus
    telemetry -. configured pipeline .-> kafka
    services -. local dependencies .-> postgres
    services -. local dependencies .-> redis
```

## Explanation

The repository defines seven local demo services, telemetry schemas and capture utilities, and a staged intelligence pipeline. RCA creates ranked hypotheses, and the challenger/causal stages assess those hypotheses; neither represents an automatic root-cause confirmation. Counterfactual outputs and priority intelligence inform a remediation plan, but the plan must pass SentinelGuard, explicit human approval, and the final execution gate before any sandbox action can occur.

After recovery verification, Phase 15 combines artifact evidence with local runbooks and deterministic retrieval for investigation reporting. The infrastructure nodes represent repository-supported local Compose/configuration components, not production connections.

## Provenance and runtime boundary

- **LOCAL:** Distributed services, infrastructure URLs, execution, and recovery checks are local development/sandbox artifacts.
- **SIMULATED:** Counterfactual simulation is decision support only.
- **DEVELOPMENT/SYNTHETIC DATA:** Prediction and telemetry evidence is not production telemetry or production performance.
- **DETERMINISTIC:** Phase 15 uses `DeterministicGroundedProvider` and local TF-IDF retrieval.
- **NOT CONNECTED:** Production infrastructure is not connected.
