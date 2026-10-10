# Phase A Held-out Burn Log — Retroactive Reconstruction

This log is a **retroactive reconstruction** from committed provenance and result artifacts. It was not the contemporaneous mechanism that controlled access during Steps 26–27; the contemporaneous pre-run/preflight documents remain the primary evidence for what was frozen before access.

For this reconstruction, a suite is considered **burned when results first become visible**, not merely when raw data is first accessed. Raw-data access is recorded separately because it marks the loss of data secrecy even before aggregate scoring.

## RE2-SS

- **Data first accessed:** no later than commit `ed05649ecb69a24bfca059f185ce45f8c0564cdd` at `2026-10-03T11:13:55Z`, which first committed `docs/evidence/phase_a/re2ss/step26_download_integrity.json` after RE2-SS download/validation.
- **Results first visible / burn point:** no later than commit `bdc9dc0dbc72caf1348c2dd948acce59656bbcea` at `2026-10-03T13:34:36Z`, which first committed `step26_results.json` and `STEP26_RESULTS.md`. The local `step26_results.json` file mtime is `2026-10-03T13:31:03` in the benchmark workspace, but the committed timestamp is the authoritative repository checkpoint used here.
- **Burn status:** BURNED at the results-visible point above.
- **Post-burn rule:** no RE2-SS result may be used to tune thresholds, weights, features, topology, candidate rules, or method selection and then be re-reported as a fresh RE2-SS held-out result.

## RE2-TT

- **Data first accessed:** no later than commit `6757c9d5d52e4863840c39c7cd1782b8babc986f` at `2026-10-03T16:36:28Z`, which first committed `docs/evidence/phase_a/re2tt/step27_download_integrity.json` after RE2-TT download validation.
- **Results first visible / burn point:** no later than commit `3b1680947b93c5028a7930a732a9cae91bc19acc` at `2026-10-10T15:17:06Z`, which first committed `step27_results.json` and `STEP27_RESULTS.md`. The local `step27_results.json` file mtime is `2026-10-10T15:14:09` in the benchmark workspace, but the committed timestamp is the authoritative repository checkpoint used here.
- **Burn status:** BURNED at the results-visible point above.
- **Post-burn rule:** no RE2-TT result may be used to tune a method, threshold, graph rule, detector/RCA parameter, candidate rule, fallback rule, scorer, or analysis and then be presented as a fresh original RE2-TT held-out result.

Any post-burn methodological change intended for confirmation requires a new versioned protocol and a new held-out test set.
