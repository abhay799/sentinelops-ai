# RE2-OB Steps 21-24 implementation plan

Goal: complete the authorized frozen RE2-OB evaluation and stop at Step 25.
Spec: docs/evidence/PHASE_A_EVALUATION_SPEC.md (E3, E4, A4, E6, E7).
Execution: inline in the existing benchmark workspace; no push or held-out access.

- [x] E7 committed first, b7a6bf8.
- [x] Write synthetic scoring tests; observe the absent-module failure.
- [x] Add rcaeval_scoring.py for order-preserving filtering, E4 misses,
  metric definitions, paired bootstrap, valid-only cohorts and A4 graph-only scoring.
- [x] Add phase_a_steps21_24.py using saved RE2-OB evidence only, with
  stage-specific commands and artifact writes.
- [x] Pass focused tests and relevant lint; commit evaluator before benchmark scoring.
- [x] Run and commit Step 21 overall primary/valid-only/native tables.
- [x] Run and commit Step 22 per-fault tables.
- [x] Run and commit Step 23 CIs and paired differences, shared resamples.
- [x] Run and commit Step 24 JSON/CSV manifest and report, A4 separate.
- [x] Independent code review, full suite and evidence reconciliation.
- [x] Stop at 25 and present the RE2-OB table.

Global constraints: seed 42; 10000 case resamples; 95% percentile CIs;
fixed denominator 90; fallbacks count as misses; E3 before top-k;
Avg@5 = mean AC@1..5; Lift@5 = AC@5/(5/11); random never redrawn.
Keep original seed-42 sanity false and diagnostic mean/SD beside baseline.
Revalidate SHA256 of all existing rankings; record exact commands,
revisions, config, raw ranks, fault cohorts, coverage, fallbacks and runtimes.

Pre-flight interfaces: saved rankings -> scoring arrays -> point tables ->
bootstrap tables -> report/CSV. Shared case order must be identical.
A4 uses saved strengths and original primary bonuses, graph impact only
from the A4 allowlist graph; excluded native rows receive zero graph impact.
A4 PageRank uses the same static graph; primary PageRank is unchanged.

Review focus: filter before truncation; fallback contamination; paired index
alignment; reduced valid-only denominators; changed A4 primary bonuses.
