import redis.asyncio as redis

from sentinelops.core.config import get_settings

settings = get_settings()


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


async def check_redis() -> bool:
    try:
        result = await redis_client.ping()
        return bool(result)
    except Exception:
        return False


async def close_redis() -> None:
    await redis_client.aclose()