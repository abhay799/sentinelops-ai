# Step 26 Erratum - mmBARO/mmCIRCA unavailable on RE2-SS

Date: 2026-10-03
Status: decided and committed **before any RE2-SS scoring**.

The pinned RE2-SS input bundle provides `metrics.parquet`, `logs.parquet`, and
`inject_time.txt`, but the pinned RCAEval mmBARO/mmCIRCA path requires the
preprocessed `logts.csv` input used by the native multi-source benchmark.
No frozen, audited raw-log-to-logts transform exists in the Phase A harness for
RE2-SS, and no transform will be invented after held-out access.

Therefore, for Step 26:
- mmBARO = `n/a (input unavailable)`;
- mmCIRCA = `n/a (input unavailable)`;
- both are excluded from the RE2-SS numerical method comparison and paired-CI
  matrix;
- they are **not** treated as fallback rankings and **not** scored as 90 misses;
- coverage reporting will state 0 evaluable cases because the required input
  modality is unavailable under the frozen contract, not because the methods
  failed on 90 cases.

This decision changes only how unavailable methods are represented. It does not
change any runnable method, candidate allowlist, score, bootstrap rule, or
held-out ranking. RE2-TT remains untouched.
