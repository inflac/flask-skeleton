import pytest

from myapp import create_app


@pytest.fixture()
def app():
    app = create_app("testing")

    # A route that raises to trigger 500
    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_html_404_renders_template(client):
    r = client.get("/nope", headers={"Accept": "text/html"})
    assert r.status_code == 404
    assert b"404" in r.data
    assert r.headers.get("X-Request-ID")


def test_json_404_returns_json(client):
    r = client.get("/nope", headers={"Accept": "application/json"})
    assert r.status_code == 404
    data = r.get_json()
    assert data["error"] == "not_found"
    assert "request_id" in data
    assert r.headers.get("X-Request-ID")


def test_html_500_renders_template(client):
    r = client.get("/boom", headers={"Accept": "text/html"})
    assert r.status_code == 500
    assert b"500" in r.data
    assert r.headers.get("X-Request-ID")


def test_json_500_returns_json(client):
    r = client.get("/boom", headers={"Accept": "application/json"})
    assert r.status_code == 500
    data = r.get_json()
    assert data["error"] == "internal_server_error"
    assert "request_id" in data
    assert r.headers.get("X-Request-ID")
