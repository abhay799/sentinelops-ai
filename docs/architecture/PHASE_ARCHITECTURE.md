# Phase Architecture

## Purpose

This phase map groups the implemented Phase 0 through Phase 15 responsibilities. It is an implementation/provenance map, not a production deployment diagram.

```mermaid
flowchart TD
    subgraph foundation[Foundation phases 0 to 3]
        p0[Phase 0 architecture prerequisites and infrastructure definitions]
        p1[Phase 1 platform foundation]
        p2[Phase 2 distributed system test environment]
        p3[Phase 3 telemetry and observability]
        p0 --> p1 --> p2 --> p3
    end

    subgraph intelligence[Intelligence phases 4 to 9]
        p4[Phase 4 feature platform]
        p5[Phase 5 anomaly detection]
        p6[Phase 6 service dependency graph]
        p7[Phase 7 incident correlation]
        p8[Phase 8 evidence based RCA hypotheses]
        p9[Phase 9 causal RCA and challenger]
        p4 --> p5 --> p6 --> p7 --> p8 --> p9
    end

    subgraph decision[Prediction and decision support phases 10 to 12]
        p10[Phase 10 failure prediction]
        p11[Phase 11 counterfactual simulation]
        p12[Phase 12 SLO and business impact intelligence]
        p10 --> p11 --> p12
    end

    subgraph remediation[Safe remediation phases 13 to 14]
        p13[Phase 13 remediation planner and SentinelGuard]
        p14[Phase 14 controlled local sandbox remediation and recovery verification]
        p13 --> p14
    end

    subgraph investigation[Grounded investigation phase 15]
        p15[Phase 15 local RAG deterministic provider and constrained multi-agent investigation]
    end

    p3 --> p4
    p9 --> p10
    p12 --> p13
    p14 --> p15
```

## Explanation

The first four phases establish the local environment and telemetry foundations. Phases 4–9 turn telemetry artifacts into features, anomalies, graph/incident context, RCA hypotheses, and challenged causal dispositions. Phases 10–12 provide development-data prediction, simulated counterfactual analysis, and priority intelligence. Phases 13–14 constrain planning and local sandbox execution; Phase 15 investigates accumulated evidence without granting agent authority.

## Provenance annotations

| Group | Status |
| --- | --- |
| Phases 0–9 | **IMPLEMENTED** locally; telemetry and associated evaluation artifacts are development-oriented. |
| Phase 10 | **IMPLEMENTED** with **DEVELOPMENT/SYNTHETIC DATA** measurements, not production performance. |
| Phase 11 | **IMPLEMENTED** and **SIMULATED**; no counterfactual execution authority. |
| Phase 14 | **IMPLEMENTED** as **LOCAL** sandbox execution with rollback as the configured adapter. |
| Phase 15 | **IMPLEMENTED** and **DETERMINISTIC** with `DeterministicGroundedProvider`. |
| Entire map | **NOT CONNECTED** to production infrastructure. |
