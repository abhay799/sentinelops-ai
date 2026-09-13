from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetryType(StrEnum):
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"
    CHANGE = "change"


class ChangeType(StrEnum):
    DEPLOYMENT = "deployment"
    CONFIGURATION_CHANGE = "configuration_change"
    SCALING_EVENT = "scaling_event"
    FEATURE_RELEASE = "feature_release"
    VERSION_CHANGE = "version_change"


class TelemetryBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_time: datetime
    ingest_time: datetime
    service: str = Field(min_length=1)
    telemetry_type: TelemetryType

    @field_validator("event_time", "ingest_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return value


class MetricEvent(TelemetryBase):
    telemetry_type: TelemetryType = TelemetryType.METRIC

    metric_name: str = Field(min_length=1)
    value: float
    unit: str | None = None


class LogEvent(TelemetryBase):
    telemetry_type: TelemetryType = TelemetryType.LOG

    level: str = Field(min_length=1)
    message: str = Field(min_length=1)
    trace_id: str | None = None


class TraceEvent(TelemetryBase):
    telemetry_type: TelemetryType = TelemetryType.TRACE

    trace_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    parent_span_id: str | None = None
    operation: str = Field(min_length=1)
    start_time: datetime
    end_time: datetime
    status: str = Field(min_length=1)

    @field_validator("start_time", "end_time")
    @classmethod
    def require_trace_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("trace timestamp must include timezone information")
        return value


class ChangeEvent(TelemetryBase):
    telemetry_type: TelemetryType = TelemetryType.CHANGE

    change_type: ChangeType
    version_before: str | None = None
    version_after: str | None = None
    actor: str | None = None
    description: str | None = None