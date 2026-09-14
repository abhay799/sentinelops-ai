from __future__ import annotations

from typing import Any

import polars as pl


def _rows_for_incident(
    data: pl.DataFrame,
    incident_id: str,
) -> list[dict[str, Any]]:

    if data.is_empty():
        return []

    if "incident_id" not in data.columns:
        return []

    return (
        data
        .filter(
            pl.col("incident_id")
            == incident_id
        )
        .to_dicts()
    )


def build_evidence_bundle(
    incident_id: str,
    incident_intelligence: pl.DataFrame,
    rca_disposition: pl.DataFrame,
    incident_priority: pl.DataFrame,
    counterfactual_summary: pl.DataFrame,
    remediation_audit: pl.DataFrame,
    execution_results: pl.DataFrame,
    recovery_verification: pl.DataFrame,
) -> dict[str, Any]:

    incident_rows = _rows_for_incident(
        incident_intelligence,
        incident_id,
    )

    rca_rows = _rows_for_incident(
        rca_disposition,
        incident_id,
    )

    priority_rows = _rows_for_incident(
        incident_priority,
        incident_id,
    )

    counterfactual_rows = _rows_for_incident(
        counterfactual_summary,
        incident_id,
    )

    remediation_rows = _rows_for_incident(
        remediation_audit,
        incident_id,
    )

    execution_rows = _rows_for_incident(
        execution_results,
        incident_id,
    )

    verification_rows = _rows_for_incident(
        recovery_verification,
        incident_id,
    )

    sources = []

    datasets = [
        (
            "incident_intelligence",
            incident_rows,
        ),
        (
            "rca_disposition",
            rca_rows,
        ),
        (
            "incident_priority",
            priority_rows,
        ),
        (
            "counterfactual_summary",
            counterfactual_rows,
        ),
        (
            "remediation_audit",
            remediation_rows,
        ),
        (
            "execution_results",
            execution_rows,
        ),
        (
            "recovery_verification",
            verification_rows,
        ),
    ]

    for name, rows in datasets:

        if rows:
            sources.append(
                {
                    "source":
                        name,

                    "row_count":
                        len(rows),
                }
            )

    return {
        "incident_id":
            incident_id,

        "incident":
            incident_rows,

        "rca":
            rca_rows,

        "priority":
            priority_rows,

        "counterfactual":
            counterfactual_rows,

        "remediation":
            remediation_rows,

        "execution":
            execution_rows,

        "verification":
            verification_rows,

        "evidence_sources":
            sources,

        "evidence_source_count":
            len(sources),

        "agent_can_confirm_root_cause":
            False,

        "agent_can_execute":
            False,
    }
