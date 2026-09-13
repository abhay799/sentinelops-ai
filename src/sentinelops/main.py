from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sentinelops.api.router import router
from sentinelops.core.config import get_settings
from sentinelops.core.logging import configure_logging, get_logger
from sentinelops.db.postgres import close_postgres
from sentinelops.db.redis import close_redis

settings = get_settings()

configure_logging(settings.SENTINELOPS_LOG_LEVEL)

logger = get_logger("sentinelops")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "application_startup",
        environment=settings.SENTINELOPS_ENV,
    )

    yield

    await close_redis()
    await close_postgres()

    logger.info("application_shutdown")


def create_app() -> FastAPI:
    application = FastAPI(
        title="SentinelOps AI",
        description=(
            "Autonomous Reliability Intelligence "
            "& Failure Prevention Platform"
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(router)

    @application.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": "SentinelOps AI",
            "status": "running",
            "version": "0.1.0",
        }

    return application


app = create_app()
