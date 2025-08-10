from app.normalizer import normalize_event

def test_normalize_minimal():
    ev = {"level":"info","message":"ok","service":"svc","env":"dev","host":"h"}
    out = normalize_event(ev)
    assert out["level"] == "info"
    assert out["service"] == "svc"
    assert "@timestamp" in out
    assert "_idempotencyKey" in out
