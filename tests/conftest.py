import os
from pathlib import Path

import pytest

from myapp import create_app
from myapp.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    os.environ["CONFIG"] = "testing"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["AUTH_PROVIDERS"] = "local"
    os.environ["AUTH_ALLOW_REGISTRATION"] = "1"

    # Build a temporary app just to discover instance_path is NOT ideal,
    # so instead: pick a deterministic test DB path and ensure directory exists.
    # We align with Flask's default instance folder: <repo>/instance.
    instance_dir = Path.cwd() / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    db_path = instance_dir / "test.sqlite3"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    app = create_app("testing")

    with app.app_context():
        _db.drop_all()
        _db.create_all()

    yield app

    with app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()

    try:
        db_path.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db():
    return _db
