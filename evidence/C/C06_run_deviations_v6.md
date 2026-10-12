# C6 Run Deviations — Amendment 6

## C6-DEV-006 — Environmental pre-injection interruption during Amendment 5 rerun

Registered identity:

- run_id: `C-SPARE-TRAIN-BDR-02`
- seed: `300872472`
- scenario: `bad_deployment_rollback`
- replacement_for: `C-TRAIN-BDR-12`

Attempt artifact:

`C-SPARE-TRAIN-BDR-02__a5_rerun`

Observed state:

- stage: `pre_injection_reset`
- exception: `httpx.ReadTimeout`
- injection_start: null
- run_summary.json absent
- no registered outcome visible

Preserved partial evidence SHA-256:

- execution_state.json:
  `6eed79cb8666435c256dc6fcc29d0e61536d7e8027bd49c0596502f921098f10`
- preflight_health.json:
  `9860150db32ae6e14a32d138f1d5fb6e988aaf8db099cb980ad71392d75084b3`

Classification:

Recognized pre-injection environmental interruption.

This is not a harness defect and does not consume another spare.

Recovery:

The prior attempt remains immutable. After Amendment 6 is frozen, one
subsequent attempt may use the same registered run identity and original seed
under the distinct artifact namespace:

`C-SPARE-TRAIN-BDR-02__a5_rerun_02`

The original historical BDR-02 record and first Amendment 5 rerun artifact must
remain unchanged.
