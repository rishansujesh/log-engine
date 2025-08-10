from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class LogEvent(BaseModel):
    timestamp: datetime = Field(alias='@timestamp')
    level: str
    service: str
    env: str
    host: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class IngestResponse(BaseModel):
    accepted: int
    failed: int
    errors: list[str] = []
