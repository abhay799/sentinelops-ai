# Step 27 RE2-TT topology validation

Date: 2026-10-04
Status: validated before any Step 27 RCA method run or scoring.

The frozen topology runner completed all 90 RE2-TT cases successfully. It produced a label-free static suite graph from pre-injection trace parent/child relationships only: 69 metric-visible nodes and 55 directed caller-to-callee edges. Ground truth was not used.

The graph intentionally retains metric-visible infrastructure/database/support nodes. This is consistent with frozen Erratum E3.1: PageRank is computed on the full frozen graph and the resulting native ranking is then deterministically filtered to the frozen 45-service RE2-TT application allowlist. The topology is therefore not rewritten to the allowlist after seeing TT data.

The aggregate unresolved-parent count is 501981. The frozen adapter separately checks every unresolved pre-injection parent key against the complete trace table and hard-fails if that parent exists elsewhere in the full traces, which would make the pre-injection boundary ambiguous. No case failed that check. Therefore these unresolved parents do not establish post-injection leakage or an ambiguous cross-boundary parent mapping under the frozen rule.

No exact duplicate/conflicting trace-key case was reported. All 90 topology case artifacts completed with status ok.
