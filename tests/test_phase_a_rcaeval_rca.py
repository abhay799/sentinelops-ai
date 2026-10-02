import pytest

from sentinelops.evaluation.rcaeval_rca import (
    graph_from_edges,
    sentinelops_continuous_ranking,
)


def test_sentinelops_rca_uses_frozen_weights_and_continuous_strength():
    graph = graph_from_edges(
        ["frontend", "checkout", "payment"],
        [
            ("frontend", "checkout"),
            ("checkout", "payment"),
        ],
    )
    ranking = sentinelops_continuous_ranking(
        {
            "frontend": 0.20,
            "checkout": 0.60,
            "payment": 0.90,
        },
        graph,
        max_candidates=3,
    )

    assert ranking[0]["service"] == "payment"
    assert ranking[0]["anomaly_strength"] == pytest.approx(0.90)
    assert ranking[0]["change_signal"] == 0.0
    assert ranking[0]["graph_impact"] == pytest.approx(1.0)
    assert ranking[0]["primary_service_bonus"] == 1.0
    assert ranking[0]["rca_score"] == pytest.approx(0.705)


def test_sentinelops_rca_ties_are_lexical_after_score():
    graph = graph_from_edges(["a", "b"], [])
    ranking = sentinelops_continuous_ranking(
        {"a": 0.5, "b": 0.5},
        graph,
        max_candidates=2,
    )
    assert [row["service"] for row in ranking] == ["b", "a"]
    assert ranking[0]["primary_service_bonus"] == 1.0


def test_rca_rejects_missing_graph_service():
    graph = graph_from_edges(["a"], [])
    with pytest.raises(ValueError, match="missing services"):
        sentinelops_continuous_ranking(
            {"a": 0.2, "b": 0.5},
            graph,
        )
