import polars as pl

from sentinelops.rca.validation import (
    validate_rca_hypotheses,
)


def valid_fixture():
    return pl.DataFrame(
        [
            {
                "hypothesis_id":
                    "H-1",

                "incident_id":
                    "INC-0001",

                "candidate_service":
                    "payment-service",

                "rank":
                    1,

                "rca_score":
                    0.8,

                "confidence":
                    "high",

                "evidence_count":
                    2,

                "evidence":
                    [
                        {
                            "type":
                                "anomaly",
                            "service":
                                "payment-service",
                            "value":
                                0.95,
                            "description":
                                "anomaly",
                        },
                        {
                            "type":
                                "correlation",
                            "service":
                                "payment-service",
                            "value":
                                1.0,
                            "description":
                                "correlation",
                        },
                    ],

                "confirmed_root_cause":
                    False,

                "requires_challenger":
                    True,

                "requires_human_confirmation":
                    True,
            }
        ]
    )


def test_valid_rca_passes():
    errors = validate_rca_hypotheses(
        valid_fixture()
    )

    assert errors == []


def test_auto_confirmed_rca_fails():
    data = valid_fixture().with_columns(
        pl.lit(True).alias(
            "confirmed_root_cause"
        )
    )

    errors = validate_rca_hypotheses(
        data
    )

    assert any(
        "prematurely confirmed"
        in error
        for error in errors
    )


def test_missing_challenger_fails():
    data = valid_fixture().with_columns(
        pl.lit(False).alias(
            "requires_challenger"
        )
    )

    errors = validate_rca_hypotheses(
        data
    )

    assert any(
        "challenger"
        in error
        for error in errors
    )
