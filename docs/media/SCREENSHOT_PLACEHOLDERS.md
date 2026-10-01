# Screenshot placeholders and reproduction steps

All nine records are **PENDING CAPTURE**. No screenshot files are supplied by these records, and no images have been generated or reconstructed. Captures must show real rendered UI with its LOCAL / SYNTHETIC / DETERMINISTIC / NOT CONNECTED boundaries intact.

## Shared setup

From the repository root, start a deterministic static Control Center preview in Windows PowerShell:

```powershell
cd frontend
npm.cmd ci
npm.cmd run build
npm.cmd run preview -- --host 127.0.0.1 --port 4173 --strictPort
```

Leave that terminal running. In a second terminal, again starting from the repository root, start the portfolio preview:

```powershell
cd ui/portfolio
npm.cmd ci
npm.cmd run build
npm.cmd exec -- vite preview --host 127.0.0.1 --port 4174 --strictPort
```

On Linux/macOS, use `npm` instead of `npm.cmd`. `--strictPort` ensures that a busy port produces an error instead of silently changing the capture URL. Stop any earlier preview on these ports before starting this procedure.

In Chrome or Edge, set browser zoom to 100%, open Developer Tools, enable the device toolbar, choose **Responsive**, and set its width to **1440** and height to **1024**. In the toolbar's options menu, show **Device type** and **Device pixel ratio**; choose **Desktop** and **1** respectively. For each record, open the specified URL, select the exact scenario value in **DEMO SCENARIO**, and wait until the loading message disappears and the screen title/scenario title are visible. `?mode=demo` explicitly selects the offline provider even if an API URL was configured for a local build. No Python API or Docker services are required for these UI captures.

Open the Developer Tools command menu (`Ctrl+Shift+P` on Windows/Linux, `Command+Shift+P` on macOS), choose **Capture screenshot**, and save the viewport image using the filename for that record. Capture only the viewport, not browser chrome or a full scrolling page. Retain visible provenance and safety labels. Use the [capture guide](CAPTURE_GUIDE.md) review checklist before adding an image.

Actual reviewed captures belong in `ui/portfolio/public/media/`, matching the existing [media manifest](MEDIA_MANIFEST.md). The placeholder records themselves remain in `docs/media/`. Change manifest status only after an actual reviewed file exists; a successful screenshot command does not validate a backend action or production connection.

## Mission Control

**PENDING CAPTURE — `mission-control.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/` and choose `safe-local-recovery` in **DEMO SCENARIO**.
2. Confirm **Reliability Mission Control**, **Safe local recovery**, the lifecycle, and visible LOCAL LAB / NOT CONNECTED labels. Follow the shared viewport capture steps and save as `mission-control.png`.

## Service Health

**PENDING CAPTURE — `service-health.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/services` and choose `correlated-multi-signal`.
2. Confirm **Service Health**, the selected scenario, service cards, and visible LOCAL/SYNTHETIC provenance. Capture as `service-health.png`.

## RCA Intelligence

**PENDING CAPTURE — `rca-intelligence.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/rca` and choose `competing-rca-hypotheses`.
2. Confirm **RCA Intelligence**, the leading candidate, evidence, and the statement that the candidate remains unconfirmed. Capture as `rca-intelligence.png`; do not describe the image as independently confirmed RCA.

## RCA Challenger

**PENDING CAPTURE — `rca-challenger.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/challenger` and choose `adversarial-rca-challenge`.
2. Confirm **RCA Challenger**, the displayed contradictory-evidence/alternative-candidate checks, and **Supported is not confirmed root cause**. Capture the displayed values unchanged as `rca-challenger.png`; do not infer a stronger outcome from the scenario name.

## SentinelGuard

**PENDING CAPTURE — `sentinelguard.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/guard` and choose `sentinelguard-rejection`.
2. Confirm **SentinelGuard**, **SentinelGuard rejection**, the **Rollback available** checklist row marked **blocked**, and **Technical eligibility is not execution authorization**. Capture as `sentinelguard.png`. Keep the UI's header and checklist unchanged; a static header is not evidence that execution occurred.

## Safe Local Recovery

**PENDING CAPTURE — `safe-local-recovery.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/recovery` and choose `safe-local-recovery`.
2. Confirm **Recovery / Execution**, the LOCAL SANDBOX boundary, human approval and final gate checks, configured `rollback`, and recovery verification labels. Capture as `safe-local-recovery.png`; these are deterministic UI scenario values, not a newly executed recovery.

## Investigation

**PENDING CAPTURE — `investigation.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/investigation` and choose `competing-rca-hypotheses`.
2. Confirm **Grounded Investigation**, the provider label, and the disabled agent execution, RCA confirmation, Guard bypass, and human-approval bypass labels. Capture as `investigation.png`.

## System Status

**PENDING CAPTURE — `system-status.png`**

1. Open `http://127.0.0.1:4173/?mode=demo#/system` and choose `normal-operation`.
2. Confirm **System / Research Status**, production infrastructure/telemetry **NOT CONNECTED**, production benchmark **NOT MEASURED**, LOCAL SANDBOX, SIMULATED, and human authorization **REQUIRED**. Capture as `system-status.png`.

## Portfolio Home

**PENDING CAPTURE — `portfolio-home.png`**

1. Open `http://127.0.0.1:4174/` in the same 1440 × 1024 desktop viewport at 100% zoom and scroll to the top. There is no scenario selector for this page.
2. Confirm the project title and the visible LOCAL LAB / SYNTHETIC / DETERMINISTIC / NOT CONNECTED boundary card. Capture as `portfolio-home.png`. Leave all pending screenshot states unchanged elsewhere on the page.
