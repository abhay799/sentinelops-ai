from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


REPORT = Path(
    "data/processed/investigation/"
    "final_investigation_v1.json"
)


def create_app() -> FastAPI:

    app = FastAPI(
        title="SentinelOps Investigation API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://sentinelops-ai-weld.vercel.app",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/live")
    def live():
        return {
            "status": "live"
        }

    @app.get("/ready")
    def ready():

        return {
            "status":
                (
                    "ready"
                    if REPORT.exists()
                    else "not_ready"
                )
        }

    @app.get(
        "/investigation/latest"
    )
    def latest():

        if not REPORT.exists():

            raise HTTPException(
                status_code=503,
                detail=(
                    "Investigation artifact "
                    "not available"
                ),
            )

        return json.loads(
            REPORT.read_text(
                encoding="utf-8"
            )
        )

    @app.get(
        "/capabilities"
    )
    def capabilities():

        return {
            "investigation":
                True,

            "rag":
                True,

            "multi_agent":
                True,

            "agent_rca_confirmation":
                False,

            "agent_execution":
                False,

            "sentinelguard_bypass":
                False,

            "human_approval_bypass":
                False,
        }

    return app


app = create_app()
