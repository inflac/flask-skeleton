from __future__ import annotations

import os
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlparse


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_INSTANCE_DIR = _PROJECT_ROOT / "instance"


def _normalize_db_url(db_url: str) -> str:
    if not db_url:
        return db_url
    if not db_url.startswith("sqlite:"):
        return db_url

    parsed = urlparse(db_url)
    path = parsed.path or ""

    if path == "/:memory:":
        return db_url

    raw = path.lstrip("/")
    is_windows_abs = len(raw) >= 3 and raw[1] == ":" and raw[2] in ("/", "\\")
    is_posix_abs = path.startswith("//")

    if is_windows_abs or is_posix_abs:
        return db_url

    if raw.startswith("instance/") or raw.startswith("instance\\"):
        raw = raw.split("instance", 1)[1].lstrip("/\\")

    _INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    abs_path = (_INSTANCE_DIR / raw).resolve()
    return f"sqlite:///{abs_path.as_posix()}"


def _db_url(default: str) -> str:
    return _normalize_db_url(os.getenv("DATABASE_URL", default))


@dataclass(frozen=True)
class BaseConfig:
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))

    AUTH_PROVIDERS: list[str] = field(
        default_factory=lambda: _env_list("AUTH_PROVIDERS", ["local"])
    )
    AUTH_ALLOW_REGISTRATION: bool = field(
        default_factory=lambda: _env_bool("AUTH_ALLOW_REGISTRATION", False)
    )
    AUTH_AFTER_LOGIN: str = field(default_factory=lambda: os.getenv("AUTH_AFTER_LOGIN", "/"))
    AUTH_DEFAULT_ADMIN_REDIRECT: str = field(
        default_factory=lambda: os.getenv("AUTH_DEFAULT_ADMIN_REDIRECT", "/admin")
    )

    AUTH_LINK_BY_EMAIL: bool = field(default_factory=lambda: _env_bool("AUTH_LINK_BY_EMAIL", False))
    AUTH_TRUSTED_EMAIL_PROVIDERS: list[str] = field(
        default_factory=lambda: _env_list("AUTH_TRUSTED_EMAIL_PROVIDERS", ["google"])
    )

    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    REMEMBER_COOKIE_HTTPONLY: bool = True
    REMEMBER_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = True
    REMEMBER_COOKIE_SECURE: bool = True

    SQLALCHEMY_DATABASE_URI: str = field(default_factory=lambda: _db_url("sqlite:///app.sqlite3"))
    SQLALCHEMY_ECHO: bool = field(default_factory=lambda: _env_bool("SQLALCHEMY_ECHO", False))
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = field(
        default_factory=lambda: _env_bool("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    )


@dataclass(frozen=True)
class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    SESSION_COOKIE_SECURE: bool = False
    REMEMBER_COOKIE_SECURE: bool = False


@dataclass(frozen=True)
class TestingConfig(BaseConfig):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = field(default_factory=lambda: _db_url("sqlite:///test.sqlite3"))
    WTF_CSRF_ENABLED: bool = False
    SESSION_COOKIE_SECURE: bool = False
    REMEMBER_COOKIE_SECURE: bool = False


@dataclass(frozen=True)
class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False


_CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "testing": TestingConfig,
    "test": TestingConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
}


def get_config(name: str) -> type[BaseConfig]:
    """Return a config class by name (e.g. 'development', 'testing', 'production')."""
    try:
        return _CONFIG_MAP[name.lower()]
    except KeyError as e:
        raise ValueError(
            f"Unknown CONFIG={name!r}. Use one of: {', '.join(sorted(_CONFIG_MAP))}"
        ) from e


def build_config(name: str) -> dict[str, object]:
    """
    Materialize a dataclass config into a plain dict suitable for app.config.from_mapping().
    Ensures default_factory values are evaluated.
    """
    cls = get_config(name)
    return asdict(cls())
