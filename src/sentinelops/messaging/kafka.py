from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient

from sentinelops.core.config import get_settings

settings = get_settings()


async def check_kafka() -> bool:
    admin = AIOKafkaAdminClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        client_id="sentinelops-healthcheck",
    )

    try:
        await admin.start()

        topics = await admin.list_topics()

        return "sentinelops.telemetry.raw" in topics

    except Exception:
        return False

    finally:
        await admin.close()


async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        client_id="sentinelops-api",
        acks="all",
    )

    await producer.start()

    return producer


async def close_producer(
    producer: AIOKafkaProducer,
) -> None:
    await producer.stop()