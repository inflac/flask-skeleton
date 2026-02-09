from __future__ import annotations

import uuid
from flask import g, request


HEADER = "X-Request-ID"


def register_request_id(app):
    @app.before_request
    def _set_request_id():
        rid = request.headers.get(HEADER)
        if not rid:
            rid = uuid.uuid4().hex
        g.request_id = rid

    @app.after_request
    def _add_request_id_header(response):
        rid = getattr(g, "request_id", None)
        if rid:
            response.headers[HEADER] = rid
        return response
