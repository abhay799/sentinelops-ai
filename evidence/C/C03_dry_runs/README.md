# C03 dry-run evidence

Everything under this directory is development-only `non_registry` evidence.

These artifacts must never be included in the preregistered Phase C result set. The control-path dry runs do not sleep the configured 120/180-second injection windows or the 120-second baseline/cool-down periods and do not represent performance measurements.

Ground-truth injection records are isolated under `_ground_truth_injection_only/`. Detection, correlation, RCA, challenger, and SentinelGuard modules are prohibited by test from reading or importing that source.
