from app.routers.query import build_search_body

def test_build_search_body_terms():
    body = build_search_body("err*", "2024-01-01T00:00:00Z", None, "error", "api", "dev")
    q = body["query"]["bool"]
    assert any("simple_query_string" in m for m in q["must"])
    assert any("term" in f and "level" in f["term"] for f in q["filter"])
