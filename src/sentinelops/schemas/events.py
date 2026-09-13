from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class InternalEventType(StrEnum):
    TELEMETRY_INGESTED = "telemetry_ingested"
    ANOMALY_DETECTED = "anomaly_detected"
    INCIDENT_CREATED = "incident_created"
    RCA_CREATED = "rca_created"
    RCA_CHALLENGED = "rca_challenged"
    FAILURE_PREDICTED = "failure_predicted"
    REMEDIATION_PROPOSED = "remediation_proposed"
    GUARD_DECISION = "guard_decision"
    REMEDIATION_EXECUTED = "remediation_executed"
    RECOVERY_VERIFIED = "recovery_verified"


class InternalEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    event_type: InternalEventType

    source_service: str = Field(min_length=1)

    correlation_id: str | None = None

    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    payload: dict[str, Any] = Field(default_factory=dict)
