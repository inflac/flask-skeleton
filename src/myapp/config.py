from __future__ import annotations

import os
import secrets

from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class BaseConfig:
    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))  # default to random for dev, but require env var in prod

    # SQLAlchemy (Flask-SQLAlchemy reads these keys)
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///instance/app.sqlite3",  # safe default for local dev
    )
    SQLALCHEMY_ECHO: bool = _env_bool("SQLALCHEMY_ECHO", False)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = _env_bool("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Recommended for proxy setups (Traefik/Nginx) if you use them later
    # Prefer to keep off unless needed.
    # PREFERRED_URL_SCHEME: str = "https"


@dataclass(frozen=True)
class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True


@dataclass(frozen=True)
class TestingConfig(BaseConfig):
    TESTING: bool = True
    # For tests, default to in-memory sqlite unless overridden
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    WTF_CSRF_ENABLED: bool = False  # if you later add Flask-WTF


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
