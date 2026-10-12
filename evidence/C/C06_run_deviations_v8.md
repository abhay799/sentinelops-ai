# Phase C C6 Amendment 8 Run Deviations

## C6-DEV-008 — Authoritative re-execution resolution

A resume audit after Amendment 7 showed that the TRAIN loop still saw
the historical base summary for `C-SPARE-TRAIN-BDR-02` as:

`infrastructure_invalid_interrupted`

while the authoritative finalized registered result existed in:

`C-SPARE-TRAIN-BDR-02__a5_rerun_02/run_summary.json`

with:

- status: `run_failed_after_injection`
- registered_result_eligible: `true`
- counted_in_analysis_denominator: `true`
- replacement_for: `C-TRAIN-BDR-12`
- seed: `300872472`

This created a resume-accounting hazard: the replacement loop could
ignore the authoritative post-injection result and incorrectly continue
replacement selection.

Amendment 8 changes only summary resolution.

It does not:

- rerun any registered case;
- create another artifact namespace;
- alter the registered seed;
- alter historical evidence;
- alter the Amendment 7 classification;
- consume another spare.

The resolver fails closed if multiple authoritative re-execution
summaries are found for the same spare and primary replacement pair.

Read-only verification confirmed that BDR-12 now resolves through
`C-SPARE-TRAIN-BDR-02__a5_rerun_02`.

The next scheduled TRAIN primary is:

`C-TRAIN-LAT-11`
