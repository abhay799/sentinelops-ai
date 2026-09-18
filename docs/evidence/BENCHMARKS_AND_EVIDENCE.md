# Benchmarks and Evidence

## Evidence categories

Implementation evidence is source/configuration; test evidence is executable test coverage; preflight/validation evidence is phase script coverage; local generated evidence is present locally but Git-ignored; historical internal certification is the Phase tags and must not be read as external, regulatory, or industry certification. Public productization evidence is the tracked documentation and source that can be inspected without local generated artifacts.

## Historical development measurement

Phase 10 local `data/processed/prediction/evaluation_v1.json` records a temporal split of 39 train / 18 test rows and supervised precision **0.2778**, recall **1.0000**, F1 **0.4348**, and average lead events **1.8**. Classification: **MEASURED ON DEVELOPMENT DATA**, **SYNTHETIC / DEMO CONTEXT**, **NOT PRODUCTION-CALIBRATED**. The underlying processed data is Git-ignored, so this is local historical evidence, not a durable public benchmark artifact.

## Local generated evidence

Local Phase 4–15 artifacts, including feature, anomaly, graph, incident, RCA, prediction, counterfactual, remediation, execution, recovery, and investigation files, exist under `data/processed/`; model binaries exist under `models/`. They are **LOCAL HISTORICAL EVIDENCE**, **GENERATED**, and **NOT DURABLE PUBLIC EVIDENCE** because those paths are ignored. Phase 14 local execution/recovery files support historical development validation only. Runtime boundary: **LOCAL SANDBOX**; `rollback` is the configured adapter. `traffic_shift` and `restart` are planning/allowlist concepts, not validated adapters.

## Capability manifest

The machine-readable [manifest](EVIDENCE_MANIFEST.json) contains 22 deterministically ordered entries covering the implemented evidence areas. It records repository-relative implementation, test, validation, artifact, reproducibility, limitation, permitted-claim, and prohibited-claim fields.

## Historical internal certification and gaps

Git tags through `sentinelops-v0-phase15-certified` and `sentinelops-v1.0.0` are **HISTORICAL INTERNAL CERTIFICATION** only. They are not external certification. Known gaps: `scripts/phase15_preflight.py` and `tests/test_phase15_final.py` are absent; `pyproject.toml` is `0.1.0` while the tag is `sentinelops-v1.0.0`.

## UI and scenario evidence

The Control Center and nine scenarios are source/test evidence. Scenario values are **DETERMINISTIC**, **SYNTHETIC**, and **SIMULATED** where stated. They are demonstration inputs, not benchmark measurements or real incident history.

## Not measured

The repository does not provide production latency overhead, throughput, incident-detection accuracy, RCA accuracy, false-positive rate, calibrated prediction probability, MTTR improvement, remediation success rate, scale limits, availability, external LLM quality benchmark, Kubernetes remediation performance, production telemetry coverage, or production execution evidence.
