from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "configs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SENTINELOPS_ENV: str = "development"
    SENTINELOPS_LOG_LEVEL: str = "INFO"
    SENTINELOPS_HOST: str = "127.0.0.1"
    SENTINELOPS_PORT: int = 8000

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "sentinelops"
    POSTGRES_USER: str = "sentinelops"
    POSTGRES_PASSWORD: str = "sentinelops_dev"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    OTEL_SERVICE_NAME: str = "sentinelops-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    PROMETHEUS_URL: str = "http://localhost:9090"
    GRAFANA_URL: str = "http://localhost:3000"

    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    SENTINELGUARD_MODE: str = "recommend_only"
    SENTINELGUARD_AUTO_EXECUTE: bool = False

    SENTINELOPS_SECRET_KEY: str = "CHANGE_ME"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml_config(filename: str) -> dict[str, Any]:
    path = CONFIG_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ValueError(f"Configuration must contain a YAML mapping: {path}")

    return data