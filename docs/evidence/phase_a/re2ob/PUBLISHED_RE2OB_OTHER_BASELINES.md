# Published RE2-OB Check: CIRCA, mmBARO, mmCIRCA

Date: 2026-10-03
Scope: publication/source check only; no reruns or score changes.

## CIRCA

No directly citable published RE2-OB numeric target was found in the sources
checked. The current RCAEval README states that its `main.py` reproduces paper
results and that one can substitute methods such as CIRCA and datasets such as
RE2-OB to reproduce the corresponding Table 6 entries. However, the accessible
README text exposes a concrete BARO/RE2-TT numeric example, not a CIRCA/RE2-OB
number. Therefore Phase A has **not** compared its CIRCA RE2-OB value against a
verified published numeric target.

Source: https://github.com/phamquiluan/RCAEval/blob/main/README.md

## mmBARO and mmCIRCA

No published RE2-OB numeric targets were found for multi-source BARO or
multi-source CIRCA. RCAEval's current README/release history documents runnable
`mmbaro --dataset re2-ob` and `mmcirca --dataset re2-ob` commands and notes that
multi-source benchmark wiring was added in 2026. These sources provide runnable
benchmark support, but not paper-table RE2-OB numeric targets for these two
methods.

Sources:
- https://github.com/phamquiluan/RCAEval/blob/main/README.md
- https://github.com/phamquiluan/RCAEval/releases

Conclusion: BARO has a published RE2-OB comparison recorded separately; CIRCA,
mmBARO, and mmCIRCA do not currently have verified published RE2-OB numeric
comparisons in Phase A. Their saved values must remain labeled as pinned-code
native/harness results rather than literature reproductions. Never push.
