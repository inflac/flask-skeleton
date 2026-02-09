from __future__ import annotations

from flask import Blueprint, Flask

bp = Blueprint("auth", __name__)


def init_auth(app: Flask) -> None:
    from . import routes_local  # noqa: F401

    providers = app.config.get("AUTH_PROVIDERS", ["local"])

    if "github" in providers or "google" in providers:
        try:
            from .oauth import init_oauth
        except ModuleNotFoundError as e:
            raise RuntimeError(
                "OAuth provider enabled but 'authlib' is not installed. "
                "Install with: pip install -e '.[oauth]'"
            ) from e

        init_oauth(app)
        from . import routes_oauth  # noqa: F401
