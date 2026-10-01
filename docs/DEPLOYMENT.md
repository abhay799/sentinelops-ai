# Public deployment and offline demo

The primary [Live demo](https://sentinelops-ai-weld.vercel.app) is the Vercel Control Center. Its companion [Railway backend](https://sentinelops-ai-backend-production.up.railway.app) serves precomputed investigation artifacts. GitHub Pages remains the [offline demo-data version](https://abhay799.github.io/sentinelops-ai/control-center/), with the [portfolio](https://abhay799.github.io/sentinelops-ai/) at the site root.

Public web hosting does not establish production infrastructure or telemetry integration. LOCAL / SYNTHETIC / DETERMINISTIC / NOT CONNECTED still describe the evidence and operational boundary. Counterfactuals are SIMULATED; production performance is NOT MEASURED.

## Component scope

| Component | Host | What it runs | What it does NOT run |
| --- | --- | --- | --- |
| Frontend | Vercel — `https://sentinelops-ai-weld.vercel.app` | React/Vite Control Center, deterministic scenarios, and an optional API capabilities probe | FastAPI, infrastructure services, the ML pipeline, live production telemetry ingestion, or remediation execution |
| Backend | Railway — `https://sentinelops-ai-backend-production.up.railway.app` | FastAPI reading and serving precomputed Phase 15 investigation JSON | Kafka, PostgreSQL, Redis, Prometheus, the ML pipeline, new investigations on request, or remediation execution |
| Offline demo and portfolio | GitHub Pages — `https://abhay799.github.io/sentinelops-ai/` | Static portfolio and Control Center at `control-center/` using the offline `demo` provider | The Railway API in offline mode, a backend server, infrastructure services, or pipeline execution |

## What the public backend serves

The public backend serves **precomputed Phase 15 investigation artifacts via FastAPI**. It does **not** run Kafka, PostgreSQL, Redis, Prometheus, or the ML pipeline.

[Dockerfile.backend](../Dockerfile.backend) copies the tracked `deploy_assets/final_investigation_v1.json` into `data/processed/investigation/final_investigation_v1.json` in the image. [The Investigation API](../src/sentinelops/investigation/api.py) reads that report. Requests do not regenerate telemetry, train models, run retrieval/agent orchestration, or execute remediation. Replacing the report in the source/build and redeploying updates the bundled artifact; this is not a live incident stream.

| Endpoint | Public URL | Meaning |
| --- | --- | --- |
| `/live` | [GET /live](https://sentinelops-ai-backend-production.up.railway.app/live) | The API process responds; it is not a health check of Kafka, PostgreSQL, or Redis |
| `/ready` | [GET /ready](https://sentinelops-ai-backend-production.up.railway.app/ready) | Reports whether the investigation artifact file exists; it does not check infrastructure or pipeline health |
| `/capabilities` | [GET /capabilities](https://sentinelops-ai-backend-production.up.railway.app/capabilities) | Describes the investigation interface and disabled agent execution, RCA confirmation, and approval/Guard bypass authority; advertised capabilities do not mean the pipeline runs on request |
| `/investigation/latest` | [GET /investigation/latest](https://sentinelops-ai-backend-production.up.railway.app/investigation/latest) | Returns the precomputed report; returns HTTP 503 if the artifact is absent |

`/ready` returns HTTP 200 with a `ready` or `not_ready` status value, so check the response body rather than treating HTTP 200 alone as artifact readiness. `/` is not a documented API endpoint.

## Frontend API URL and CORS origin

In the Vercel project's production environment variables, set:

```text
VITE_API_BASE=https://sentinelops-ai-backend-production.up.railway.app
```

Use the base URL without a trailing slash; the provider appends `/capabilities`. Vite embeds this value at build time, so rebuild/redeploy the frontend after changing it.

The current frontend selects its `local-api` provider when this variable is set, unless `?mode=demo` explicitly selects offline mode. The provider probes `/capabilities`; it does not currently load `/investigation/latest` into the views. A successful probe shows **API AVAILABLE**, while the UI scenario remains deterministic and synthetic. If the probe fails, the UI falls back to demo data with **NOT CONNECTED** status. API availability is distinct from production telemetry connectivity.

The backend's CORS origin setting is the `allow_origins` list in `CORSMiddleware` inside [src/sentinelops/investigation/api.py](../src/sentinelops/investigation/api.py). Its existing allowed origin is:

```text
https://sentinelops-ai-weld.vercel.app
```

This is a code-configured allowlist, not an environment variable. A different frontend domain or preview origin is not covered by that entry. The Pages offline version does not need access to Railway.

## Minimal deployment dependencies

[requirements-deploy.txt](../requirements-deploy.txt) is **intentionally minimal**: it pins FastAPI and Uvicorn for the isolated artifact-serving API. It does not install the complete Python intelligence/pipeline environment or start infrastructure services. Use the project development install in [RUNNING.md](RUNNING.md) for local Python tests and pipeline development; the two installation profiles serve different scopes.

## Idle requests and limitations

The first request after idle may be slow while the hosted backend wakes or starts. Allow time for the response and retry if needed; a delay or UI fallback is not a production performance measurement. No cold-start timing or availability guarantee is claimed here.

The deployment does not expand execution authority. Agents still cannot independently confirm RCA, execute remediation, bypass SentinelGuard, or bypass human approval. The configured execution adapter described by the repository remains LOCAL SANDBOX `rollback`; it is not exposed as a public remediation service. `traffic_shift` and `restart` remain planning/allowlist concepts, not validated execution adapters.

See [LIMITATIONS.md](LIMITATIONS.md) and [VALIDATION.md](VALIDATION.md) for the unchanged claim boundaries, missing Phase 15 validation files, ignored generated artifacts, and development-only evidence. See [PAGES.md](PAGES.md) for the static offline packaging and GitHub Pages source setting.
