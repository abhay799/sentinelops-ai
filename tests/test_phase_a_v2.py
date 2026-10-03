from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from sentinelops.evaluation.rcaeval_rca import (
    graph_from_edges,
    sentinelops_continuous_ranking,
)
from sentinelops.evaluation.rcaeval_v2 import (
    V2Strengths,
    normalize_unclipped_from_calibration,
    sentinelops_v2_ranking,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/phase_a/re2ob"


def test_v2_unclipped_normalization_retains_extremes() -> None:
    scores = np.array([0.0, 1.0, 2.0, -1.0])
    got = normalize_unclipped_from_calibration(scores, 2)
    assert np.array_equal(got, np.array([0.0, 1.0, 2.0, -1.0]))


def test_v2_constant_range_uses_binary_guard() -> None:
    scores = np.array([2.0, 2.0, 2.0, 3.0])
    got = normalize_unclipped_from_calibration(scores, 2)
    assert np.array_equal(got, np.array([0.0, 0.0, 0.0, 1.0]))


def test_v2b_primary_bonus_uses_raw_strength_not_name() -> None:
    graph = graph_from_edges(["a", "z"], [])
    strengths = V2Strengths(
        clipped={"a": 1.0, "z": 1.0},
        unclipped={"a": 4.0, "z": 2.0},
    )
    _rows, primary = sentinelops_v2_ranking(strengths, graph, "v2b")
    assert primary == "a"


def test_v2b_exact_raw_tie_assigns_no_primary_bonus() -> None:
    graph = graph_from_edges(["a", "z"], [])
    strengths = V2Strengths(
        clipped={"a": 1.0, "z": 1.0},
        unclipped={"a": 4.0, "z": 4.0},
    )
    rows, primary = sentinelops_v2_ranking(strengths, graph, "v2b")
    assert primary is None
    assert all(row["primary_service_bonus"] == 0.0 for row in rows)


def test_v1_rca_outputs_are_byte_identical_to_frozen_evidence() -> None:
    graph_payload = json.loads((OUT / "re2ob_suite_graph.json").read_text())
    graph = graph_from_edges(
        graph_payload["nodes"],
        [(str(a), str(b)) for a, b in graph_payload["edges"]],
    )
    frozen_files = sorted((OUT / "rca_cases").glob("*.json"))
    assert len(frozen_files) == 90

    for frozen_path in frozen_files:
        case_id = frozen_path.stem
        detection = json.loads(
            (OUT / "detection_cases" / f"{case_id}.json").read_text()
        )
        strengths = {
            service: float(values["fault_max_anomaly_strength"])
            for service, values in detection["per_service"].items()
        }
        ranking = sentinelops_continuous_ranking(
            strengths,
            graph,
            max_candidates=len(strengths),
        )
        payload = {
            "status": "ok",
            "case_id": case_id,
            "candidate_count": len(strengths),
            "ranking": ranking,
            "ground_truth_used_for_ranking": False,
            "change_signal": 0.0,
        }
        regenerated = (
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        ).encode()
        assert regenerated == frozen_path.read_bytes(), case_id
