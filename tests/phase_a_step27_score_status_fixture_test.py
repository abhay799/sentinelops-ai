from __future__ import annotations

import json

import numpy as np

from scripts.phase_a_step27_score import case_hits


def test_non_ok_statuses_are_zero_and_valid_count_is_ok_count(tmp_path):
    truth = "svc-a"
    statuses = [
        "ok",
        "fallback_unranked",
        "timeout_unranked",
        "hard_failed",
        "unknown_status",
    ]
    paths = []
    for idx, status in enumerate(statuses):
        path = tmp_path / f"case_{idx}.json"
        path.write_text(
            json.dumps(
                {
                    "case_id": f"case_{idx}",
                    "status": status,
                    "e3_filtered_service_ranking": [truth, "svc-b"],
                }
            )
        )
        paths.append(path)

    rows = [json.loads(path.read_text()) for path in paths]
    hit_vectors = [
        case_hits(row["e3_filtered_service_ranking"], truth, row["status"])
        for row in rows
    ]

    assert np.array_equal(hit_vectors[0], np.ones(5, dtype=float))
    for vector in hit_vectors[1:]:
        assert np.array_equal(vector, np.zeros(5, dtype=float))

    valid_only_count = sum(row["status"] == "ok" for row in rows)
    assert valid_only_count == 1
    assert valid_only_count == sum(status == "ok" for status in statuses)
