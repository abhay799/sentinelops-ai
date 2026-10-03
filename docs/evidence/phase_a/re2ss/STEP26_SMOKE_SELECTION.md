# Step 26 smoke-case selection provenance correction

Date: 2026-10-03
Status: retrospective documentation; no new smoke or accuracy run.

The smoke used these two cases, which are the first two lexicographically
sorted RE2-SS case IDs:
1. `re2ss_carts_cpu_1`
2. `re2ss_carts_cpu_2`

The scripts and completed smoke evidence were first committed together in
`9009bac47a26229e77e64c5fc8ee1297603b9d21` at
2026-10-03T11:36:47Z. The standalone selection-rule note was committed later
in `f90609fc1e5d0915bef34b0264c4ac49a52e3b2c` at
2026-10-03T12:01:58Z. Consequently this rule was not separately committed
before the smoke ran. The previous wording "fixed before smoke outputs were
inspected" is not independently established by those commits and is
withdrawn. The checked-in smoke scripts hard-code the same two cases, but
their co-commit with outputs does not prove pre-run registration.

This is a provenance correction, not outcome-driven case selection. The saved
smoke records declare `ground_truth_read_for_smoke=false` and
`accuracy_computed=false`; the smoke code checks runtime, non-empty rankings,
finiteness and fallback status, and does not compute rank-of-truth or accuracy.
There is no evidence in those smoke artifacts of AC@k, Avg@5, Lift@5, or an
accuracy-based choice. A negative historical claim about every possible shell
command cannot be independently proved.

Both smoke cases remain in the full 90-case SS suite with the same weight as
every other case. No case is removed, downweighted, or used for calibration
beyond the frozen per-case preprocessing. No method, setting, ranking, or
scoring rule is changed here. No jobs are started or killed. Never push.
