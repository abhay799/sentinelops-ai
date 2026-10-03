# Held-out Catalog Read Statement

Date: 2026-10-03

The shared Hugging Face `cases.parquet` catalog was read for dataset-level
metadata counts during the Phase A audit. That catalog contains 90 metadata rows
for RE2-SS and 90 metadata rows for RE2-TT, in addition to 90 RE2-OB rows.

This catalog read is disclosed because RE2-SS and RE2-TT are held out. The read
was limited to catalog metadata (`dataset` counts); no RE2-SS/RE2-TT raw metrics,
logs, traces, injection files, rankings, labels beyond catalog-level dataset
identity, or outcomes were opened or evaluated.

Current targeted filesystem checks found:
- `/home/dell/benchmarks/RCAEval/data/RE2/RE2-SS`: absent.
- `/home/dell/benchmarks/RCAEval/data/RE2/RE2-TT`: absent.
- local HF revision root: 0 `re2ss_*` case directories.
- local HF revision root: 0 `re2tt_*` case directories.

Therefore the held-out raw suites have not been downloaded into the inspected
Phase A locations and no held-out evaluation has started. This statement does
not claim an exhaustive scan of every file on the machine. Never push.
