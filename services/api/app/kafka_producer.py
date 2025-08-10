import asyncio
import json
from typing import Optional

from aiokafka import AIOKafkaProducer
from .settings import settings

_producer: Optional[AIOKafkaProducer] = None
_started = asyncio.Event()

def _json_serialize(v):
    # default=str makes datetime -> ISO string if any slipped through
    return json.dumps(v, default=str).encode("utf-8")

async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKERS,
            client_id=settings.KAFKA_CLIENT_ID,
            value_serializer=_json_serialize,
            compression_type="gzip",
            linger_ms=10,
            max_request_size=1048576,
        )
        await _producer.start()
        _started.set()
    return _producer

async def stop_producer():
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        _started.clear()
