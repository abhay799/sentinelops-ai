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

from sentinelops.evaluation.rcaeval_adapter import (
    derive_pre_injection_topology,
    load_rcaeval_traces,
    metric_services_from_columns,
)
from sentinelops.evaluation.rcaeval_rca import (
    graph_from_edges,
    sentinelops_continuous_ranking,
)

ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ob")
TOPO_OUT = OUT / "topology_cases"
RCA_OUT = OUT / "rca_cases"
def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()


def case_ids() -> list[str]:
    frame = pl.read_parquet(ROOT / "cases.parquet")
    return (
        frame.filter(pl.col("dataset") == "RE2-OB")
        .sort("case")["case"]
        .to_list()
    )


def topology_case(case_id: str) -> dict[str, object]:
    started = time.perf_counter()
    try:
        case = ROOT / case_id
        metrics = pl.read_parquet(case / "metrics.parquet")
        traces = load_rcaeval_traces(
            case / "traces.parquet"
        )
        inject = int((case / "inject_time.txt").read_text().strip())
        result = derive_pre_injection_topology(
            metrics, traces, inject
        )
        payload: dict[str, object] = {
            "status": "ok",
            "case_id": case_id,
            "metric_services": sorted(
                metric_services_from_columns(metrics.columns)
            ),
            "edges": [list(edge) for edge in result.edges],
            "unresolved_parent_count": result.unresolved_parent_count,
            "metric_only_services": list(result.metric_only_services),
            "service_mapping": [list(row) for row in result.service_mapping],
            "trace_duplicates": {
                "duplicate_key_count":
                    result.trace_duplicate_stats.duplicate_key_count,
                "duplicate_row_count":
                    result.trace_duplicate_stats.duplicate_row_count,
                "removed_row_count":
                    result.trace_duplicate_stats.removed_row_count,
                "conflicting_duplicate_found":
                    result.trace_duplicate_stats.conflicting_duplicate_found,
            },
        }
    except Exception as exc:
        payload = {
            "status": "failed",
            "case_id": case_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    payload["runtime_seconds"] = time.perf_counter() - started
    return payload
def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    started = time.perf_counter()
    ids = case_ids()
    TOPO_OUT.mkdir(parents=True, exist_ok=True)

    existing: dict[str, dict[str, object]] = {}
    pending: list[str] = []
    for case_id in ids:
        path = TOPO_OUT / f"{case_id}.json"
        if path.exists():
            existing[case_id] = json.loads(path.read_text())
        else:
            pending.append(case_id)

    if pending:
        with ProcessPoolExecutor(
            max_workers=args.workers,
            mp_context=multiprocessing.get_context("spawn"),
        ) as pool:
            futures = {
                pool.submit(topology_case, case_id): case_id
                for case_id in pending
            }
            for future in as_completed(futures):
                payload = future.result()
                write_json(
                    TOPO_OUT / f"{payload['case_id']}.json",
                    payload,
                )
                existing[str(payload["case_id"])] = payload
                print(
                    "topology",
                    payload["case_id"],
                    payload["status"],
                    flush=True,
                )
    ordered = [existing[case_id] for case_id in ids]
    failed_topology = [
        payload for payload in ordered
        if payload["status"] != "ok"
    ]
    duplicate_affected = [
        {
            "case_id": str(payload["case_id"]),
            **dict(payload["trace_duplicates"]),
        }
        for payload in ordered
        if payload["status"] == "ok"
        and int(
            dict(payload["trace_duplicates"])[
                "duplicate_key_count"
            ]
        ) > 0
    ]
    if failed_topology:
        summary = {
            "step": 16,
            "status": "failed_topology",
            "execution_date": "2026-10-02",
            "exact_command":
                "python scripts/phase_a_step16_rca.py --workers 2",
            "sentinelops_commit": git_head(),
            "rcaeval_revision":
                "259ea4167160256a74ad30004aa3d96a998c846e",
            "dataset_revision":
                "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e",
            "python": platform.python_version(),
            "case_count_expected": len(ids),
            "case_count_topology_ok":
                len(ids) - len(failed_topology),
            "case_count_topology_failed": len(failed_topology),
            "failed_topology_cases": failed_topology,
            "duplicate_affected_cases": duplicate_affected,
            "trace_duplicate_policy":
                "exact full-row duplicates cleaned; conflicts fail",
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(OUT / "step16_rca_summary.json", summary)
        print(json.dumps(summary, indent=2))
        raise SystemExit(2)

    services: set[str] = set()
    edges: set[tuple[str, str]] = set()
    unresolved = 0
    for payload in ordered:
        services.update(payload["metric_services"])
        edges.update(
            (str(source), str(target))
            for source, target in payload["edges"]
        )
        unresolved += int(payload["unresolved_parent_count"])

    graph = graph_from_edges(services, edges)
    graph_payload = {
        "source": "union of all RE2-OB pre-injection traces",
        "nodes": graph.services(),
        "edges": [list(edge) for edge in sorted(edges)],
        "node_count": len(graph.services()),
        "edge_count": len(edges),
        "unresolved_parent_count_total": unresolved,
    }
    write_json(OUT / "re2ob_suite_graph.json", graph_payload)
    RCA_OUT.mkdir(parents=True, exist_ok=True)
    failed_detection: list[dict[str, object]] = []
    ranked = 0

    for case_id in ids:
        detection_path = OUT / "detection_cases" / f"{case_id}.json"
        if not detection_path.exists():
            failed_detection.append(
                {"case_id": case_id, "error": "missing detection result"}
            )
            continue
        detection = json.loads(detection_path.read_text())
        if detection["status"] != "ok":
            failed_detection.append(
                {
                    "case_id": case_id,
                    "error": detection.get("error", "detection failed"),
                }
            )
            continue

        strengths = {
            service: float(values["fault_max_anomaly_strength"])
            for service, values in detection["per_service"].items()
        }
        ranking = sentinelops_continuous_ranking(
            strengths,
            graph,
            max_candidates=5,
        )
        payload = {
            "status": "ok",
            "case_id": case_id,
            "candidate_count": len(strengths),
            "ranking": ranking,
            "ground_truth_used_for_ranking": False,
            "change_signal": 0.0,
        }
        write_json(RCA_OUT / f"{case_id}.json", payload)
        ranked += 1
    summary = {
        "step": 16,
        "status": (
            "complete"
            if not failed_detection
            else "completed_with_failures"
        ),
        "execution_date": "2026-10-02",
        "exact_command":
            "python scripts/phase_a_step16_rca.py --workers 2",
        "sentinelops_commit": git_head(),
        "rcaeval_revision":
            "259ea4167160256a74ad30004aa3d96a998c846e",
        "dataset_revision":
            "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e",
        "python": platform.python_version(),
        "case_count_expected": len(ids),
        "ranked_cases": ranked,
        "failed_detection_cases": failed_detection,
        "duplicate_affected_cases": duplicate_affected,
        "trace_duplicate_policy":
            "exact full-row duplicates cleaned; conflicts fail",
        "suite_graph": graph_payload,
        "weights": {
            "anomaly_strength": 0.45,
            "change_signal": 0.25,
            "graph_impact": 0.20,
            "primary_service_bonus": 0.10,
        },
        "ranking_signal":
            "max fault-window continuous v1 anomaly strength per service",
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(OUT / "step16_rca_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
