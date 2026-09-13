import asyncio
import json
import os
import random
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import httpx
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, HTTPException, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))

DOWNSTREAMS_RAW = os.getenv("DOWNSTREAMS", "")

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "sentinelops-kafka:29092",
)

OTEL_ENDPOINT = os.getenv(
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "http://sentinelops-otel:4318",
)

TELEMETRY_TOPIC = "sentinelops.telemetry.raw"


# ============================================================
# Prometheus metrics
# ============================================================

REQUEST_COUNT = Counter(
    "sentinelops_http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "sentinelops_http_request_duration_seconds",
    "HTTP request latency",
    ["service", "method", "path"],
)


# ============================================================
# Configuration
# ============================================================

def parse_downstreams() -> dict[str, str]:
    result: dict[str, str] = {}

    if not DOWNSTREAMS_RAW.strip():
        return result

    for entry in DOWNSTREAMS_RAW.split(","):
        entry = entry.strip()

        if not entry:
            continue

        name, url = entry.split("=", 1)

        result[name.strip()] = url.strip()

    return result


DOWNSTREAMS = parse_downstreams()


# ============================================================
# Failure injection
# ============================================================

class FailureMode(BaseModel):
    mode: Literal[
        "normal",
        "latency",
        "errors",
    ] = "normal"

    latency_ms: int = Field(
        default=0,
        ge=0,
        le=5000,
    )

    error_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


class ChangeEventRequest(BaseModel):
    change_type: Literal[
        "deployment",
        "configuration_change",
        "scaling_event",
        "feature_release",
        "version_change",
    ]

    description: str = Field(min_length=1)

    version_before: str | None = None
    version_after: str | None = None

    actor: str = "phase3-test"


failure_state = FailureMode()


# ============================================================
# OpenTelemetry
# ============================================================

resource = Resource.create(
    {
        "service.name": SERVICE_NAME,
        "service.version": "0.1.0",
        "deployment.environment": "development",
    }
)

tracer_provider = TracerProvider(
    resource=resource,
)

span_exporter = OTLPSpanExporter(
    endpoint=f"{OTEL_ENDPOINT}/v1/traces",
)

tracer_provider.add_span_processor(
    BatchSpanProcessor(span_exporter)
)

trace.set_tracer_provider(tracer_provider)


def server_request_hook(
    span,
    scope: dict,
) -> None:
    if span and span.is_recording():
        context = span.get_span_context()

        scope["sentinelops_trace_id"] = (
            f"{context.trace_id:032x}"
        )


# ============================================================
# Kafka telemetry
# ============================================================

producer: AIOKafkaProducer | None = None


async def emit_telemetry(
    telemetry_type: str,
    payload: dict,
) -> None:
    if producer is None:
        return

    event = {
        "event_id": str(uuid4()),
        "telemetry_type": telemetry_type,
        "service": SERVICE_NAME,
        "event_time": datetime.now(UTC).isoformat(),
        "payload": payload,
    }

    try:
        await producer.send_and_wait(
            TELEMETRY_TOPIC,
            json.dumps(event).encode("utf-8"),
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "level": "warning",
                    "event": "telemetry_publish_failed",
                    "service": SERVICE_NAME,
                    "error": type(exc).__name__,
                }
            ),
            flush=True,
        )


# ============================================================
# Application lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer

    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            client_id=f"{SERVICE_NAME}-telemetry",
            acks="all",
        )

        await producer.start()

        print(
            json.dumps(
                {
                    "level": "info",
                    "event": "kafka_telemetry_connected",
                    "service": SERVICE_NAME,
                }
            ),
            flush=True,
        )

    except Exception as exc:
        producer = None

        print(
            json.dumps(
                {
                    "level": "error",
                    "event": "kafka_telemetry_unavailable",
                    "service": SERVICE_NAME,
                    "error": type(exc).__name__,
                }
            ),
            flush=True,
        )

    yield

    if producer is not None:
        await producer.stop()

    tracer_provider.shutdown()


# ============================================================
# Application factory
# ============================================================

def create_app() -> FastAPI:
    app = FastAPI(
        title=SERVICE_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    # --------------------------------------------------------
    # Telemetry middleware
    # --------------------------------------------------------

    @app.middleware("http")
    async def telemetry_middleware(
        request: Request,
        call_next,
    ):
        started = time.perf_counter()

        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        finally:
            elapsed = time.perf_counter() - started

            path = request.url.path

            REQUEST_COUNT.labels(
                service=SERVICE_NAME,
                method=request.method,
                path=path,
                status=str(status_code),
            ).inc()

            REQUEST_LATENCY.labels(
                service=SERVICE_NAME,
                method=request.method,
                path=path,
            ).observe(elapsed)

            if path not in {
                "/metrics",
                "/live",
                "/ready",
            }:
                trace_id = request.scope.get(
                    "sentinelops_trace_id"
                )

                log_payload = {
                    "method": request.method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(
                        elapsed * 1000,
                        3,
                    ),
                    "trace_id": trace_id,
                }

                print(
                    json.dumps(
                        {
                            "level": "info",
                            "event": "http_request",
                            "service": SERVICE_NAME,
                            **log_payload,
                        }
                    ),
                    flush=True,
                )

                await emit_telemetry(
                    "log",
                    log_payload,
                )

                await emit_telemetry(
                    "metric",
                    {
                        "metric_name": "http_request_duration_ms",
                        "value": round(
                            elapsed * 1000,
                            3,
                        ),
                        "path": path,
                        "status_code": status_code,
                    },
                )

                if trace_id:
                    await emit_telemetry(
                        "trace",
                        {
                            "trace_id": trace_id,
                            "operation": (
                                f"{request.method} {path}"
                            ),
                            "status_code": status_code,
                        },
                    )

    # --------------------------------------------------------
    # Basic endpoints
    # --------------------------------------------------------

    @app.get("/")
    async def root():
        return {
            "service": SERVICE_NAME,
            "status": "running",
            "port": SERVICE_PORT,
        }

    @app.get("/live")
    async def live():
        return {
            "service": SERVICE_NAME,
            "status": "alive",
        }

    @app.get("/ready")
    async def ready():
        return {
            "service": SERVICE_NAME,
            "status": "ready",
            "telemetry": (
                "connected"
                if producer is not None
                else "degraded"
            ),
        }

    @app.get("/metrics")
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.get("/identity")
    async def identity():
        return {
            "service": SERVICE_NAME,
            "port": SERVICE_PORT,
            "downstreams": DOWNSTREAMS,
            "failure_mode": failure_state.model_dump(),
        }

    # --------------------------------------------------------
    # Workload
    # --------------------------------------------------------

    @app.get("/work")
    async def work():
        if failure_state.mode == "latency":
            await asyncio.sleep(
                failure_state.latency_ms / 1000
            )

        if failure_state.mode == "errors":
            if random.random() < failure_state.error_rate:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"{SERVICE_NAME} "
                        "simulated failure"
                    ),
                )

        return {
            "service": SERVICE_NAME,
            "result": "success",
            "failure_mode": failure_state.mode,
        }

    # --------------------------------------------------------
    # Dependency checks
    # --------------------------------------------------------

    @app.get("/dependencies")
    async def dependencies():
        results: dict[str, object] = {}

        async with httpx.AsyncClient(
            timeout=3.0
        ) as client:

            for name, base_url in DOWNSTREAMS.items():

                try:
                    response = await client.get(
                        f"{base_url}/live"
                    )

                    results[name] = {
                        "reachable": (
                            response.status_code == 200
                        ),
                        "status_code": (
                            response.status_code
                        ),
                    }

                except Exception as exc:
                    results[name] = {
                        "reachable": False,
                        "error": type(exc).__name__,
                    }

        return {
            "service": SERVICE_NAME,
            "dependencies": results,
        }

    # --------------------------------------------------------
    # Failure controls
    # --------------------------------------------------------

    @app.post("/failure-mode")
    async def set_failure_mode(
        config: FailureMode,
    ):
        global failure_state

        if config.mode == "normal":
            config.latency_ms = 0
            config.error_rate = 0.0

        failure_state = config

        return {
            "service": SERVICE_NAME,
            "failure_mode": failure_state.model_dump(),
        }

    @app.post("/failure-mode/reset")
    async def reset_failure_mode():
        global failure_state

        failure_state = FailureMode()

        return {
            "service": SERVICE_NAME,
            "failure_mode": failure_state.model_dump(),
        }

    # --------------------------------------------------------
    # Change events
    # --------------------------------------------------------

    @app.post("/change-event")
    async def change_event(
        event: ChangeEventRequest,
    ):
        payload = event.model_dump()

        await emit_telemetry(
            "change",
            payload,
        )

        print(
            json.dumps(
                {
                    "level": "info",
                    "event": "system_change",
                    "service": SERVICE_NAME,
                    **payload,
                }
            ),
            flush=True,
        )

        return {
            "accepted": True,
            "service": SERVICE_NAME,
            "change": payload,
        }

    # --------------------------------------------------------
    # OpenTelemetry instrumentation
    # --------------------------------------------------------

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        server_request_hook=server_request_hook,
        excluded_urls="live,ready,metrics",
    )

    HTTPXClientInstrumentor().instrument()

    return app