from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/phase_a/re2ob"
RCA = OUT / "rca_cases"
STEP21 = OUT / "step21_cases.json"


def main() -> None:
    scored = json.loads(STEP21.read_text())["cases"]
    by_case = {row["case_id"]: row for row in scored}
    rows = []
    for path in sorted(RCA.glob("*.json")):
        payload = json.loads(path.read_text())
        case_id = payload["case_id"]
        case = by_case[case_id]
        truth = case["root_cause_service"]
        final = case["methods"]["SentinelOps"]["e3_filtered_service_ranking"]
        eligible = set(final)
        evidence = {r["service"]: r for r in payload["ranking"] if r["service"] in eligible}
        strengths = {s: float(evidence[s]["anomaly_strength"]) for s in final}
        top_strength = max(strengths.values())
        strength_one = [s for s in final if strengths[s] == 1.0]
        top_tied = [s for s in final if strengths[s] == top_strength]
        truth_tie_pos = (
            top_tied.index(truth) + 1 if truth in top_tied else None
        )
        rows.append({
            "case_id": case_id,
            "fault": case["fault"],
            "root_cause_service": truth,
            "strength_eq_1_count": len(strength_one),
            "strength_eq_1_services_final_order": strength_one,
            "top_strength": top_strength,
            "top_tie_count": len(top_tied),
            "top_tied_services_final_order": top_tied,
            "true_service_position_within_top_tie": truth_tie_pos,
            "true_service_final_rank": final.index(truth) + 1,
            "ac_at_1": int(final[0] == truth),
        })

    no_tie = [r for r in rows if r["top_tie_count"] == 1]
    tie = [r for r in rows if r["top_tie_count"] > 1]
    truth_in_top_tie = [r for r in rows if r["true_service_position_within_top_tie"] is not None]
    def ac1(group):
        return sum(r["ac_at_1"] for r in group) / len(group) if group else None

    summary = {
        "case_count": len(rows),
        "tie_definition": (
            "top tie means more than one E3-eligible service has the "
            "maximum saved anomaly_strength"
        ),
        "strength_eq_1_count_distribution": dict(
            sorted(Counter(r["strength_eq_1_count"] for r in rows).items())
        ),
        "top_tie_count_distribution": dict(
            sorted(Counter(r["top_tie_count"] for r in rows).items())
        ),
        "no_top_tie": {"cases": len(no_tie), "ac_at_1": ac1(no_tie)},
        "top_tie": {"cases": len(tie), "ac_at_1": ac1(tie)},
        "true_service_in_top_tied_group_count": len(truth_in_top_tie),
        "true_service_position_within_top_tie_distribution": dict(
            sorted(
                Counter(
                    r["true_service_position_within_top_tie"]
                    for r in truth_in_top_tie
                ).items()
            )
        ),
        "tie_breaking": {
            "primary_service": (
                "max(sorted(service_strengths), key=(strength, service)); "
                "equal max strength therefore chooses lexicographically "
                "largest service for primary bonus"
            ),
            "final_ranking": (
                "descending rounded rca_score, then service name ascending "
                "for equal rca_score"
            ),
            "ranking_weights_unchanged": True,
        },
        "ground_truth_used_for_ranking": False,
        "cases": rows,
    }
    (OUT / "sentinelops_tie_diagnostic.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "cases"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
