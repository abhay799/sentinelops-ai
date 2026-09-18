# SentinelOps AI Phase Index

## Status convention

All entries below describe implementation evidence in the current repository, not production deployment or production performance. No Phase 16 or later capability is implemented or claimed.

| Phase | Implemented capability | Repository evidence | Claim boundary |
| ---: | --- | --- | --- |
| 0 | Architecture, prerequisites, and infrastructure definitions | Docker Compose, monitoring, configuration, and preflight artifacts | Local development infrastructure, not connected production infrastructure. |
| 1 | Platform foundation | Application/configuration foundations, contracts, smoke/preflight tests | Development foundation only. |
| 2 | Distributed-system test environment | Seven local services and Phase 2 Compose configuration | Local test environment. |
| 3 | Telemetry and observability | Telemetry schema/sink, collector and Prometheus configuration, Phase 3 preflight | Telemetry configuration and generated/local signals are not production telemetry. |
| 4 | Feature platform | Feature and temporal builders, Phase 4 scripts/tests | Artifact-based development pipeline. |
| 5 | Anomaly detection | Statistical, EWMA, Isolation Forest, and ensemble code with training/evaluation scripts | Development/synthetic evaluation only. |
| 6 | Service dependency graph | Service graph and graph-risk modules with tests/preflight | Local topology/model evidence. |
| 7 | Incident correlation | Correlator and incident-intelligence modules with tests/preflight | Local artifact processing. |
| 8 | Evidence-based RCA | RCA engine, validation, summaries, tests/preflight | Ranked hypotheses; no independent root-cause confirmation. |
| 9 | Causal RCA and challenger | Causal disposition and challenger modules with tests/preflight | Challenger can support, weaken, reject, or leave candidates inconclusive; it does not confirm RCA. |
| 10 | Failure prediction | Early warning, Logistic Regression training/evaluation, tests/preflight | Development/synthetic metrics; not production performance. |
| 11 | Counterfactual simulation | Counterfactual engine, ranking, validation, scripts/tests/preflight | Simulated decision-support outputs; no execution authority. |
| 12 | SLO and business-impact intelligence | Impact/prioritization code, scripts/tests/preflight | Configured/local input based; no live business-impact claim. |
| 13 | Remediation planner and SentinelGuard | Planner, SentinelGuard, validation, audit/preflight tests | Plans and guard decisions are fail-closed recommendations pending human approval. |
| 14 | Controlled remediation and recovery verification | Execution request/gate/runtime, approval and execution scripts, Phase 14 tests/preflight | Local sandbox only. Rollback is the configured adapter; `traffic_shift`/`restart` are not validated adapters. |
| 15 | RAG and grounded multi-agent investigation | Evidence, retrieval, provider, agents, orchestrator, API, build script, investigation tests | Deterministic local provider; agents cannot confirm RCA, execute remediation, or bypass safety/human controls. |

## Certification and repository gaps

Git includes phase tags through `sentinelops-v0-phase15-certified` and the `sentinelops-v1.0.0` tag. The latter points to the Phase 15 certification commit, while `pyproject.toml` declares version `0.1.0`; this mismatch is a provenance/documentation gap.

The working tree does not contain `scripts/phase15_preflight.py` or `tests/test_phase15_final.py`. Current Phase 15 evidence instead includes `scripts/build_phase15_final.py` and `tests/test_phase15_investigation.py`. This index does not infer missing validation assets from tag names or commit messages.

`frontend/` is present locally but ignored/untracked. It is not listed as a release/public Phase 15 implementation artifact.
