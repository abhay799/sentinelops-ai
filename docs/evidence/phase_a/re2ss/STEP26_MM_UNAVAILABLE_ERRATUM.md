# Step 26 Erratum - mmBARO/mmCIRCA excluded by the pinned SS input contract

Date: 2026-10-03
Status: exclusion decided and committed before any RE2-SS scoring;
physical-availability wording corrected retrospectively.

The official RCAEval RE2-SS archive **does ship `logts.csv`**. It is therefore
incorrect to describe the required preprocessed logs as physically absent
from all official SS distributions.

The selected pinned Hugging Face SS bundle provides `metrics.parquet`,
`logs.parquet` and `inject_time.txt`. The frozen Step 26 contract does not
include native archive `logts.csv` or a frozen, audited conversion from HF raw
logs into that input. Adding the archive modality or a new conversion after
held-out access would change the pinned input contract.

The exclusion was recorded in `68ade27` before SS accuracy scoring and was
based on that contract, not on SS outcomes. This correction does not reverse
the decision and authorizes no mm run:
- mmBARO = `n/a (outside pinned input contract)`;
- mmCIRCA = `n/a (outside pinned input contract)`;
- both remain excluded from SS numerical comparisons and paired CIs;
- neither is counted as a fallback or scored as 90 misses;
- there are 0 evaluable cases for these methods under the selected contract.

The frozen scorer's literal label `n/a (input unavailable)` and its
`input_unavailable=90` field mean unavailable **under this contract**, not
absent from the official archive and not 90 execution failures. Its evidence
will be read with this correction; no code change is made.

No new modality, transform, method, ranking, filter, seed, bootstrap rule or
denominator is introduced. Do not run mm methods. RE2-TT remains untouched.
Never push.
