from fastapi import APIRouter
from aiokafka.admin import AIOKafkaAdminClient
import asyncio
from ..os_client import get_client
from ..settings import settings

router = APIRouter(tags=["health"])

@router.get("/healthz")
async def healthz():
    kafka_status = "down"
    os_status = "down"

    # Kafka probe
    try:
        admin = AIOKafkaAdminClient(bootstrap_servers=settings.KAFKA_BROKERS, client_id=settings.KAFKA_CLIENT_ID)
        await admin.start()
        await admin.list_topics()
        await admin.close()
        kafka_status = "ok"
    except Exception:
        kafka_status = "down"

    # OpenSearch probe
    try:
        client = get_client()
        h = client.cluster.health()
        if h and h.get("status"):
            os_status = "ok"
    except Exception:
        os_status = "down"

    return {"kafka": kafka_status, "opensearch": os_status}
