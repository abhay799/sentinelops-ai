export const lifecycle = ["Sense", "Detect", "Predict", "Correlate", "Diagnose", "Challenge RCA", "Simulate", "Prioritize", "Plan", "Guard", "Human Authorization", "Controlled Execution", "Verify", "Investigate"];

export const scenarios = [
  ["normal-operation", "Cautious local baseline"],
  ["early-degradation", "Early warning before incident creation"],
  ["correlated-multi-signal", "Correlated anomaly, temporal, graph, and change evidence"],
  ["competing-rca-hypotheses", "Ranked hypotheses, not a confirmed cause"],
  ["adversarial-rca-challenge", "Contradictory evidence and alternatives"],
  ["sentinelguard-rejection", "Fail-closed proposal rejection"],
  ["human-authorization-pending", "Technical eligibility without execution"],
  ["safe-local-recovery", "Authorized sandbox rollback and verification"],
  ["failed-verification-safe-failure", "Safe local re-verification failure path"],
];

export const layers = [
  "Distributed Demo System", "Observability", "Feature Platform", "Anomaly Intelligence", "Dependency Graph", "Incident Correlation", "Evidence-based RCA", "Causal / Adversarial RCA", "Failure Prediction", "Counterfactual Simulation", "SLO / Priority Intelligence", "Remediation Planning", "SentinelGuard", "Human Authorization", "Local Sandbox Execution", "Recovery Verification", "Grounded Investigation", "Control Center",
];

export const previews = [
  ["Mission Control", "mission-control.png", "safe-local-recovery", "The lifecycle, evidence context, and local recovery state."],
  ["RCA / Challenger", "rca-challenger.png", "adversarial-rca-challenge", "Candidate hypotheses and structured challenge evidence."],
  ["SentinelGuard", "sentinelguard.png", "sentinelguard-rejection", "Fail-closed guard checks before authorization."],
  ["Recovery", "safe-local-recovery.png", "safe-local-recovery", "The configured local rollback adapter and verification."],
  ["Investigation", "investigation.png", "competing-rca-hypotheses", "Grounded investigation without independent RCA confirmation."],
];

export const docLinks = [
  ["README", "https://github.com/abhay799/sentinelops-ai#readme"],
  ["Running Guide", "https://github.com/abhay799/sentinelops-ai/blob/main/docs/RUNNING.md"],
  ["Architecture", "https://github.com/abhay799/sentinelops-ai/blob/main/docs/architecture/PROJECT_ARCHITECTURE.md"],
  ["Demo Scenarios", "https://github.com/abhay799/sentinelops-ai/blob/main/docs/demo/SCENARIOS.md"],
  ["Evidence Report", "https://github.com/abhay799/sentinelops-ai/blob/main/docs/evidence/BENCHMARKS_AND_EVIDENCE.md"],
  ["Control Center", "./control-center/"],
];
