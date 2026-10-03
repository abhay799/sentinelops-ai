from __future__ import annotations

import argparse
import json
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import polars as pl

from sentinelops.evaluation.rcaeval_adapter import (
    derive_pre_injection_topology,
    load_rcaeval_traces,
    metric_services_from_columns,
)
from sentinelops.evaluation.rcaeval_rca import graph_from_edges

ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2tt")
TOPO_OUT = OUT / "topology_cases"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def case_ids() -> list[str]:
    frame = pl.read_parquet(ROOT / "cases.parquet")
    ids = (
        frame.filter(pl.col("dataset") == "RE2-TT")
        .sort("case")["case"]
        .to_list()
    )
    if len(ids) != 90:
        raise RuntimeError(f"Expected 90 RE2-TT cases, found {len(ids)}")
    return [str(x) for x in ids]


def topology_case(case_id: str) -> dict[str, object]:
    started = time.perf_counter()
    try:
        case = ROOT / case_id
        metrics = pl.read_parquet(case / "metrics.parquet")
        traces = load_rcaeval_traces(case / "traces.parquet")
        inject = int((case / "inject_time.txt").read_text().strip())
        result = derive_pre_injection_topology(metrics, traces, inject)
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
                "duplicate_key_count": (
                    result.trace_duplicate_stats.duplicate_key_count
                ),
                "duplicate_row_count": (
                    result.trace_duplicate_stats.duplicate_row_count
                ),
                "removed_row_count": (
                    result.trace_duplicate_stats.removed_row_count
                ),
                "conflicting_duplicate_found": (
                    result.trace_duplicate_stats.conflicting_duplicate_found
                ),
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
            cached = json.loads(path.read_text())
            if (
                cached.get("status") == "ok"
                and "trace_duplicates" in cached
            ):
                existing[case_id] = cached
                continue
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
    failed = [row for row in ordered if row["status"] != "ok"]
    if failed:
        write_json(
            OUT / "step27_topology_summary.json",
            {
                "status": "failed_topology",
                "case_count_expected": 90,
                "case_count_failed": len(failed),
                "failed_cases": failed,
            },
        )
        raise SystemExit(2)

    services: set[str] = set()
    edges: set[tuple[str, str]] = set()
    unresolved = 0
    duplicate_affected: list[dict[str, object]] = []
    for row in ordered:
        services.update(str(x) for x in row["metric_services"])
        edges.update(
            (str(source), str(target))
            for source, target in row["edges"]
        )
        unresolved += int(row["unresolved_parent_count"])
        stats = dict(row["trace_duplicates"])
        if int(stats["duplicate_key_count"]) > 0:
            duplicate_affected.append(
                {"case_id": row["case_id"], **stats}
            )

    graph = graph_from_edges(services, edges)
    graph_payload = {
        "source": "union of all RE2-TT pre-injection traces",
        "nodes": graph.services(),
        "edges": [list(edge) for edge in sorted(edges)],
        "node_count": len(graph.services()),
        "edge_count": len(edges),
        "unresolved_parent_count_total": unresolved,
    }
    write_json(OUT / "re2tt_suite_graph.json", graph_payload)
    write_json(
        OUT / "step27_topology_summary.json",
        {
            "status": "complete",
            "case_count_expected": 90,
            "case_count_ok": 90,
            "duplicate_affected_cases": duplicate_affected,
            "trace_duplicate_policy": (
                "exact full-row duplicates cleaned; conflicts fail"
            ),
            "graph": graph_payload,
            "runtime_seconds": time.perf_counter() - started,
            "ground_truth_used": False,
        },
    )
    print(json.dumps(graph_payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
