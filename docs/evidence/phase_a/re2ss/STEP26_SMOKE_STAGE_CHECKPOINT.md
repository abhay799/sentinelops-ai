# Step 26 smoke-stage checkpoint

Date: 2026-10-03

The smoke implementation/evidence itself was committed earlier as `9009bac`
(`evidence: validate Step 26 RE2-SS smoke adapters`). Before the full 90-case
run, this checkpoint confirms that stage remains the authoritative smoke record.

Validated on exactly the two smoke cases (selection documented retrospectively;
see STEP26_SMOKE_SELECTION.md):
- v1: non-empty E3-filtered ranking;
- V2a: non-empty E3-filtered ranking and all strengths finite;
- static threshold: non-empty E3-filtered ranking;
- random seed 42: deterministic non-empty E3-filtered ranking;
- PageRank: non-empty E3-filtered ranking on the frozen static topology;
- BARO: native smoke ranking returned without fallback;
- CIRCA: native smoke ranking returned without fallback.

mmBARO/mmCIRCA are separately covered by the pre-scoring input-unavailable
erratum and are not part of the full SS numerical run.

Smoke accuracy remained uncomputed, no smoke case was removed from the final
90, and no parameter, mapping rule, topology, allowlist, or method was tuned
from smoke output. Targeted Ruff/tests at `9009bac` passed (22 tests).
