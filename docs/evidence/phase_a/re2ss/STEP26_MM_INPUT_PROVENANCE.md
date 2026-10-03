# Step 26 mmBARO/mmCIRCA input provenance

Date: 2026-10-03

RE2-OB mmBARO/mmCIRCA did not obtain log features by transforming the pinned
Hugging Face `logs.parquet` inside the Phase A harness. The committed Step-20
runner (`scripts/phase_a_step20_rcaeval_baselines.py`, first committed as
`ea1818e` at 2026-10-02T17:07:01Z) points instead to the separate native RCAEval
working tree `/home/dell/benchmarks/RCAEval/data/RE2/RE2-OB` and directly reads
`path.parent / "logts.csv"` for mmBARO/mmCIRCA.

The native RE2-OB case tree already contained preprocessed inputs before that
runner commit. Example `checkoutservice_cpu/1` contains `simple_metrics.csv`,
`logts.csv`, `tracets_err.csv`, and `tracets_lat.csv`, with filesystem mtimes
around 2026-10-02T15:45:51Z, about 81 minutes before `ea1818e`. The saved RE2-OB
case evidence also describes the trace inputs as `RCAEval-shipped preaggregated`
time series and records mmCIRCA as using metric plus logts.

No committed Phase A script was found that writes `logts.csv` from
`logs.parquet`; Step-20 only reads the already-preprocessed native files.
There is no frozen, audited harness transform from the selected HF raw logs
to native logts inputs for Step 26. The pinned RE2-SS Hugging Face cases contain only
`inject_time.txt`, `metrics.parquet`, and `logs.parquet`, and inventing a new
raw-log-to-logts transform after held-out access would change the input contract.
No such transform will be introduced for Step 26.

## Physical availability versus the selected contract correction

The official RCAEval RE2-SS archive does ship `logts.csv`. The statements above
refer to the selected HF bundle and absence of a frozen harness transform, not
absence from every official distribution. Native archive logts is outside the
pinned SS input contract; mmBARO/mmCIRCA remain n/a by the pre-scoring decision
in `68ade27`, independently of outcomes. See STEP26_MM_UNAVAILABLE_ERRATUM.md.
No mm run is authorized by this note.
