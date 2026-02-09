from flask import flash, redirect, url_for

from . import bp


@bp.errorhandler(401)
def unauthorized(e):
    flash("Please log in to continue.", "warning")
    return redirect(url_for("auth.login"))
