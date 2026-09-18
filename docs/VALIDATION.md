# Validation Scope and Evidence

## What is validated in this repository

The repository contains phase-specific scripts and tests through Phase 14 and Phase 15 investigation tests. Validation covers module and artifact contracts such as feature construction, anomaly detection, graph intelligence, incident correlation, RCA/challenging, prediction safety, counterfactual safety, priority/impact, remediation/SentinelGuard, local execution gating, and grounded investigation constraints.

Important local execution tests demonstrate that:

- A rollback request with Guard pass, explicit human approval, local target, and configured adapter can pass the final gate.
- A missing human approval blocks execution.
- A non-local target blocks execution.
- `restart` blocks at the sandbox-adapter check despite being on the allowlist.
- Local mock HTTP responses can verify `/live`, `/ready`, and the rollback endpoint.

Phase 15 investigation tests demonstrate that agents do not confirm root cause or obtain execution authority, evidence bundles disable agent execution/confirmation, and the local runbook retriever returns sources.

## What this does not validate

Repository tests and scripts do not establish:

- Production infrastructure connectivity or access control.
- Production telemetry ingestion, coverage, scale, or quality.
- Production failure-prediction precision, recall, lead time, calibration, or business impact.
- Live counterfactual correctness or actual remediation effectiveness.
- Production execution adapters for `traffic_shift` or `restart`.
- A public/release frontend; `frontend/` is a local ignored/untracked directory.

Counterfactual outputs are simulated decision-support results. Failure-prediction metrics in repository examples are development/synthetic measurements, not production performance metrics.

## Current validation gaps

- `scripts/phase15_preflight.py` is absent from the current working tree.
- `tests/test_phase15_final.py` is absent from the current working tree.
- Phase 15 instead contains `scripts/build_phase15_final.py` and `tests/test_phase15_investigation.py`.
- The package metadata version is `0.1.0`, while Git also contains a `sentinelops-v1.0.0` tag; these versions differ.

No conclusion beyond the tests/scripts present in the working tree should be inferred from a tag, artifact name, or README statement alone.

## Validation terminology

| Term | Meaning in this repository |
| --- | --- |
| Validated local sandbox execution | A local, adapter-backed runtime path exercised with local/mock HTTP behavior and recovery probes. |
| Simulated | A modelled counterfactual result, not an action on infrastructure. |
| Synthetic/development measurement | Evaluation derived from the repository’s generated or development data, not a production SLO or production model-performance measurement. |
| Implemented | Source/config/script/test evidence exists in this repository. It does not alone imply deployment, connectivity, or operational approval. |
