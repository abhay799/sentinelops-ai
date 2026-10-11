# Phase C Deviation Log

## C-DEV-001 — Phase 5 legacy-mode output regression unavailable

- **Stage:** C2/C3 prerequisite audit carried into C4.
- **Requested check:** run the existing Phase 5 mode on the saved Phase 5 input before and after adding the explicit fit/freeze path and prove byte-identical outputs.
- **Observed limitation:** the saved Phase 5 input `data/processed/features/temporal_features_v1.parquet`, the corresponding saved anomaly output, and the saved Phase 5 model are absent from the accessible WSL workspace and repository history.
- **What was verified instead:** `scripts/train_phase5_anomaly.py` was not modified; its working-tree Git blob and committed `HEAD` blob were identical at the C2/C3 checkpoint (`9782a8d8fba0c4cfd8de19be1450bd271c0752da`).
- **Interpretation:** this is code-identity evidence only. It is not equivalent to an empirical byte-identical output regression.
- **Registered-fit consequence:** no registered detector fit has been run. The explicit baseline-fit/freeze path remains the only preregistered registered-fit path.
- **Windows-side read-only check:** `C:\Users\DELL\sentinelops-ai\data` does not exist. `C:\Users\DELL\Projects\sentinelops-ai\data` exists, but no files named `temporal_features_v1.parquet`, `anomaly_scores_v1.parquet`, or `early_warning_v1.parquet` were found in its processed tree during the C4 check; no matching Isolation Forest model was found in its models tree.

## C-DEV-002 — Registered executor omitted from original prerun freeze

- **Amendment time (UTC):** `2026-10-10T19:43:32Z`.
- **Stage:** C6 start gate, before registered run 1.
- **Observed limitation:** `freeze/C-prerun` froze the registry, scenario/config hashes, analysis and evidence schema, but the repository had only the non-registry dry-run harness and no executable registered-run orchestration entry point.
- **Results visible:** no. Zero registered runs had started and no registered result existed when this was discovered and amended.
- **Action:** add the registered TRAIN executor and tests without changing any frozen registry identity, seed, partition, scenario parameter, Guard threshold, analysis metric, or replacement rule.
- **Freeze treatment:** preserve `freeze/C-prerun` unchanged and create a new preregistration freeze `freeze/C-prerun-v2` before run 1.
- **Methodology note:** C6 TRAIN uses the existing legacy Phase 5 detector only for development-chain evidence. The registered detector-fit gate remains C7: TRAIN baselines only, artifact SHA-256 frozen before VALIDATION.


## C-DEV-003 — C6 loop and non-registry executor mode absent from v2 checklist

- **Amendment time (UTC):** `2026-10-11T16:41:10Z`.
- **Stage:** C6 start gate, amendment 3, before registered run 1.
- **Cause:** the executor loop and non-registry mode were absent from the v2 checklist/freeze, so the v2 executor could not yet satisfy resumable unattended TRAIN execution or pre-result non-registry path validation.
- **Registered-result state:** no registered run executed, no registered result exists.
- **Action:** add the resumable TRAIN loop, non-registry executor mode with collision protection, completeness inventory, tests, and v3 freeze coverage before any registered execution.
- **Methodology impact:** none to the frozen registry identities, seeds, partition assignment, scenario definitions, Guard/remediation thresholds, registered analysis metrics, or C7 detector-fit rule.
