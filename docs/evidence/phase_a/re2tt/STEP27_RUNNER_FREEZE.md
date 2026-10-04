# Step 27 RE2-TT runner freeze

Date: 2026-10-04
Status: frozen before any Step 27 RCA method ranking or scoring.

Frozen scripts and SHA-256:

- `scripts/phase_a_step27_run.py`: `f22505e4a522a6a478fa33fbcfcaf67ccc4c79969908a5f6171ac1a2025d9c7a`
- `scripts/phase_a_step27_rcaeval_run.py`: `210ff1db9e638eb55bdbfa9484d6d791b7f5ed9f307610f5a17ab58e09047a96`
- `scripts/phase_a_step27_score.py`: `dc29c2cd656cb06a53ae37cea6c3a6dfd5ac6a9cc75aa4dbe459a8c6fc2b503a`

Validation before freeze:

- Ruff: pass.
- Python compilation: pass.
- git diff --check: pass.
- Relevant Phase A RCA/evaluation tests: 46 passed.

The local runner uses the frozen RE2-TT static suite graph, v1, selected V2a, threshold 2.5, random master seed 42, and PageRank damping 0.85. The native RCAEval runner uses pinned RCAEval revision `259ea4167160256a74ad30004aa3d96a998c846e`, dataset `re2-tt`, and fixed root-cause-independent `ts-ui-dashboard_latency` SLI. BARO and CIRCA are runnable. mmBARO/mmCIRCA remain n/a outside the pinned input contract.

No root-cause label or ranking accuracy was used to create or validate these runners.
