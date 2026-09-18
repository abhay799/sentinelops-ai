# SentinelOps AI

Reliability intelligence and failure-prevention engineering for distributed-system demos. SentinelOps turns local, generated evidence into detection, investigation, safety-gated planning, and controlled local sandbox recovery decisions.

> **Current boundary:** LOCAL, SYNTHETIC, DETERMINISTIC, and NOT CONNECTED to production infrastructure. Counterfactuals are SIMULATED; production performance is NOT MEASURED.

## Reliability lifecycle

`Sense → Detect → Predict → Correlate → Diagnose → Challenge RCA → Simulate → Prioritize → Plan → Guard → Human Authorization → Controlled Execution → Verify → Investigate`

## Safety invariant

```text
NO REMEDIATION WITHOUT
EVIDENCE + CONFIDENCE + SAFETY + AUTHORIZATION + ROLLBACK + VERIFICATION
```

RCA output remains a hypothesis. Agents cannot independently confirm RCA, execute remediation, bypass SentinelGuard, or bypass human approval. The execution boundary is **LOCAL SANDBOX**: `rollback` is the configured adapter; `traffic_shift` and `restart` are planning/allowlist concepts only.

## Quick demo

The committed React Control Center works offline with deterministic demo data:

```bash
cd frontend
npm install
npm run dev
```

Vite prints the local URL. See [running locally](docs/RUNNING.md) for setup, API, infrastructure, tests, and shutdown instructions.

## Control Center and scenarios

The Control Center presents 15 reliability/SRE views through a provider boundary that supports deterministic `demo` data and optional `local-api` fallback. It is a local demonstration UI, not a live operations console.

Nine deterministic scenarios demonstrate cautious operation, RCA uncertainty, Guard rejection, pending human authorization, local recovery, and safe failure. See [scenario documentation](docs/demo/SCENARIOS.md).

## Architecture, evidence, and validation

- [Project architecture](docs/architecture/PROJECT_ARCHITECTURE.md) and [phase index](docs/architecture/PHASE_INDEX.md)
- [System overview](docs/architecture/SYSTEM_OVERVIEW.md), [execution lifecycle](docs/architecture/EXECUTION_LIFECYCLE.md), and [safety control plane](docs/architecture/SAFETY_CONTROL_PLANE.md)
- [Safety invariants](docs/architecture/SAFETY_INVARIANTS.md), [limitations](docs/LIMITATIONS.md), and [validation scope](docs/VALIDATION.md)
- [Benchmarks and evidence](docs/evidence/BENCHMARKS_AND_EVIDENCE.md) and [evidence manifest](docs/evidence/EVIDENCE_MANIFEST.json)
- [Static Pages packaging](docs/PAGES.md) and [internal release certification](docs/RELEASE_CERTIFICATION.md)

Historical Phase 10 development metrics are measured on synthetic/development data, not production-calibrated. Git tags are historical internal certification markers, not external certification.

## Screenshot / demo media

No screenshots or demo media are committed yet. This section is intentionally a placeholder until reproducible assets are added.

## Repository structure

```text
configs/     Runtime and safety configuration
docs/        Architecture, evidence, scenarios, and running guides
frontend/    React/Vite local Control Center
infra/       Docker Compose local infrastructure
monitoring/  Prometheus and OpenTelemetry configuration
scripts/     Phase build, preflight, and local API entry points
services/    Seven local demo services
src/         SentinelOps Python implementation
tests/       Python contract and phase tests
```

## Status and limitations

Repository implementation evidence covers Phases 0–15. Generated `data/processed/` artifacts and model binaries are local/Git-ignored and are not durable public evidence. Production infrastructure and telemetry are NOT CONNECTED; production benchmarks are NOT MEASURED. The package version is `0.1.0`, while Git contains the `sentinelops-v1.0.0` tag; this mismatch is documented, not hidden.

No Kubernetes or Helm assets are present. `scripts/phase15_preflight.py` and `tests/test_phase15_final.py` are absent; existing Phase 15 evidence is documented in the validation and evidence guides.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). No license file has been selected for this repository.
