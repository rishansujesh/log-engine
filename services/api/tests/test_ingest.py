from app.schemas import LogEvent
from datetime import datetime, timezone

def test_logevent_validation():
    data = {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "info",
        "service": "api-gateway",
        "env": "dev",
        "host": "localhost",
        "message": "hello"
    }
    ev = LogEvent.model_validate(data)
    assert ev.service == "api-gateway"
