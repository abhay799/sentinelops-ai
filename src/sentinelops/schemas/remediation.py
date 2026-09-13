from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardDecision(StrEnum):
    AUTO_EXECUTE = "AUTO_EXECUTE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    RECOMMEND_ONLY = "RECOMMEND_ONLY"
    BLOCK = "BLOCK"


class RemediationAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)

    target_service: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    description: str = Field(min_length=1)

    risk_level: RiskLevel

    rollback_available: bool
    rollback_action: str | None = None

    expected_outcome: str | None = None
    created_at: datetime


class SentinelGuardDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(min_length=1)

    decision: GuardDecision
    confidence: float = Field(ge=0.0, le=1.0)

    evidence_verified: bool
    rollback_verified: bool
    permissions_verified: bool
    blast_radius_checked: bool
    service_criticality_checked: bool

    reason: str = Field(min_length=1)

    decided_at: datetime