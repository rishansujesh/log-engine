from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from .routers import ingest, query, health

app = FastAPI(title="Log Engine API", version="0.1.0")
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(health.router)

# Root convenience
@app.get("/")
def root():
    return {"ok": True, "service": "api"}
