from __future__ import annotations

from flask import g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException


def _wants_html() -> bool:
    # If the client explicitly prefers HTML over JSON
    best = request.accept_mimetypes.best_match(
        ["text/html", "application/json"], default="application/json"
    )
    return (
        best == "text/html"
        and request.accept_mimetypes["text/html"] >= request.accept_mimetypes["application/json"]
    )


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        request_id = getattr(g, "request_id", None)

        if _wants_html():
            # Render a matching template if present; fallback to 500 template
            code = e.code or 500
            template = f"errors/{code}.html"
            try:
                return render_template(template, request_id=request_id), code
            except Exception:
                return render_template("errors/500.html", request_id=request_id), 500

        payload = {
            "error": e.name.lower().replace(" ", "_"),
            "message": e.description,
            "request_id": request_id,
        }
        return jsonify(payload), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e: Exception):
        request_id = getattr(g, "request_id", None)

        # Keep logs correlated
        app.logger.exception("Unhandled exception (request_id=%s)", request_id)

        if _wants_html():
            return render_template("errors/500.html", request_id=request_id), 500

        return jsonify(
            error="internal_server_error",
            message="An unexpected error occurred",
            request_id=request_id,
        ), 500
