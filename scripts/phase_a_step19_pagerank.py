from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from pathlib import Path

import polars as pl

from sentinelops.evaluation.rcaeval_baselines import (
    pagerank_ranking,
)

ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ob")
DETECTION_CASES = OUT / "detection_cases"
CASE_OUT = OUT / "pagerank_cases"
GRAPH_PATH = OUT / "re2ob_suite_graph.json"
DAMPING = 0.85


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()
def case_ids() -> list[str]:
    frame = pl.read_parquet(ROOT / "cases.parquet")
    return (
        frame.filter(pl.col("dataset") == "RE2-OB")
        .sort("case")["case"]
        .to_list()
    )


def write_json(
    path: Path,
    payload: dict[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True)
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    started = time.perf_counter()
    ids = case_ids()
    graph_payload = json.loads(GRAPH_PATH.read_text())
    edges = [
        (str(source), str(target))
        for source, target in graph_payload["edges"]
    ]
    CASE_OUT.mkdir(parents=True, exist_ok=True)
    failed: list[dict[str, object]] = []
    completed = 0
    for case_id in ids:
        path = CASE_OUT / f"{case_id}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            if cached.get("status") == "ok":
                completed += 1
                continue

        try:
            detection = json.loads(
                (
                    DETECTION_CASES
                    / f"{case_id}.json"
                ).read_text()
            )
            if detection["status"] != "ok":
                raise ValueError(
                    "Detection candidate source failed"
                )
            strengths = {
                str(service): float(
                    values["fault_max_anomaly_strength"]
                )
                for service, values
                in detection["per_service"].items()
            }
            ranking = pagerank_ranking(
                services=strengths,
                edges=edges,
                service_strengths=strengths,
                damping=DAMPING,
            )
            payload: dict[str, object] = {
                "status": "ok",
                "case_id": case_id,
                "candidate_count": len(strengths),
                "damping": DAMPING,
                "personalization_source":
                    "continuous v1 fault-window anomaly strength",
                "ranking": ranking,
                "ground_truth_used_for_ranking": False,
            }
            completed += 1
        except Exception as exc:
            payload = {
                "status": "failed",
                "case_id": case_id,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            failed.append(payload)

        write_json(path, payload)
    summary = {
        "step": 19,
        "status":
            "complete"
            if not failed
            else "completed_with_failures",
        "execution_date": "2026-10-02",
        "exact_command":
            "python scripts/phase_a_step19_pagerank.py",
        "sentinelops_commit": git_head(),
        "rcaeval_revision":
            "259ea4167160256a74ad30004aa3d96a998c846e",
        "dataset_revision":
            "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e",
        "python": platform.python_version(),
        "case_count_expected": len(ids),
        "case_count_ok": completed,
        "case_count_failed": len(failed),
        "failed_cases": failed,
        "damping": DAMPING,
        "graph_source":
            "union of all RE2-OB pre-injection traces",
        "personalization":
            "continuous v1 fault-window anomaly strength",
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(OUT / "step19_pagerank_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
