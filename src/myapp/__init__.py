from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, render_template

from .blueprints.admin import bp as admin_bp
from .blueprints.api import bp as api_bp
from .blueprints.auth import bp as auth_bp
from .blueprints.auth import init_auth
from .cli import register_cli
from .config import build_config
from .errors import register_error_handlers
from .extensions import csrf, db, login_manager, migrate
from .models import User
from .request_id import register_request_id


def create_app(config_name: str | None = None) -> Flask:
    load_dotenv()  # Load .env if it exists

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )

    # Config: default from env (e.g. CONFIG=development)
    config_name = config_name or os.getenv("CONFIG", "development").lower()
    app.config.from_mapping(build_config(config_name))

    # Ensure instance folder exists (good for local configs / sqlite)
    os.makedirs(app.instance_path, exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    init_auth(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    register_cli(app)
    register_request_id(app)
    register_error_handlers(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
