import json
from typing import Optional
from aiokafka import AIOKafkaProducer
from .settings import settings

_producer: Optional[AIOKafkaProducer] = None

async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKERS,
            client_id=f"{settings.KAFKA_CLIENT_ID}-ingestor",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            compression_type="gzip",
            linger_ms=10,
        )
        await _producer.start()
    return _producer

async def close_producer():
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
