from flask import render_template

from . import bp


@bp.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@bp.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403
