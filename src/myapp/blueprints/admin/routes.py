from flask import render_template

from . import bp
from .utils import admin_required


@bp.get("/")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")
