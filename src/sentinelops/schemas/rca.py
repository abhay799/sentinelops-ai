from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceType(StrEnum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    CHANGE = "change"
    TOPOLOGY = "topology"
    HISTORICAL_INCIDENT = "historical_incident"


class RCAEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    evidence_type: EvidenceType

    service: str = Field(min_length=1)
    observed_at: datetime

    description: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)

    supports_hypothesis: bool = True


class RCAHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)

    suspected_service: str = Field(min_length=1)
    suspected_cause: str = Field(min_length=1)

    confidence: float = Field(ge=0.0, le=1.0)

    evidence: list[RCAEvidence] = Field(default_factory=list)

    alternative_explanations: list[str] = Field(default_factory=list)

    created_at: datetime

    challenger_reviewed: bool = False
    challenger_rejected: bool = False