import asyncio
import json
import logging
from typing import Dict, List

from aiokafka import AIOKafkaConsumer
from .settings import Settings
from .index_writer import IndexWriter
from .os_client import build_client, ping_ok

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = Settings()

    client = build_client(
        host=settings.os_host,
        user=settings.os_user,
        password=settings.os_password,
        timeout=settings.os_request_timeout,
        max_retries=settings.os_max_retries,
        backoff=settings.os_retry_backoff_base,
    )
    if not ping_ok(client):
        logger.warning("OpenSearch ping failed; continuing (will retry on bulk)")

    consumer = AIOKafkaConsumer(
        settings.topic_parsed,
        bootstrap_servers=[b.strip() for b in settings.kafka_brokers.split(",") if b.strip()],
        group_id=settings.kafka_group_indexer,
        client_id=settings.kafka_client_id + "-indexer",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda v: v.decode("utf-8") if v is not None else None,
        # max_poll_records is not in aiokafka; we batch via getmany below
    )

    writer = IndexWriter(
        client=client,
        index_alias=settings.os_index_alias,
        max_docs=settings.bulk_max_docs,
        max_bytes=settings.bulk_max_bytes,
        flush_interval_s=settings.bulk_flush_interval_s,
        max_retries=settings.os_max_retries,
        retry_backoff_base=settings.os_retry_backoff_base,
    )

    await consumer.start()
    try:
        while True:
            batch_map = await consumer.getmany(timeout_ms=settings.consumer_poll_ms, max_records=settings.consumer_max_records)
            total = sum(len(msgs) for msgs in batch_map.values())
            if total == 0:
                # Periodic time-based flush if buffers exist
                await writer.flush(force=False)
                continue

            # Process messages
            for tp, msgs in batch_map.items():
                for m in msgs:
                    try:
                        doc = m.value  # already deserialized
                        # Ensure minimal required fields exist; ingestor should have normalized these
                        writer.add(doc)
                    except Exception as e:
                        logger.exception("failed to prepare doc for bulk: %s", e)

            # Force flush so we can safely commit consumed offsets (exactly-once indexing via idempotent _id)
            flushed = await writer.flush(force=True)
            if flushed > 0:
                await consumer.commit()
    finally:
        await consumer.stop()
