from flask import jsonify

from . import bp


@bp.errorhandler(404)
def not_found(e):
    return jsonify(
        error="not_found",
        message="Resource not found",
    ), 404


@bp.errorhandler(400)
def bad_request(e):
    return jsonify(
        error="bad_request",
        message=str(e),
    ), 400


@bp.errorhandler(401)
def unauthorized(e):
    return jsonify(
        error="unauthorized",
        message="Authentication required",
    ), 401


@bp.errorhandler(403)
def forbidden(e):
    return jsonify(
        error="forbidden",
        message="You do not have access to this resource",
    ), 403
