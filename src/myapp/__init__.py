from __future__ import annotations

import os

from flask import Flask
from .config import get_config
from .extensions import db, migrate
from .errors import register_error_handlers
from .request_id import register_request_id

from .blueprints.auth import bp as auth_bp
from .blueprints.api import bp as api_bp
from .blueprints.admin import bp as admin_bp


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )

    # Config: default from env (e.g. CONFIG=development)
    config_name = config_name or os.getenv("CONFIG", "development")
    app.config.from_object(get_config(config_name))

    # Ensure instance folder exists (good for local configs / sqlite)
    os.makedirs(app.instance_path, exist_ok=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    register_request_id(app)
    register_error_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
