from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from ..os_client import get_client
from ..settings import settings
from ..deps import check_basic, rate_limiter

router = APIRouter(tags=["query"])

def build_search_body(q: Optional[str], start: Optional[str], end: Optional[str],
                      level: Optional[str], service: Optional[str], env: Optional[str]) -> Dict[str, Any]:
    must = []
    filter_clause = []

    if q:
        must.append({"simple_query_string": {"query": q, "fields": ["message", "message.keyword", "service", "host", "traceId", "labels.*", "fields.*"]}})

    def term(field: str, value: Optional[str]):
        if value:
            filter_clause.append({"term": {field: value}})

    term("level", level)
    term("service", service)
    term("env", env)

    if start or end:
        rng: Dict[str, Any] = {}
        if start: rng["gte"] = start
        if end: rng["lte"] = end
        filter_clause.append({"range": {"@timestamp": rng}})

    body = {
        "query": {
            "bool": {
                "must": must or [{"match_all": {}}],
                "filter": filter_clause
            }
        }
    }
    return body

@router.get("/query")
def query_logs(
    q: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    level: Optional[str] = None,
    service: Optional[str] = None,
    env: Optional[str] = None,
    size: int = Query(50, ge=1, le=1000),
    from_: int = Query(0, ge=0, alias="from"),
    _user: str = Depends(check_basic),
    _rl: None = Depends(rate_limiter),
):
    client = get_client()
    body = build_search_body(q, start, end, level, service, env)
    try:
        res = client.search(index=settings.OS_INDEX_PATTERN, body=body, size=size, from_=from_, sort="@timestamp:desc")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    hits = [
        {"_id": h.get("_id"), "_source": h.get("_source"), "_score": h.get("_score")}
        for h in res.get("hits", {}).get("hits", [])
    ]
    return {"total": res.get("hits", {}).get("total", {}), "hits": hits, "took": res.get("took")}
