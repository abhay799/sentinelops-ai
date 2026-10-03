# Pre-Step-21 baseline process checkpoint

Checked 2026-10-03 using ps -eo pid,etime,args.

Initial check: CIRCA PID 1593 and mmCIRCA PID 1594 were both running.
No relaunch was needed. At this later checkpoint only CIRCA remains running;
mmCIRCA has written all 90 case records and its completion summary.
The runner resumes E4-aware cached cases and logs progress under logs/.

Current process snapshot:

- 1593       18:40 /home/dell/benchmarks/RCAEval/.venv/bin/python scripts/phase_a_step20_rcaeval_baselines.py --method circa

Saved case status counts (progress snapshot; expected 90 per method):

- baro: {"ok": 90}
- circa: {"fallback_unranked": 3, "ok": 67}
- mmbaro: {"ok": 90}
- mmcirca: {"fallback_unranked": 1, "ok": 89}

Logs: logs/step20_circa_e4.log and logs/step20_mmcirca_e4.log.
No AC@k was computed and no baseline data files were modified by this check.
Final fallback validation remains gated on both jobs completing.
