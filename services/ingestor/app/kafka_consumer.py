import asyncio
import json
import logging
from typing import Any, Dict

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from aiokafka.structs import TopicPartition

from .settings import settings
from .kafka_producer import get_producer
from .normalizer import normalize_event, NormalizationError

logger = logging.getLogger(__name__)

async def handle_record(rec: ConsumerRecord) -> None:
    try:
        payload = json.loads(rec.value.decode("utf-8"))
        norm = normalize_event(payload)
        producer = await get_producer()
        await producer.send_and_wait(settings.TOPIC_PARSED, norm)
    except (json.JSONDecodeError, NormalizationError) as e:
        logger.warning("DLQ record offset=%s error=%s", rec.offset, e)
        producer = await get_producer()
        await producer.send_and_wait(settings.TOPIC_DLQ, {"error": str(e), "raw": rec.value.decode("utf-8", "ignore")})

async def run_consumer(stop_event: asyncio.Event) -> None:
    consumer = AIOKafkaConsumer(
        settings.TOPIC_RAW,
        bootstrap_servers=settings.KAFKA_BROKERS,
        group_id=settings.KAFKA_GROUP_INGESTOR,
        client_id=f"{settings.KAFKA_CLIENT_ID}-ingestor",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        max_partition_fetch_bytes=1024*1024,
        fetch_max_wait_ms=200,
    )
    await consumer.start()
    try:
        while not stop_event.is_set():
            batch = await consumer.getmany(timeout_ms=500, max_records=100)
            for tp, records in batch.items():
                for rec in records:
                    await handle_record(rec)
                # commit partition after processing
                if records:
                    last_offset = records[-1].offset
                    await consumer.commit({tp: last_offset + 1})
    finally:
        await consumer.stop()
