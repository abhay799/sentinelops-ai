from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class IncidentSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RECOVERED = "recovered"
    CLOSED = "closed"


class IncidentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_time: datetime
    service: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    title: str = Field(min_length=1)

    severity: IncidentSeverity
    status: IncidentStatus

    started_at: datetime
    detected_at: datetime

    affected_services: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)

    timeline: list[IncidentEvent] = Field(default_factory=list)

    correlated_alert_count: int = Field(default=0, ge=0)

    customer_impact: str | None = None
    suspected_change_id: str | None = None