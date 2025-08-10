from typing import List, Tuple
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import ValidationError
from . import query as query_router  # for types
from ..schemas import LogEvent
from ..kafka_producer import get_producer
from ..settings import settings
from ..deps import check_basic, rate_limiter

router = APIRouter(tags=["ingest"])

def _parse_ndjson(raw: bytes) -> Tuple[List[LogEvent], List[str]]:
    ok, bad = [], []
    for i, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = LogEvent.model_validate_json(line)
            ok.append(obj)
        except ValidationError as ve:
            bad.append(f"line {i}: {ve}")
    return ok, bad

@router.post("/ingest/logs")
async def ingest_logs(request: Request, _user: str = Depends(check_basic), _rl: None = Depends(rate_limiter)):
    ctype = request.headers.get("content-type", "")
    body = await request.body()
    docs: List[LogEvent] = []
    errors: List[str] = []

    if "application/x-ndjson" in ctype:
        docs, errors = _parse_ndjson(body)
    elif "application/json" in ctype or ctype == "":
        try:
            docs_in = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        if not isinstance(docs_in, list):
            raise HTTPException(status_code=400, detail="Expected JSON array for application/json")
        for i, obj in enumerate(docs_in, start=1):
            try:
                docs.append(LogEvent.model_validate(obj))
            except ValidationError as ve:
                errors.append(f"item {i}: {ve}")
    else:
        raise HTTPException(status_code=415, detail="Unsupported Content-Type")

    if not docs and errors:
        return {"accepted": 0, "failed": len(errors), "errors": errors[:10]}

    producer = await get_producer()
    topic = settings.TOPIC_RAW
    accepted = 0
    for d in docs:
        try:
            await producer.send_and_wait(topic, d.model_dump(by_alias=True, mode="json"))
            accepted += 1
        except Exception as e:
            errors.append(str(e))

    return {"accepted": accepted, "failed": len(errors), "errors": errors[:10]}
