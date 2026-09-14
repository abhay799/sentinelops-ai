import json
from pathlib import Path

import polars as pl
import yaml

from sentinelops.investigation.agents import (
    challenger_agent,
    investigator_agent,
    remediation_agent,
    verifier_agent,
)

from sentinelops.investigation.evidence import (
    build_evidence_bundle,
)

from sentinelops.investigation.rag import (
    RunbookRetriever,
)


with open(
    "configs/investigation.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "investigation"
    ]


INCIDENTS = pl.read_parquet(
    "data/processed/incidents/"
    "incident_intelligence_v1.parquet"
)

RCA = pl.read_parquet(
    "data/processed/rca/"
    "rca_disposition_v1.parquet"
)

PRIORITY = pl.read_parquet(
    "data/processed/impact/"
    "incident_priority_v1.parquet"
)

COUNTERFACTUAL = pl.read_parquet(
    "data/processed/counterfactual/"
    "counterfactual_summary_v1.parquet"
)

REMEDIATION = pl.read_parquet(
    "data/processed/remediation/"
    "remediation_audit_v1.parquet"
)

EXECUTION = pl.read_parquet(
    "data/processed/execution/"
    "execution_results_v1.parquet"
)

VERIFICATION = pl.read_parquet(
    "data/processed/execution/"
    "recovery_verification_v1.parquet"
)


incident_id = (
    PRIORITY
    .sort(
        "priority_rank"
    )
    [
        "incident_id"
    ][0]
)


evidence = build_evidence_bundle(
    incident_id=incident_id,

    incident_intelligence=INCIDENTS,

    rca_disposition=RCA,

    incident_priority=PRIORITY,

    counterfactual_summary=COUNTERFACTUAL,

    remediation_audit=REMEDIATION,

    execution_results=EXECUTION,

    recovery_verification=VERIFICATION,
)


if (
    evidence[
        "evidence_source_count"
    ]
    == 0
):

    raise RuntimeError(
        "Investigation has no evidence"
    )


retriever = RunbookRetriever(
    config[
        "rag"
    ][
        "corpus_path"
    ]
)


query = (
    f"Investigate incident {incident_id}. "
    "Determine evidence-based RCA, safe remediation, "
    "SentinelGuard requirements and recovery verification."
)


retrieved = retriever.retrieve(
    query=query,

    top_k=int(
        config[
            "rag"
        ][
            "top_k"
        ]
    ),

    minimum_similarity=float(
        config[
            "rag"
        ][
            "minimum_similarity"
        ]
    ),
)


report = {
    "incident_id":
        incident_id,

    "investigator":
        investigator_agent(
            evidence,
            retrieved,
        ),

    "challenger":
        challenger_agent(
            evidence
        ),

    "remediation":
        remediation_agent(
            evidence
        ),

    "verifier":
        verifier_agent(
            evidence
        ),

    "retrieved_sources":
        [
            {
                "source":
                    row["source"],

                "similarity":
                    row["similarity"],
            }
            for row in retrieved
        ],

    "safety": {
        "root_cause_confirmed_by_agent":
            False,

        "agent_execution_authority":
            False,

        "sentinelguard_bypass_allowed":
            False,

        "human_approval_bypass_allowed":
            False,
    },
}


output = config[
    "output"
]


evidence_path = Path(
    output[
        "evidence"
    ][
        "path"
    ]
)

retrieval_path = Path(
    output[
        "retrieval"
    ][
        "path"
    ]
)

report_path = Path(
    output[
        "report"
    ][
        "path"
    ]
)


evidence_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)


evidence_path.write_text(
    json.dumps(
        evidence,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)


retrieval_path.write_text(
    json.dumps(
        retrieved,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)


report_path.write_text(
    json.dumps(
        report,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)


print()
print("=" * 80)
print(
    " SENTINELOPS AI - PHASE 15 GROUNDED INVESTIGATION"
)
print("=" * 80)

print(
    "Incident:",
    incident_id,
)

print(
    "Evidence sources:",
    evidence[
        "evidence_source_count"
    ],
)

print(
    "Retrieved runbooks:",
    len(
        retrieved
    ),
)

print(
    "Leading candidate:",
    report[
        "investigator"
    ][
        "leading_candidate"
    ],
)

print(
    "Recovery verified:",
    report[
        "verifier"
    ][
        "recovery_verified"
    ],
)

print(
    "Agent RCA confirmation:",
    report[
        "safety"
    ][
        "root_cause_confirmed_by_agent"
    ],
)

print(
    "Agent execution authority:",
    report[
        "safety"
    ][
        "agent_execution_authority"
    ],
)

print()
print(
    "PHASE 15 GROUNDED INVESTIGATION: PASSED"
)
