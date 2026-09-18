# Incident Intelligence Lifecycle

## Purpose

This diagram shows how the implemented intelligence stages refine local telemetry into prioritization inputs while preserving RCA uncertainty.

```mermaid
flowchart TD
    telemetry[Telemetry artifacts]
    features[Point in time safe features]
    anomalies[Anomaly signals]
    graph[Dependency graph relationships]
    correlation[Incident correlation]
    hypotheses[RCA candidate hypotheses]
    challenge[Challenger checks contradictions and alternatives]
    disposition[Causal disposition]
    prediction[Failure prediction]
    simulation[Counterfactual analysis]
    priority[Priority intelligence]

    telemetry --> features --> anomalies --> graph --> correlation --> hypotheses
    hypotheses --> challenge --> disposition --> prediction --> simulation --> priority

    unconfirmed[Candidate remains unconfirmed]
    hypotheses -. not a root cause claim .-> unconfirmed
    challenge -. supported weakened rejected or inconclusive .-> unconfirmed
```

## Explanation

Feature construction is point-in-time aware, after which anomaly detectors and graph relationships contribute to incident correlation. RCA ranks candidate services using available evidence. The challenger and causal disposition stages can assess consistency and contradictions, but a candidate remains a hypothesis even if supported.

Prediction, counterfactual analysis, and priority intelligence are downstream decision-support inputs. They do not independently confirm RCA and do not authorize remediation.

## Provenance and runtime boundary

- **DEVELOPMENT/SYNTHETIC DATA:** Local/generated artifacts back the current evaluation path.
- **SIMULATED:** Counterfactual analysis estimates outcomes rather than exercising infrastructure.
- **NOT CONNECTED:** This lifecycle does not consume production telemetry in the current repository.
