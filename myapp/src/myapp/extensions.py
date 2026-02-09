from __future__ import annotations

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Create extension objects once; init_app(app) happens in create_app()
db = SQLAlchemy()
migrate = Migrate()
