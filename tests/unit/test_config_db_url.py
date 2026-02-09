from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import pytest

from myapp import config


def _path_from_sqlite_url(sqlite_url: str) -> Path:
    """
    sqlite:///C:/x/y.db -> /C:/x/y.db  (parsed.path)
    sqlite:////abs/x.db -> //abs/x.db
    sqlite:///rel.db -> /rel.db
    """
    parsed = urlparse(sqlite_url)
    return Path(parsed.path)


def test_normalize_db_url_empty_string():
    assert config._normalize_db_url("") == ""


def test_normalize_db_url_non_sqlite_passthrough():
    url = "postgresql+psycopg://user:pass@localhost/db"
    assert config._normalize_db_url(url) == url


def test_normalize_db_url_memory_passthrough():
    url = "sqlite:///:memory:"
    assert config._normalize_db_url(url) == url


def test_normalize_db_url_relative_anchors_to_repo_instance(tmp_path):
    # sqlite:///test.sqlite3 should be anchored to <repo>/instance/test.sqlite3
    out = config._normalize_db_url("sqlite:///test.sqlite3")

    expected = (config._PROJECT_ROOT / "instance" / "test.sqlite3").resolve().as_posix()
    assert out == f"sqlite:///{expected}"


def test_normalize_db_url_strips_leading_instance_segment():
    # sqlite:///instance/foo.db should NOT become <repo>/instance/instance/foo.db
    out = config._normalize_db_url("sqlite:///instance/foo.db")

    expected = (config._PROJECT_ROOT / "instance" / "foo.db").resolve().as_posix()
    assert out == f"sqlite:///{expected}"


@pytest.mark.parametrize(
    "absolute_url",
    [
        # Windows absolute (drive letter)
        "sqlite:///C:/temp/mydb.sqlite3",
        # POSIX absolute: sqlite:////abs/path.db results in parsed.path starting with '//'
        "sqlite:////tmp/mydb.sqlite3",
    ],
)
def test_normalize_db_url_absolute_paths_passthrough(absolute_url: str):
    # absolute paths should be returned unchanged
    assert config._normalize_db_url(absolute_url) == absolute_url


def test_build_config_materializes_dataclass_to_dict(monkeypatch):
    monkeypatch.setenv("AUTH_PROVIDERS", "local")
    d = config.build_config("testing")
    assert isinstance(d, dict)
    assert "SQLALCHEMY_DATABASE_URI" in d
    assert "AUTH_PROVIDERS" in d
