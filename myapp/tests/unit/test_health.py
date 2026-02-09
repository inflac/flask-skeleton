from myapp import create_app


def test_health_endpoint():
    app = create_app("testing")
    client = app.test_client()

    r = client.get("/health", headers={"Accept": "application/json"})
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}
    assert r.headers.get("X-Request-ID")
