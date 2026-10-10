from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

Scenario = Literal["latency", "errors", "bad_deployment_rollback"]
Approver = Literal["scripted_approver_v1"]

_TIMESTAMP_FIELDS = (
    "injection_start",
    "injection_end",
    "recovery_time",
    "detection_time",
    "rca_output_time",
    "guard_decision_time",
    "remediation_time",
    "verification_time",
)


class ChaosRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    seed: int
    scenario: Scenario
    approver: Approver
    injection_start: datetime
    injection_end: datetime
    recovery_time: datetime | None
    detection_time: datetime | None
    rca_output_time: datetime | None
    guard_decision_time: datetime | None
    remediation_time: datetime | None
    verification_time: datetime | None

    @field_validator(*_TIMESTAMP_FIELDS)
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware UTC")
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("timestamp must be UTC")
        return value

    @model_validator(mode="after")
    def validate_order(self) -> "ChaosRunRecord":
        ordered = [
            self.injection_start,
            self.detection_time,
            self.rca_output_time,
            self.guard_decision_time,
            self.remediation_time,
            self.injection_end,
            self.verification_time,
            self.recovery_time,
        ]
        observed = [value for value in ordered if value is not None]
        if any(
            later < earlier
            for earlier, later in zip(
                observed,
                observed[1:],
                strict=False,
            )
        ):
            raise ValueError("timestamps are out of order")
        return self
