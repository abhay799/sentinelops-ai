from __future__ import annotations

import argparse
import json
import multiprocessing
import platform
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import polars as pl

from sentinelops.evaluation.rcaeval_baselines import (
    static_threshold_ranking,
)

ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ob")
CASE_OUT = OUT / "threshold_cases"


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


def run_case(case_id: str) -> dict[str, object]:
    started = time.perf_counter()
    try:
        case = ROOT / case_id
        metrics = pl.read_parquet(case / "metrics.parquet")
        inject = int(
            (case / "inject_time.txt")
            .read_text()
            .strip()
        )
        ranking = static_threshold_ranking(
            metrics,
            inject_time_s=inject,
            threshold=2.5,
        )
        payload: dict[str, object] = {
            "status": "ok",
            "case_id": case_id,
            "candidate_count": len(ranking),
            "ranking": ranking,
            "ground_truth_used_for_ranking": False,
        }
    except Exception as exc:
        payload = {
            "status": "failed",
            "case_id": case_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    payload["runtime_seconds"] = (
        time.perf_counter() - started
    )
    return payload
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
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    started = time.perf_counter()
    ids = case_ids()
    CASE_OUT.mkdir(parents=True, exist_ok=True)

    existing: dict[str, dict[str, object]] = {}
    pending: list[str] = []
    for case_id in ids:
        path = CASE_OUT / f"{case_id}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            if cached.get("status") == "ok":
                existing[case_id] = cached
            else:
                pending.append(case_id)
        else:
            pending.append(case_id)
    if pending:
        with ProcessPoolExecutor(
            max_workers=args.workers,
            mp_context=multiprocessing.get_context("spawn"),
        ) as pool:
            futures = {
                pool.submit(run_case, case_id): case_id
                for case_id in pending
            }
            for future in as_completed(futures):
                payload = future.result()
                write_json(
                    CASE_OUT / f"{payload['case_id']}.json",
                    payload,
                )
                existing[str(payload["case_id"])] = payload
                print(
                    "threshold",
                    payload["case_id"],
                    payload["status"],
                    flush=True,
                )

    ordered = [existing[case_id] for case_id in ids]
    failed = [
        payload
        for payload in ordered
        if payload["status"] != "ok"
    ]
    summary = {
        "step": 17,
        "status": "complete" if not failed else "completed_with_failures",
        "execution_date": "2026-10-02",
        "exact_command":
            "python scripts/phase_a_step17_threshold.py --workers 4",
        "sentinelops_commit": git_head(),
        "rcaeval_revision":
            "259ea4167160256a74ad30004aa3d96a998c846e",
        "dataset_revision":
            "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e",
        "python": platform.python_version(),
        "case_count_expected": len(ids),
        "case_count_ok": len(ids) - len(failed),
        "case_count_failed": len(failed),
        "failed_cases": failed,
        "threshold": 2.5,
        "ranking_rule":
            "max post-calibration metric z-score per service",
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(OUT / "step17_threshold_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
