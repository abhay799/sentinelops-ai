"""E5 rank-preservation audit; deliberately performs no ground-truth scoring."""
import json
import subprocess
from collections import Counter
from pathlib import Path

BASE = "f0e1f41^"
AFTER = "6de0260"
OUT = Path("docs/evidence/phase_a/re2ob")
ALLOW = set(("adservice cartservice checkoutservice currencyservice emailservice "
             "frontend paymentservice productcatalogservice recommendationservice "
             "redis shippingservice").split())

def read(ref, path):
    return json.loads(subprocess.check_output(["git", "show", f"{ref}:{path}"], text=True))

paths = sorted(subprocess.check_output(
    ["git", "ls-tree", "-r", "--name-only", AFTER, str(OUT / "rca_cases")],
    text=True).splitlines())
assert len(paths) == 90
rows = []
for path in paths:
    before, after = read(BASE, path), read(AFTER, path)
    old, new = before["ranking"], after["ranking"]
    assert old == new[:len(old)], path
    assert len(old) == 5 and len(new) == after["candidate_count"], path
    assert {k: v for k, v in before.items() if k != "ranking"} == {
        k: v for k, v in after.items() if k != "ranking"}, path
    native_before = [r["service"] for r in old]
    native_after = [r["service"] for r in new]
    filtered_before = [s for s in native_before if s in ALLOW]
    filtered_after = [s for s in native_after if s in ALLOW]
    assert len(filtered_after) == 11, path
    rows.append({
        "case_id": after["case_id"], "native_before": native_before,
        "native_after": native_after, "e3_filtered_before": filtered_before,
        "e3_filtered_after": filtered_after,
        "filtered_top5_before": filtered_before[:5],
        "filtered_top5_after": filtered_after[:5],
        "filtered_top5_changed": filtered_before[:5] != filtered_after[:5],
        "saved_prefix_identical": True, "before_rows_unchanged": True,
        "before_rows": old, "after_rows": new,
    })
summary = {
    "case_count": len(rows), "saved_prefix_identical_cases": len(rows),
    "before_rows_unchanged_cases": len(rows),
    "filtered_top5_changed_cases": sum(r["filtered_top5_changed"] for r in rows),
    "native_after_length_counts": dict(Counter(len(r["native_after"]) for r in rows)),
    "e3_filtered_before_length_counts": dict(Counter(len(r["e3_filtered_before"]) for r in rows)),
    "e3_filtered_after_length_counts": dict(Counter(len(r["e3_filtered_after"]) for r in rows)),
    "ground_truth_read": False, "accuracy_metrics_computed": False,
}
payload = {"before_revision": BASE, "after_revision": AFTER,
           "exact_command": ".venv/bin/python scripts/phase_a_e5_rank_comparison.py",
           "summary": summary, "cases": rows}
(OUT / "e5_rank_comparison.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
lines = ["# E5 before/after rank comparison", "",
         "No ground-truth labels are read and no accuracy metrics are computed.", "",
         "| Case | Native before (5) | E3 before | E3 after (complete) | Top 5 changed |",
         "|---|---|---|---|---|"]
for r in rows:
    lines.append("| " + " | ".join([r["case_id"], ", ".join(r["native_before"]),
        ", ".join(r["e3_filtered_before"]), ", ".join(r["e3_filtered_after"]),
        str(r["filtered_top5_changed"])]) + " |")
(OUT / "E5_RANK_COMPARISON.md").write_text("\n".join(lines) + "\n")
print(json.dumps(summary, indent=2, sort_keys=True))
