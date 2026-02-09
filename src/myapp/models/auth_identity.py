from __future__ import annotations

from datetime import datetime

from ..extensions import db


class AuthIdentity(db.Model):
    __tablename__ = "auth_identities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    provider = db.Column(db.String(32), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False, index=True)

    email = db.Column(db.String(255), nullable=True)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    user = db.relationship(
        "User",
        backref=db.backref("identities", cascade="all, delete-orphan"),
    )

    __table_args__ = (db.UniqueConstraint("provider", "subject", name="uq_provider_subject"),)
