import asyncio
import os
import random
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
DOWNSTREAMS_RAW = os.getenv("DOWNSTREAMS", "")


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


class FailureMode(BaseModel):
    mode: Literal["normal", "latency", "errors"] = "normal"
    latency_ms: int = Field(default=0, ge=0, le=5000)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)


failure_state = FailureMode()


app = FastAPI(
    title=SERVICE_NAME,
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "service": SERVICE_NAME,
        "status": "running",
        "port": SERVICE_PORT,
    }


@app.get("/live")
async def live() -> dict[str, str]:
    return {
        "service": SERVICE_NAME,
        "status": "alive",
    }


@app.get("/ready")
async def ready() -> dict[str, str]:
    return {
        "service": SERVICE_NAME,
        "status": "ready",
    }


@app.get("/identity")
async def identity() -> dict[str, object]:
    return {
        "service": SERVICE_NAME,
        "port": SERVICE_PORT,
        "downstreams": DOWNSTREAMS,
        "failure_mode": failure_state.model_dump(),
    }


@app.get("/work")
async def work() -> dict[str, object]:
    if failure_state.mode == "latency":
        await asyncio.sleep(failure_state.latency_ms / 1000)

    if failure_state.mode == "errors":
        if random.random() < failure_state.error_rate:
            raise HTTPException(
                status_code=503,
                detail=f"{SERVICE_NAME} simulated failure",
            )

    return {
        "service": SERVICE_NAME,
        "result": "success",
        "failure_mode": failure_state.mode,
    }


@app.get("/dependencies")
async def dependencies() -> dict[str, object]:
    if not DOWNSTREAMS:
        return {
            "service": SERVICE_NAME,
            "dependencies": {},
        }

    results: dict[str, object] = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, base_url in DOWNSTREAMS.items():
            try:
                response = await client.get(f"{base_url}/live")

                results[name] = {
                    "reachable": response.status_code == 200,
                    "status_code": response.status_code,
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


@app.post("/failure-mode")
async def set_failure_mode(
    config: FailureMode,
) -> dict[str, object]:
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
async def reset_failure_mode() -> dict[str, object]:
    global failure_state

    failure_state = FailureMode()

    return {
        "service": SERVICE_NAME,
        "failure_mode": failure_state.model_dump(),
    }
