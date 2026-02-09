import pytest
from flask import g

from myapp import create_app


@pytest.fixture()
def app():
    app = create_app("testing")

    @app.get("/rid/normal")
    def rid_normal():
        return {"ok": True}

    @app.get("/rid/delete")
    def rid_delete():
        # Force the after_request branch where rid is missing
        if hasattr(g, "request_id"):
            delattr(g, "request_id")
        return {"ok": True}

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_generates_request_id_when_missing(client):
    r = client.get("/rid/normal")  # no header
    assert r.status_code == 200
    rid = r.headers.get("X-Request-ID")
    assert rid is not None
    assert len(rid) > 0


def test_preserves_request_id_when_provided(client):
    r = client.get("/rid/normal", headers={"X-Request-ID": "abc123"})
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == "abc123"


def test_does_not_set_header_if_request_id_missing_in_g(client):
    r = client.get("/rid/delete")  # route removes g.request_id
    assert r.status_code == 200
    assert "X-Request-ID" not in r.headers
