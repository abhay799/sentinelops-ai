# RE2-OB SLI-Selection Disclosure

Date: 2026-10-03
Scope: provenance audit only; no fixes or reruns.

Both pinned RCAEval `main.py` and the Phase A Step 20 harness derive `service`
from the case directory/path. For RE2-OB they default `sli` to
`frontend_latency`, but use `<service>_latency` when that column exists, with
`frontend_1` as the harness/native fallback where applicable. Because the case
path encodes the injected service, this SLI-selection rule is root-service
informed and must be disclosed.

For the four Step 20 methods at pinned RCAEval revision
`259ea4167160256a74ad30004aa3d96a998c846e`, source audit shows:
- BARO accepts `sli` in its signature but never reads it in its computation.
- CIRCA accepts it only through `**kwargs` and never reads it.
- mmBARO forwards `sli` to `mmnsigma`; `mmnsigma` accepts but never reads it.
- mmCIRCA accepts it through `**kwargs` and never reads it.

Therefore the root-service-informed SLI variable is a provenance/comparability
caveat, but it does not alter BARO/CIRCA/mmBARO/mmCIRCA rankings at this pinned
revision. This statement is specific to these methods and revision; it must not
be generalized to other RCAEval methods that may use `sli`.

No ranking, score, input window, candidate set, fallback status, or evaluation
metric is changed by this disclosure. No RE2-SS/RE2-TT raw case content was
opened. Never push.
