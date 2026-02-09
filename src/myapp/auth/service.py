from __future__ import annotations

from urllib.parse import urlparse

from flask import current_app, request
from flask_login import login_user

from ..extensions import db
from ..models import User, auth_identity


def is_safe_next_url(url: str) -> bool:
    """
    Prevent open redirects. Allows only same-host relative URLs.
    """
    if not url:
        return False
    parts = urlparse(url)
    return parts.scheme == "" and parts.netloc == "" and url.startswith("/")


def get_or_create_user_from_oauth(
    *,
    provider: str,
    subject: str,
    email: str | None,
    email_verified: bool,
    username_hint: str | None,
) -> User:
    # 1) identity exists -> login that user
    ident = auth_identity.query.filter_by(provider=provider, subject=subject).first()
    if ident:
        return ident.user

    # 2) optional: link by email only if allowed and trusted
    user = None
    link_by_email = bool(current_app.config.get("AUTH_LINK_BY_EMAIL", False))
    trusted = set(current_app.config.get("AUTH_TRUSTED_EMAIL_PROVIDERS", []))
    if link_by_email and email and email_verified and provider in trusted:
        user = User.query.filter_by(email=email).first()

    # 3) create user if none
    if not user:
        user = User(email=email, username=username_hint)

    db.session.add(user)
    db.session.flush()  # ensure user.id

    db.session.add(
        auth_identity(
            user_id=user.id,
            provider=provider,
            subject=subject,
            email=email,
            email_verified=bool(email_verified),
        )
    )
    db.session.commit()
    return user


def complete_login(user: User) -> str:
    login_user(user)

    next_url = request.args.get("next", "")
    if is_safe_next_url(next_url):
        # Optional: Admin-Ziel abfangen, wenn User kein Admin ist
        if next_url.startswith("/admin") and not getattr(user, "is_admin", False):
            return current_app.config.get("AUTH_AFTER_LOGIN", "/")
        return next_url

    # role-aware fallback
    if getattr(user, "is_admin", False):
        return current_app.config.get("AUTH_DEFAULT_ADMIN_REDIRECT", "/admin")
    return current_app.config.get("AUTH_AFTER_LOGIN", "/")
