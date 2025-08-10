import time
from typing import Callable, Dict
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .settings import settings

security = HTTPBasic()

# Simple token bucket per client IP
RATE_LIMIT = {
    "capacity": 30,      # max tokens
    "refill_rate": 15.0, # tokens per second
}
_buckets: Dict[str, Dict[str, float]] = {}

def check_basic(credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == settings.API_BASIC_USER and credentials.password == settings.API_BASIC_PASS):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return credentials.username

def rate_limiter(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _buckets.setdefault(ip, {"tokens": RATE_LIMIT["capacity"], "last": now})
    # refill
    elapsed = now - bucket["last"]
    bucket["tokens"] = min(RATE_LIMIT["capacity"], bucket["tokens"] + elapsed * RATE_LIMIT["refill_rate"])
    bucket["last"] = now
    if bucket["tokens"] < 1.0:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket["tokens"] -= 1.0
