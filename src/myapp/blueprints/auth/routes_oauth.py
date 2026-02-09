from __future__ import annotations

from flask import redirect, request, url_for
from flask_login import login_user

from ...auth.service import complete_login, get_or_create_user_from_oauth, is_safe_next_url
from . import bp
from .oauth import oauth


@bp.get("/github/login")
def github_login():
    next_url = request.args.get("next", "")
    if next_url and not is_safe_next_url(next_url):
        next_url = ""
    redirect_uri = url_for("auth.github_callback", _external=True)
    return oauth.github.authorize_redirect(redirect_uri, next=next_url)


@bp.get("/github/callback")
def github_callback():
    oauth.github.authorize_access_token()
    userinfo = oauth.github.get("user").json()

    # GitHub "id" is stable; preferred subject
    subject = str(userinfo["id"])
    username = userinfo.get("login")

    # Try get primary email (may be absent/private)
    emails = oauth.github.get("user/emails").json()
    primary = next((e for e in emails if e.get("primary")), None)
    email = primary.get("email") if primary else None
    # GitHub email verification is tricky; treat as unverified unless explicitly true
    email_verified = bool(primary.get("verified")) if primary else False

    user = get_or_create_user_from_oauth(
        provider="github",
        subject=subject,
        email=email,
        email_verified=email_verified,
        username_hint=username,
    )

    login_user(user)
    return redirect(complete_login(user))


@bp.get("/google/login")
def google_login():
    next_url = request.args.get("next", "")
    if next_url and not is_safe_next_url(next_url):
        next_url = ""
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri, next=next_url)


@bp.get("/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    # OpenID Connect userinfo
    claims = oauth.google.parse_id_token(token)

    subject = str(claims["sub"])
    email = claims.get("email")
    email_verified = bool(claims.get("email_verified", False))
    username = claims.get("name") or (email.split("@")[0] if email else None)

    user = get_or_create_user_from_oauth(
        provider="google",
        subject=subject,
        email=email,
        email_verified=email_verified,
        username_hint=username,
    )

    login_user(user)
    return redirect(complete_login(user))
