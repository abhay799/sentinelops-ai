# Step 26 smoke-case selection

Date: 2026-10-03

The smoke rule was fixed before smoke outputs were inspected: use the **first two
lexicographically sorted RE2-SS case IDs** from the already validated 90-case
suite. This deterministically selected:

1. `re2ss_carts_cpu_1`
2. `re2ss_carts_cpu_2`

The smoke was adapter/runtime validation only. The smoke scripts explicitly set
`ground_truth_read_for_smoke=false` and `accuracy_computed=false`; no AC@k,
Avg@5, rank-of-truth, or other accuracy statistic was computed on either case.
No setting was changed from smoke output.

Both smoke cases remain ordinary members of the final 90-case held-out suite.
They are not removed, downweighted, or treated as calibration cases in final
scoring. The final evaluation therefore still uses all 90 RE2-SS cases exactly
once under the frozen scoring rules.
