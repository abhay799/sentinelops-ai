from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sentinelops.schemas.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
)
from sentinelops.schemas.rca import (
    EvidenceType,
    RCAEvidence,
    RCAHypothesis,
)
from sentinelops.schemas.remediation import (
    GuardDecision,
    RiskLevel,
    SentinelGuardDecision,
)
from sentinelops.schemas.telemetry import (
    MetricEvent,
    TelemetryType,
)


def now() -> datetime:
    return datetime.now(UTC)


def test_metric_event_accepts_valid_timezone_aware_timestamp():
    event = MetricEvent(
        event_time=now(),
        ingest_time=now(),
        service="payment-service",
        telemetry_type=TelemetryType.METRIC,
        metric_name="latency",
        value=120.5,
        unit="ms",
    )

    assert event.service == "payment-service"
    assert event.value == 120.5


def test_metric_event_rejects_naive_timestamp():
    with pytest.raises(ValidationError):
        MetricEvent(
            event_time=datetime.now(),
            ingest_time=now(),
            service="payment-service",
            telemetry_type=TelemetryType.METRIC,
            metric_name="latency",
            value=120.5,
        )


def test_incident_contract():
    incident = Incident(
        incident_id="INC-001",
        title="Payment latency spike",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        started_at=now(),
        detected_at=now(),
        affected_services=["payment-service"],
        symptoms=["latency spike"],
        correlated_alert_count=3,
    )

    assert incident.incident_id == "INC-001"


def test_rca_confidence_cannot_exceed_one():
    evidence = RCAEvidence(
        evidence_id="E-001",
        evidence_type=EvidenceType.METRIC,
        service="payment-service",
        observed_at=now(),
        description="Memory increased sharply",
        source_reference="metric://payment-service/memory",
    )

    with pytest.raises(ValidationError):
        RCAHypothesis(
            hypothesis_id="RCA-001",
            incident_id="INC-001",
            suspected_service="payment-service",
            suspected_cause="memory exhaustion",
            confidence=1.5,
            evidence=[evidence],
            created_at=now(),
        )


def test_sentinelguard_decision_contract():
    decision = SentinelGuardDecision(
        action_id="ACT-001",
        decision=GuardDecision.RECOMMEND_ONLY,
        confidence=0.80,
        evidence_verified=True,
        rollback_verified=True,
        permissions_verified=True,
        blast_radius_checked=True,
        service_criticality_checked=True,
        reason="Human review required",
        decided_at=now(),
    )

    assert decision.decision == GuardDecision.RECOMMEND_ONLY