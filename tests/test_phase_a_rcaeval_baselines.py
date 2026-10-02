import polars as pl

from sentinelops.evaluation.rcaeval_baselines import (
    deterministic_random_ranking,
    pagerank_ranking,
    static_threshold_ranking,
)


def test_static_threshold_ranking_uses_calibration_only_and_lexical_ties():
    metrics = pl.DataFrame(
        {
            "time": [1, 2, 3, 4, 5, 6],
            "a_cpu": [0.0, 1.0, 1.0, 2.0, 2.0, 2.0],
            "b_cpu": [0.0, 1.0, 1.0, 10.0, 10.0, 10.0],
            "c_cpu": [0.0, 1.0, 1.0, 2.0, 2.0, 2.0],
        }
    )

    ranking = static_threshold_ranking(
        metrics,
        inject_time_s=5,
        threshold=2.5,
    )

    assert ranking[0]["service"] == "b"
    assert ranking[1]["service"] == "a"
    assert ranking[2]["service"] == "c"


def test_deterministic_random_ranking_is_stable_and_lexical_before_shuffle():
    first, first_seed = deterministic_random_ranking(
        ["c", "a", "b"],
        case_id="case-1",
        master_seed=42,
    )
    second, second_seed = deterministic_random_ranking(
        ["b", "c", "a"],
        case_id="case-1",
        master_seed=42,
    )

    assert first_seed == second_seed
    assert first == second
    assert sorted(row["service"] for row in first) == [
        "a",
        "b",
        "c",
    ]
    assert [row["rank"] for row in first] == [1, 2, 3]


def test_pagerank_ranking_uses_strength_personalization():
    ranking = pagerank_ranking(
        services=["a", "b", "c"],
        edges=[],
        service_strengths={
            "a": 1.0,
            "b": 0.0,
            "c": 0.0,
        },
        damping=0.85,
    )

    assert ranking[0]["service"] == "a"
    assert ranking[0]["score"] > ranking[1]["score"]


def test_pagerank_zero_strengths_uses_uniform_lexical_ties():
    ranking = pagerank_ranking(
        services=["c", "a", "b"],
        edges=[],
        service_strengths={
            "a": 0.0,
            "b": 0.0,
            "c": 0.0,
        },
        damping=0.85,
    )

    assert [row["service"] for row in ranking] == [
        "a",
        "b",
        "c",
    ]
