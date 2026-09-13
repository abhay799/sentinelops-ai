from enum import StrEnum
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

from sentinelops.core.config import load_yaml_config


class ServiceCriticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    criticality: ServiceCriticality
    owner: str = Field(min_length=1)
    enabled: bool = True


@lru_cache
def get_service_registry() -> tuple[ServiceDefinition, ...]:
    config = load_yaml_config("services.yaml")

    raw_services = config.get("services", [])

    return tuple(
        ServiceDefinition.model_validate(service)
        for service in raw_services
    )


def get_service(name: str) -> ServiceDefinition | None:
    for service in get_service_registry():
        if service.name == name:
            return service

    return None
