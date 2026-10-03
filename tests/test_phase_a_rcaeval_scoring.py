import numpy as np
import pytest

from sentinelops.evaluation.rcaeval_scoring import (
    a4_sentinelops_ranking,
    case_hits,
    metric_values,
    paired_intervals,
    percentile_intervals,
    summarize_group,
)


def test_e3_filter_precedes_top_k_and_rejects_duplicate_services():
    ranking = ["mesh", "b", "a", "c"]
    assert case_hits(ranking, "a", {"a", "b", "c"}).tolist() == [0, 1, 1, 1, 1]
    with pytest.raises(ValueError, match="duplicate"):
        case_hits(["a", "a"], "a", {"a", "b"})


def test_fallback_is_a_miss_even_if_returned_order_contains_answer():
    assert case_hits(["a"], "a", {"a"}, status="fallback_unranked").tolist() == [0] * 5
    with pytest.raises(ValueError, match="status"):
        case_hits([], "a", {"a"}, status="failed")


def test_avg5_uses_all_cutoffs_and_lift5_is_ratio():
    values = metric_values(np.array([[0, 0, 1, 1, 1], [0, 0, 0, 0, 0]]), 5 / 11)
    assert values["AC@1"] == 0
    assert values["AC@3"] == 0.5
    assert values["AC@5"] == 0.5
    assert values["Avg@5"] == pytest.approx(0.3)
    assert values["Chance@5"] == pytest.approx(5 / 11)
    assert values["Lift@5"] == pytest.approx(1.1)


def test_paired_identical_methods_have_zero_uncertainty_with_variable_hits():
    hits = np.array([[1, 1, 1, 1, 1], [0, 0, 0, 0, 0]])
    indices = np.array([[0, 0], [0, 1], [1, 1]])
    assert percentile_intervals(hits, indices, 5 / 11)["AC@1"] == pytest.approx([0.025, 0.975])
    assert paired_intervals(hits, hits, indices)["AC@1"] == {"difference": 0.0, "ci95": [0.0, 0.0]}


def test_paired_differences_share_case_indices_and_direction():
    left = np.array([[1] * 5, [0] * 5])
    right = np.array([[0] * 5, [1] * 5])
    indices = np.array([[0, 0], [0, 1], [1, 1]])
    row = paired_intervals(left, right, indices)["AC@5"]
    assert row["difference"] == 0
    assert row["ci95"] == pytest.approx([-0.95, 0.95])


def test_valid_only_denominator_does_not_replace_primary_and_zero_valid_is_null():
    hits = {"SentinelOps": np.array([[1] * 5, [1] * 5]), "base": np.array([[1] * 5, [0] * 5])}
    valid = {"SentinelOps": np.array([True, True]), "base": np.array([True, False])}
    group = summarize_group(hits, valid, 5 / 11)
    assert group["primary"]["base"]["denominator"] == 2
    assert group["primary"]["base"]["metrics"]["AC@1"] == 0.5
    assert group["valid_rankings_only"]["base"]["denominator"] == 1
    assert group["valid_rankings_only"]["base"]["metrics"]["AC@1"] == 1
    group = summarize_group(
        hits, {"SentinelOps": valid["SentinelOps"], "base": np.array([False, False])}, 5 / 11
    )
    assert group["valid_rankings_only"]["base"]["denominator"] == 0
    assert group["valid_rankings_only"]["base"]["metrics"]["AC@1"] is None


def test_a4_preserves_native_strengths_and_original_excluded_primary_bonus():
    rows = [
        {
            "service": "mesh",
            "anomaly_strength": 1.0,
            "change_signal": 0.0,
            "primary_service_bonus": 1.0,
        },
        {
            "service": "a",
            "anomaly_strength": 1.0,
            "change_signal": 0.0,
            "primary_service_bonus": 0.0,
        },
        {
            "service": "b",
            "anomaly_strength": 1.0,
            "change_signal": 0.0,
            "primary_service_bonus": 0.0,
        },
    ]
    out = a4_sentinelops_ranking(rows, {"a", "b"}, [("a", "b")])
    by_service = {r["service"]: r for r in out}
    assert by_service["mesh"]["rca_score"] == pytest.approx(0.55)
    assert by_service["b"]["rca_score"] == pytest.approx(0.65)
    assert by_service["a"]["rca_score"] == pytest.approx(0.45)
    assert by_service["b"]["primary_service_bonus"] == 0


def test_pinned_evaluator_uses_its_dependency_environment():
    import importlib.util
    from pathlib import Path

    root = Path("/home/dell/benchmarks/RCAEval")
    if not (root / ".venv/bin/python").exists():
        pytest.skip("Requires the pinned local RCAEval dependency environment")
    path = Path(__file__).resolve().parents[1] / "scripts/phase_a_steps21_24.py"
    spec = importlib.util.spec_from_file_location("phase_a_scoring_driver", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    methods = (*module.METHODS, "A4_SentinelOps", "A4_PageRank")
    cases = [
        {
            "root_cause_service": "checkoutservice",
            "methods": {
                m: {
                    "native_service_ranking": ["checkoutservice"],
                    "status": "ok",
                }
                for m in methods
            },
        }
    ]
    result = module.pinned_check(cases)
    assert result["service_AC@1_to_5_and_Avg@5_match"] is True
    assert result["methods_checked"] == 10
