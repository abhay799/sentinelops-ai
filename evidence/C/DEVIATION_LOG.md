# Phase C Deviation Log

## C-DEV-001 — Phase 5 legacy-mode output regression unavailable

- **Stage:** C2/C3 prerequisite audit carried into C4.
- **Requested check:** run the existing Phase 5 mode on the saved Phase 5 input before and after adding the explicit fit/freeze path and prove byte-identical outputs.
- **Observed limitation:** the saved Phase 5 input `data/processed/features/temporal_features_v1.parquet`, the corresponding saved anomaly output, and the saved Phase 5 model are absent from the accessible WSL workspace and repository history.
- **What was verified instead:** `scripts/train_phase5_anomaly.py` was not modified; its working-tree Git blob and committed `HEAD` blob were identical at the C2/C3 checkpoint (`9782a8d8fba0c4cfd8de19be1450bd271c0752da`).
- **Interpretation:** this is code-identity evidence only. It is not equivalent to an empirical byte-identical output regression.
- **Registered-fit consequence:** no registered detector fit has been run. The explicit baseline-fit/freeze path remains the only preregistered registered-fit path.
- **Windows-side read-only check:** `C:\Users\DELL\sentinelops-ai\data` does not exist. `C:\Users\DELL\Projects\sentinelops-ai\data` exists, but no files named `temporal_features_v1.parquet`, `anomaly_scores_v1.parquet`, or `early_warning_v1.parquet` were found in its processed tree during the C4 check; no matching Isolation Forest model was found in its models tree.
