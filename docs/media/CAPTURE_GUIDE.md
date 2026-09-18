# Control Center Capture Guide

No screenshot assets are committed in this repository. This guide is the reproducible procedure for capturing **real rendered** Control Center screens; do not create illustrations, generated images, or manually constructed browser captures in their place.

## Preconditions

Use the deterministic offline demo provider. From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite. Select the named **DEMO SCENARIO** in the Control Center before each capture. Use a desktop viewport of **1440 × 1024** and retain the visible `LOCAL LAB`, connection/provenance, and safety labels. Capture the browser viewport only after the view has finished rendering.

Store actual reviewed captures in `ui/portfolio/public/media/` using the filenames below. Update the corresponding manifest status only after the file exists and was captured from the rendered Control Center.

| Filename | Scenario | Route | Required visible content |
|---|---|---|---|
| `mission-control.png` | `safe-local-recovery` | `/` | Lifecycle, local boundary, evidence, recovery state |
| `service-health.png` | `correlated-multi-signal` | `/services` | Service health and local/synthetic provenance |
| `rca-intelligence.png` | `competing-rca-hypotheses` | `/rca` | Ranked candidate hypotheses; no confirmed-RCA language |
| `rca-challenger.png` | `adversarial-rca-challenge` | `/challenger` | Challenger outcome and contradictory evidence |
| `sentinelguard.png` | `sentinelguard-rejection` | `/guard` | Rejection/fail-closed Guard result; no execution |
| `safe-local-recovery.png` | `safe-local-recovery` | `/recovery` | Human approval, configured `rollback`, verification, LOCAL LAB |
| `investigation.png` | `competing-rca-hypotheses` | `/investigation` | Grounded investigation and candidate-RCA boundary |
| `system-status.png` | `normal-operation` | `/system` | Stable deterministic system status with provenance |
| `portfolio-home.png` | Not applicable | `ui/portfolio/` home | Portfolio page, current boundaries, and no false media state |

## Review before adding an asset

- Confirm the source is a real rendered browser screen, not generated or drawn media.
- Confirm it contains no local Windows path, secret, or browser chrome revealing unrelated data.
- Confirm production is not implied and no value is labelled LIVE.
- Confirm `traffic_shift` and `restart` are not represented as validated execution adapters.
- Confirm `rollback` is shown only as the configured **LOCAL SANDBOX** adapter.
