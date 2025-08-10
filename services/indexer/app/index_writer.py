import asyncio
import json
import logging
import time
from typing import Dict, List, Tuple, Optional

from opensearchpy import OpenSearch

logger = logging.getLogger(__name__)


def _action_line(index_alias: str, doc: dict) -> dict:
    # Use _idempotencyKey if present to dedupe/idempotent writes
    idx = {"_index": index_alias}
    if "_idempotencyKey" in doc:
        idx["_id"] = doc["_idempotencyKey"]
    return {"index": idx}


def build_bulk_lines(docs: List[dict], index_alias: str) -> str:
    """Return NDJSON string for _bulk (must end with newline)."""
    parts: List[str] = []
    for d in docs:
        parts.append(json.dumps(_action_line(index_alias, d), separators=(",", ":")))
        parts.append(json.dumps(d, separators=(",", ":"), default=str))
    parts.append("")  # ensure trailing newline
    return "\n".join(parts)


class IndexWriter:
    def __init__(
        self,
        client: OpenSearch,
        index_alias: str,
        max_docs: int = 1000,
        max_bytes: int = 3_000_000,
        flush_interval_s: float = 1.0,
        max_retries: int = 5,
        retry_backoff_base: float = 0.5,
    ):
        self.client = client
        self.index_alias = index_alias
        self.max_docs = max_docs
        self.max_bytes = max_bytes
        self.flush_interval_s = flush_interval_s
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base

        self._buf: List[dict] = []
        self._bytes: int = 0
        self._last_flush = time.monotonic()

    def add(self, doc: dict) -> None:
        # Size estimate is JSON bytes of doc + action line
        action = _action_line(self.index_alias, doc)
        self._bytes += len(json.dumps(action)) + len(json.dumps(doc, default=str)) + 2  # +2 for newlines
        self._buf.append(doc)

    def _should_flush(self) -> bool:
        if not self._buf:
            return False
        if len(self._buf) >= self.max_docs:
            return True
        if self._bytes >= self.max_bytes:
            return True
        if (time.monotonic() - self._last_flush) >= self.flush_interval_s:
            return True
        return False

    async def flush(self, force: bool = False) -> int:
        if not self._buf:
            if force:
                self._last_flush = time.monotonic()
            return 0
        if not force and not self._should_flush():
            return 0

        docs = self._buf
        self._buf = []
        payload = build_bulk_lines(docs, self.index_alias)
        size = self._bytes
        self._bytes = 0

        # Retry with exponential backoff on failure or OS errors
        attempt = 0
        while True:
            try:
                resp = self.client.bulk(body=payload, refresh=False, request_timeout=30)
                if resp.get("errors"):
                    # Log individual failures; continue (at-least-once semantics + idempotent _id)
                    failures = [item for item in resp.get("items", []) if list(item.values())[0].get("error")]
                    logger.error("bulk had %d failures out of %d items", len(failures), len(docs))
                self._last_flush = time.monotonic()
                logger.debug("bulk flush: %d docs, ~%d bytes", len(docs), size)
                return len(docs)
            except Exception as e:
                if attempt >= self.max_retries:
                    logger.exception("bulk flush failed after %d retries", attempt)
                    raise
                backoff = self.retry_backoff_base * (2 ** attempt)
                logger.warning("bulk flush error: %s (retry in %.2fs)", str(e), backoff)
                await asyncio.sleep(backoff)
                attempt += 1
