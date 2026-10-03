# Published RE2-OB Comparison

Date: 2026-10-03
Scope: literature/reproduction audit; no reruns or scoring changes.

## Published BARO result

GALA (arXiv:2508.12472), Table 2, reports BARO on RE2-OB as:
- AC@1: 14.44%
- Avg@3: 61.48%
- Avg@5: 74.22%

Its per-fault BARO Avg@5 table reports CPU 64.00%, Delay 66.67%, Disk 81.33%,
Loss 80.00%, Mem 86.67%, and Socket 66.67%.
Source: https://arxiv.org/abs/2508.12472

Phase A saved BARO primary values are AC@1=0.144444 and Avg@5=0.742222;
AC@1/AC@2/AC@3 imply Avg@3=0.614815. These match the published GALA BARO
values to two decimal percentage points. The existing pinned native BARO log
reports per-fault Avg@5 CPU 0.64, MEM 0.87, DISK 0.81, SOCKET 0.67,
DELAY 0.67, LOSS 0.80, also matching GALA after its displayed rounding.

A second published source, Wang et al., *Smarter Root Cause Analysis: Enhancing
BARO With Outlier Filtering and Ranking Refinement*, IEEE Access 2025,
DOI 10.1109/ACCESS.2025.3602962, reports the unmodified BARO/max-z baseline
RE2-OB Avg@5 as 0.74, consistent with the values above.

## Scope limitation

The RCAEval README's explicit paper-reproduction example is BARO on RE2-TT.
It states that methods/datasets can be substituted, but that is not an
independent published four-method RE2-OB target table. No authoritative
published RE2-OB target was established here for CIRCA, mmBARO, or mmCIRCA.
Those Phase A values must be labeled pinned-code/native or harness results,
not literature reproductions.

RCAEval README: https://github.com/phamquiluan/RCAEval/blob/main/README.md
IEEE Access DOI: https://doi.org/10.1109/ACCESS.2025.3602962

No benchmark evidence was changed. RE2-SS/RE2-TT were not started. Never push.
