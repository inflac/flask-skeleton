from flask import Blueprint

bp = Blueprint("admin", __name__)

from . import errors, routes  # noqa: E402,F401
