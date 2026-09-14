from pathlib import Path

import polars as pl

from sentinelops.investigation.agents import (
    challenger_agent,
    investigator_agent,
)

from sentinelops.investigation.evidence import (
    build_evidence_bundle,
)

from sentinelops.investigation.rag import (
    RunbookRetriever,
)


def empty():
    return pl.DataFrame()


def test_agent_cannot_confirm_rca():

    evidence = {
        "incident_id":
            "INC-1",

        "evidence_source_count":
            1,

        "rca": [
            {
                "rank":
                    1,

                "candidate_service":
                    "payment-service",

                "causal_consistency_score":
                    0.9,

                "final_disposition":
                    "supported_candidate",
            }
        ],
    }

    result = investigator_agent(
        evidence,
        [],
    )

    assert (
        result[
            "root_cause_status"
        ]
        == "not_confirmed_by_agent"
    )

    assert not result[
        "execution_authority"
    ]


def test_challenger_never_confirms_rca():

    evidence = {
        "rca": [
            {
                "candidate_service":
                    "payment-service",

                "final_disposition":
                    "supported_candidate",
            }
        ]
    }

    result = challenger_agent(
        evidence
    )

    assert not result[
        "root_cause_confirmed"
    ]


def test_evidence_bundle_disables_agent_execution():

    incident = pl.DataFrame(
        [
            {
                "incident_id":
                    "INC-1"
            }
        ]
    )

    bundle = build_evidence_bundle(
        incident_id="INC-1",
        incident_intelligence=incident,
        rca_disposition=empty(),
        incident_priority=empty(),
        counterfactual_summary=empty(),
        remediation_audit=empty(),
        execution_results=empty(),
        recovery_verification=empty(),
    )

    assert not bundle[
        "agent_can_execute"
    ]

    assert not bundle[
        "agent_can_confirm_root_cause"
    ]


def test_rag_retrieves_runbook():

    corpus = Path(
        "docs/runbooks"
    )

    retriever = RunbookRetriever(
        corpus
    )

    results = retriever.retrieve(
        "payment service rollback "
        "SentinelGuard recovery",
        top_k=3,
    )

    assert len(results) > 0

    assert all(
        row["source"]
        for row in results
    )
