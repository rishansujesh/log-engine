from app.index_writer import build_bulk_lines
import json


def test_build_bulk_lines_with_and_without_id():
    docs = [
        {
            "@timestamp": "2025-01-01T00:00:00Z",
            "level": "info",
            "service": "api",
            "env": "dev",
            "host": "local",
            "message": "hello",
            "_idempotencyKey": "k1",
        },
        {
            "@timestamp": "2025-01-01T00:00:01Z",
            "level": "error",
            "service": "auth",
            "env": "dev",
            "host": "local",
            "message": "boom",
        },
    ]
    body = build_bulk_lines(docs, "logs-write")
    assert body.endswith("\n")

    lines = body.strip().split("\n")
    # Expect 4 lines (2 action + 2 source)
    assert len(lines) == 4

    a1 = json.loads(lines[0])
    s1 = json.loads(lines[1])
    a2 = json.loads(lines[2])
    s2 = json.loads(lines[3])

    assert "index" in a1 and a1["index"]["_index"] == "logs-write" and a1["index"]["_id"] == "k1"
    assert s1["message"] == "hello"
    assert "index" in a2 and a2["index"]["_index"] == "logs-write" and "_id" not in a2["index"]
    assert s2["message"] == "boom"
