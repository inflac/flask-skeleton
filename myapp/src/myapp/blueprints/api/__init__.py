from flask import Blueprint

bp = Blueprint("api", __name__)

from . import routes, errors  # noqa: E402,F401
