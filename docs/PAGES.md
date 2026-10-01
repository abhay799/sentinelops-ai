# Static Pages Packaging

GitHub Pages remains the **offline demo-data version**. The public frontend is hosted on [Vercel](https://sentinelops-ai-weld.vercel.app), with the precomputed Phase 15 artifact API on [Railway](https://sentinelops-ai-backend-production.up.railway.app). See [public deployment](DEPLOYMENT.md) for the component scope, endpoints, `VITE_API_BASE`, CORS origin setting, and minimal backend dependencies. Neither public hosting nor the Pages demo establishes production infrastructure or telemetry connectivity.

The repository includes **PAGES-READY** static packaging. It is deployment configuration, not evidence that GitHub Pages is currently enabled or live.

- The portfolio build is assembled at the Pages root (`/`).
- The Control Center build is assembled at `/control-center/`.
- The Control Center uses deterministic demo data by default. The local API remains optional for local development and is not deployed to Pages.
- Control Center navigation uses hash routes in the static build, so a Pages refresh does not require a server-side SPA fallback.
- Screenshot frames remain **PENDING CAPTURE** until real rendered UI media is reviewed and added according to [the capture guide](media/CAPTURE_GUIDE.md).

The deployment workflow is [`.github/workflows/pages.yml`](../.github/workflows/pages.yml). A repository administrator must enable GitHub Pages with **GitHub Actions** as the source before a workflow run can publish the artifact.

The portfolio URL is `https://abhay799.github.io/sentinelops-ai/`; the offline Control Center URL is `https://abhay799.github.io/sentinelops-ai/control-center/`. Leave `VITE_API_BASE` unset for this Pages build so it uses the offline `demo` provider. The existing Pages workflow does not supply an API URL. The demo retains LOCAL / SYNTHETIC / DETERMINISTIC / NOT CONNECTED labels; it does not deploy the Railway backend or run the ML pipeline.
