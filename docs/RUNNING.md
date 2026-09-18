# Running SentinelOps AI Locally

## 1. Scope

This guide covers repository-backed local components: the deterministic Control Center, the optional Phase 15 Investigation API, Docker Compose local infrastructure, and phase scripts whose required artifacts are present. It does not reproduce production systems: production infrastructure and telemetry are **NOT CONNECTED**, and production performance is **NOT MEASURED**.

The Control Center is the recommended reviewer path. It renders offline deterministic demo scenarios without Docker or the Python API. Generated Phase 4–15 artifacts and model binaries may exist locally, but are Git-ignored and therefore are not durable public evidence.

## 2. Prerequisites

- Python **>=3.14** (`pyproject.toml`).
- `pip` and a virtual environment tool supplied by Python.
- Node.js and npm for `frontend/`; no Node version is constrained by the repository.
- Docker Engine with Docker Compose only for infrastructure/demo services.
- Windows PowerShell, Linux, and macOS can run the Python/Node commands below. The Compose files use Docker networking and local ports.

Python dependencies are declared in `pyproject.toml`; `requirements-lock.txt` is a development lock file. Its editable-path entry is machine-specific, so prefer the project install below for a fresh checkout.

## 3. Repository setup

Start from an existing checkout. This repository does not publish a canonical clone URL, so no clone command is prescribed.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Linux/macOS, activate the same environment with:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Install the frontend dependencies from its package manifest and lock file:

```bash
cd frontend
npm install
```

## 4. Frontend-first quick demo path

From `frontend/`:

```bash
npm run dev
```

Vite has no configured fixed port in `frontend/vite.config.js`; use the local URL printed by Vite. The default provider is the offline deterministic demo provider. This is **LOCAL**, **SYNTHETIC**, and **DETERMINISTIC**; it is not production incident history.

Use the **DEMO SCENARIO** selector to switch among:

- `normal-operation`
- `early-degradation`
- `correlated-multi-signal`
- `competing-rca-hypotheses`
- `adversarial-rca-challenge`
- `sentinelguard-rejection`
- `human-authorization-pending`
- `safe-local-recovery`
- `failed-verification-safe-failure`

Scenario details are in [demo scenarios](demo/SCENARIOS.md). Counterfactual values are **SIMULATED**; scenario values are not benchmark measurements.

## 5. Optional Phase 15 local API

With the Python environment activated, from the repository root:

```powershell
python scripts\run_phase15_api.py
```

The API binds to `127.0.0.1:8200`. Supported endpoints are:

- `GET /live`
- `GET /ready`
- `GET /investigation/latest`
- `GET /capabilities`
- `GET /docs`

`/` is not a documented endpoint and may return 404. The API uses the deterministic grounded implementation and reads local generated investigation artifacts where available. It is not a production service. Start the frontend with its optional local API mode (`?mode=local-api`); if the API cannot be reached, the frontend visibly falls back to deterministic data with **NOT CONNECTED** status.

## 6. Local infrastructure

The Compose files declare an external Docker network named `sentinelops-net`. Create it once if it does not already exist:

```bash
docker network create sentinelops-net
```

Start the repository-supported local stacks from the repository root:

```bash
docker compose -f infra/docker-compose.core.yml up -d
docker compose -f infra/docker-compose.kafka.yml up -d
docker compose -f infra/docker-compose.observability.yml up -d
docker compose -f infra/docker-compose.phase2.yml up -d
```

These files provide PostgreSQL (`5432`), Redis (`6379`), Kafka (`9092`), Prometheus (`9090`), Grafana (`3000`), OpenTelemetry Collector (`4317`/`4318`), and seven demo services (`8100`–`8106`). They are local development infrastructure; no Kubernetes or Helm assets exist.

## 7. Backend and pipeline execution

Repository scripts are phase-oriented and commonly consume artifacts from earlier phases. The following are real entry points, but are not a promise that a fresh public checkout can regenerate every historical result:

- Feature work: `scripts/phase4_capture.py`, `scripts/build_phase4_features.py`, `scripts/build_phase4_temporal_features.py`.
- Anomaly work: `scripts/train_phase5_anomaly.py`, `scripts/evaluate_phase5_anomaly.py`.
- Graph/incidents/RCA: `scripts/build_phase6_graph.py` through `scripts/build_phase9_causal_disposition.py`.
- Prediction/counterfactual/priority: `scripts/train_phase10_predictor.py` through `scripts/build_phase12_incident_priority.py`.
- Remediation/execution: `scripts/build_phase13_remediation.py`, `scripts/build_phase14_execution_requests.py`, `scripts/phase14_approve.py`, `scripts/execute_phase14_request.py`.
- Investigation: `scripts/build_phase15_investigation.py`, `scripts/build_phase15_final.py`.

Use the matching existing preflight scripts (`phase1`–`phase14`, where present) only after their prerequisites/artifacts exist. `scripts/phase15_preflight.py` does not exist, so no replacement command is provided.

## 8. Testing

From the repository root, Python tests use the configuration in `pyproject.toml`:

```bash
python -m pytest
```

From `frontend/`, run the existing Node built-in tests, build, and lint:

```bash
node --test tests/*.test.mjs
npm run build
npm run lint
```

These commands validate current source/contracts. They do not recreate all historical phase certification because generated inputs/artifacts are ignored. `tests/test_phase15_final.py` is absent.

## 9. Evidence reproduction

Read [benchmarks and evidence](evidence/BENCHMARKS_AND_EVIDENCE.md) and the [evidence manifest](evidence/EVIDENCE_MANIFEST.json) before making public claims. Phase 10 precision `0.2778`, recall `1.0000`, F1 `0.4348`, and average lead events `1.8` are historical **MEASURED DEVELOPMENT DATA** in a **SYNTHETIC / DEMO CONTEXT**, not production-calibrated results.

Tracked source, tests, configurations, and documentation can be inspected from a checkout. Local `data/processed/` files and model binaries can support historical development work only when already present; they are Git-ignored and not durable public artifacts.

## 10. Local sandbox remediation

The execution boundary is **LOCAL SANDBOX**. Human authorization remains required. Only `rollback` is configured as a sandbox execution adapter (`POST /failure-mode/reset`). `traffic_shift` and `restart` are planning/allowlist concepts only; do not treat them as executable adapters.

Do not bypass SentinelGuard, human approval, rollback availability, target validation, final gating, or recovery verification. This guide provides no bypass instructions.

## 11. Known reproducibility gaps

- `scripts/phase15_preflight.py` is absent.
- `tests/test_phase15_final.py` is absent.
- Generated processed data and model binaries are ignored, local-only evidence.
- `pyproject.toml` is `0.1.0`; Git also has the `sentinelops-v1.0.0` tag.
- Production infrastructure/telemetry are **NOT CONNECTED**; production benchmarks are **NOT MEASURED**.
- Kubernetes and Helm assets are absent.

## 12. Shutdown and cleanup

Stop the local stacks without deleting volumes:

```bash
docker compose -f infra/docker-compose.phase2.yml down
docker compose -f infra/docker-compose.observability.yml down
docker compose -f infra/docker-compose.kafka.yml down
docker compose -f infra/docker-compose.core.yml down
```

Stop the API or Vite development process with `Ctrl+C`. This guide intentionally does not recommend volume deletion or other destructive cleanup by default.
