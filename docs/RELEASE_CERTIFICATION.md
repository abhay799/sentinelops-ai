# SentinelOps AI Internal Project Release Certification

**Decision: PORTFOLIO RELEASE READY**

This is an **INTERNAL PROJECT RELEASE CERTIFICATION** for portfolio/public presentation. It is not external, industry, regulatory, or security certification.

## Audit record

- Audited commit: `9481e39497d6fb30422df20000533cdb4e7bef7b`.
- Audit date: 2026-09-19 (local audit environment).
- Scope: tracked documentation, Control Center, deterministic scenarios, evidence manifest, portfolio site, media package, CI configuration, and static Pages packaging.

## Validated components

- Control Center: 15 views, nine deterministic scenarios, demo provider, and optional local-API fallback. Node tests, lint, and static build passed in the audit environment.
- Scenario safety: Guard rejection and pending human authorization cannot execute; only `safe-local-recovery` records successful configured rollback execution. `traffic_shift` and `restart` are not validated adapters.
- Safety boundary: LOCAL SANDBOX only; `rollback` is the configured adapter. Planner recommendation, SentinelGuard approval, human authorization, and execution remain separate. Agents cannot independently confirm RCA, execute, or bypass SentinelGuard/human approval.
- Investigation: `DeterministicGroundedProvider`; `/live`, `/ready`, `/investigation/latest`, `/capabilities`, and FastAPI `/docs` are repository-backed endpoints. `/` is not a documented endpoint.
- Evidence: the manifest parsed with 22 ordered entries and normal source/test/validation paths present. Phase 10 metrics remain MEASURED DEVELOPMENT DATA in SYNTHETIC / DEMO CONTEXT and are NOT PRODUCTION-CALIBRATED.
- Portfolio: clean lint and static Vite build. The page uses explicit pending screenshot placeholders and qualified evidence numbers.
- Media: no captured images are claimed; all nine capture targets remain PENDING CAPTURE with a capture guide and demo script.
- CI: frontend-and-evidence validation covers frontend dependency installation, Node tests, lint, build, and evidence-manifest parsing only. It does not claim Python CI coverage.

## Nonblocking limitations

- Production infrastructure and telemetry are NOT CONNECTED; production benchmarks are NOT MEASURED.
- Counterfactuals are SIMULATED; demo/scenario telemetry is SYNTHETIC and DETERMINISTIC.
- `scripts/phase15_preflight.py` and `tests/test_phase15_final.py` are absent.
- Python tests were not run in the audit environment because `polars`, `numpy`, and `sqlalchemy` were unavailable; this is a collection-environment limitation, not a passing Python-test claim.
- Generated processed artifacts and model binaries are local/Git-ignored, not durable public evidence.
- `pyproject.toml` is version `0.1.0`, while Git includes `sentinelops-v1.0.0`; this is a documented nonblocking identity mismatch for a portfolio release.
- Docker Compose uses explicit local development credentials; they are not production credentials and must not be reused outside local development.
- Real screenshot captures are pending and are not release-blocking.

## Static deployment readiness

The repository is configured to assemble a static artifact with the portfolio at `/` and the deterministic Control Center at `/control-center/`. This configuration does not deploy Python/FastAPI services and does not imply that Pages is enabled or live.
