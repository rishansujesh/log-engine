from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Union, Optional

Number = Union[int, float]

ALLOWED_LEVELS = {"trace","debug","info","warn","error","fatal"}

class NormalizationError(Exception):
    pass

def _iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def normalize_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(ev, dict):
        raise NormalizationError("event must be an object")

    # Required fields with defaults/validation
    ts = ev.get("@timestamp")
    if not ts:
        ts = _iso_now_utc()
    level = str(ev.get("level", "info")).lower()
    if level not in ALLOWED_LEVELS:
        raise NormalizationError(f"invalid level: {level}")
    message = ev.get("message")
    if not isinstance(message, str) or not message:
        raise NormalizationError("message required")
    service = ev.get("service") or "unknown"
    env = ev.get("env") or "dev"
    host = ev.get("host") or "unknown"
    trace_id: Optional[str] = ev.get("traceId")

    labels = ev.get("labels") or {}
    if not isinstance(labels, dict):
        labels = {}

    fields = ev.get("fields") or {}
    if not isinstance(fields, dict):
        fields = {}

    # Idempotency key: sha1(service|timestamp|message)
    idem = hashlib.sha1(f"{service}|{ts}|{message}".encode("utf-8")).hexdigest()

    out: Dict[str, Any] = {
        "@timestamp": ts,
        "level": level,
        "service": str(service),
        "env": str(env),
        "host": str(host),
        "message": message,
        "traceId": str(trace_id) if trace_id is not None else None,
        "labels": {str(k): v for k, v in labels.items()},
        "fields": {str(k): v for k, v in fields.items()},
        "_idempotencyKey": idem,
    }
    # remove None traceId to keep mapping clean
    if out["traceId"] is None:
        del out["traceId"]
    return out
