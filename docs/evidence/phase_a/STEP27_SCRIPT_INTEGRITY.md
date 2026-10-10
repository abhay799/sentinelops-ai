# Step 27 Script Integrity Record

Status: recorded after RE2-TT Step 27 execution and before Step 28 consolidation.

Frozen comparison commit: `c4c4224`

## Scripts that produced the Step 27 results

| Path | SHA-256 |
|---|---|
| `scripts/phase_a_step27_score.py` | `3ca8cc77aa6dae0f55885db77e6a3b6c465462a5c8d120ae60e20d16d2b16bb2` |
| `scripts/phase_a_step27_rcaeval_run.py` | `fdee1bc33ba59a9d70a9cfa566f461110fcb20ebdb5fc9fc81983dbe30ffb9f3` |

## Change classification relative to c4c4224

### scripts/phase_a_step27_rcaeval_run.py

- **Timeout policy:** adds a fixed CIRCA per-case timeout of 1800 seconds and records timed-out cases as `timeout_unranked`.
- **Queue fix:** replaces the multiprocessing Queue result channel with a one-way Pipe so the parent can receive a completed worker result without the Queue feeder/join interaction that could block process completion.
- **Status handling / resume:** treats `timeout_unranked` as a terminal cached status, counts it in the run summary, and skips it on resume.
- **Other:** multiprocessing import and worker/wrapper plumbing required to enforce the timeout.

The existing `run_case` implementation, method invocation, candidate allowlist, topology, ranking extraction, and ranking parameters are unchanged. The timeout wrapper can stop an over-budget CIRCA case and return an empty ranking with explicit status, but it does **not** alter CIRCA's ranking logic for any case that returns within the fixed budget.

### scripts/phase_a_step27_score.py

- **Status handling:** adds `timeout_unranked` as an explicit coverage category instead of leaving it inside `other_statuses`.
- **Reporting:** adds a Timeout column to the generated markdown table and updates explanatory text so timeout outcomes are explicitly named.

The scoring math is unchanged: `case_hits` already maps every status other than `ok` to an all-zero hit vector; metric definitions, all-90 denominator, bootstrap seed/sample count, paired-difference calculations, per-fault calculations, valid-only mask (`status == "ok"`), and Chance@5 are unchanged.

## Integrity conclusion

No observed change modifies ranking logic or scoring mathematics.

The runner changes are execution-budget/resume/result-transport changes. The scorer changes make the timeout status explicit in coverage/reporting while preserving the pre-existing non-`ok`-equals-miss scoring rule.

## Backup files retained untracked

The following original backup files are intentionally **not deleted** and are left untracked in `scripts/`:

| Path | SHA-256 | Purpose |
|---|---|---|
| `scripts/phase_a_step27_rcaeval_run.py.pre_timeout_backup` | `210ff1db9e638eb55bdbfa9484d6d791b7f5ed9f307610f5a17ab58e09047a96` | Snapshot before the 1800-second timeout wrapper |
| `scripts/phase_a_step27_rcaeval_run.py.before_queue_fix` | `4167922a0da79e3187591b50d8db14daa8c838e7e5cd0b18e66f93a0f7093a72` | Snapshot before Queue-to-Pipe result-transport fix |

These backups are evidence only and are not runtime inputs.
