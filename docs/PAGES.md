# Static Pages Packaging

The repository includes **PAGES-READY** static packaging. It is deployment configuration, not evidence that GitHub Pages is currently enabled or live.

- The portfolio build is assembled at the Pages root (`/`).
- The Control Center build is assembled at `/control-center/`.
- The Control Center uses deterministic demo data by default. The local API remains optional for local development and is not deployed to Pages.
- Control Center navigation uses hash routes in the static build, so a Pages refresh does not require a server-side SPA fallback.
- Screenshot frames remain **PENDING CAPTURE** until real rendered UI media is reviewed and added according to [the capture guide](media/CAPTURE_GUIDE.md).

The deployment workflow is [`.github/workflows/pages.yml`](../.github/workflows/pages.yml). A repository administrator must enable GitHub Pages with **GitHub Actions** as the source before a workflow run can publish the artifact.
