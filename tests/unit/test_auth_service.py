from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import myapp.auth.service as svc

# ----------------------------
# Helpers (fakes/mocks)
# ----------------------------


class FakeQuery:
    """Very small query stub: filter_by(...).first()"""

    def __init__(self, first_result=None):
        self._first_result = first_result
        self.last_filter_kwargs = None

    def filter_by(self, **kwargs):
        self.last_filter_kwargs = kwargs
        return self

    def first(self):
        return self._first_result


class FakeSession:
    def __init__(self):
        self.added = []
        self.flushed = 0
        self.committed = 0

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed += 1

    def commit(self):
        self.committed += 1


@dataclass
class FakeUser:
    email: str | None = None
    username: str | None = None
    id: int | None = None

    # In Flask-Login, login_user checks is_active attribute/property.
    is_active: bool = True


class FakeUserModel:
    """Acts like the SQLAlchemy model class 'User' with .query"""

    def __init__(self, existing_user_by_email: FakeUser | None = None):
        self.query = FakeQuery(first_result=existing_user_by_email)

    def __call__(self, email=None, username=None):
        return FakeUser(email=email, username=username)


class FakeIdentityRow:
    """Represents an identity row returned by auth_identity.query.first()."""

    def __init__(self, user: FakeUser):
        self.user = user


class FakeAuthIdentityModel:
    """Acts like a SQLAlchemy model class 'AuthIdentity' with .query and callable constructor."""

    def __init__(self, existing_identity: FakeIdentityRow | None = None):
        self.query = FakeQuery(first_result=existing_identity)
        self.created_rows = []

    def __call__(self, **kwargs):
        # return an object representing the created identity row
        row = SimpleNamespace(**kwargs)
        self.created_rows.append(row)
        return row


# ----------------------------
# is_safe_next_url
# ----------------------------


@pytest.mark.parametrize(
    "url, expected",
    [
        ("/admin", True),
        ("/auth/login?next=/admin", True),
        ("", False),
        ("admin", False),
        ("//evil.com/x", False),
        ("http://evil.com/x", False),
        ("https://evil.com/x", False),
    ],
)
def test_is_safe_next_url(url: str, expected: bool) -> None:
    assert svc.is_safe_next_url(url) is expected


# ----------------------------
# get_or_create_user_from_oauth
# ----------------------------


def test_get_or_create_user_identity_exists_returns_existing_user(app, monkeypatch):
    with app.app_context():
        existing_user = FakeUser(email="x@example.com", username="x", id=123)

        fake_user_model = FakeUserModel(existing_user_by_email=None)
        fake_ident_model = FakeAuthIdentityModel(existing_identity=FakeIdentityRow(existing_user))
        fake_session = FakeSession()

        monkeypatch.setattr(svc, "User", fake_user_model)
        monkeypatch.setattr(svc, "auth_identity", fake_ident_model)
        monkeypatch.setattr(svc, "db", SimpleNamespace(session=fake_session))

        got = svc.get_or_create_user_from_oauth(
            provider="google",
            subject="sub-123",
            email="x@example.com",
            email_verified=True,
            username_hint="ignored",
        )

        assert got is existing_user
        # since identity existed, no writes:
        assert fake_session.added == []
        assert fake_session.committed == 0


def test_get_or_create_user_creates_new_user_and_identity_when_no_linking(app, monkeypatch):
    with app.app_context():
        app.config["AUTH_LINK_BY_EMAIL"] = False
        app.config["AUTH_TRUSTED_EMAIL_PROVIDERS"] = ["google"]

        fake_user_model = FakeUserModel(existing_user_by_email=None)
        fake_ident_model = FakeAuthIdentityModel(existing_identity=None)
        fake_session = FakeSession()

        monkeypatch.setattr(svc, "User", fake_user_model)
        monkeypatch.setattr(svc, "auth_identity", fake_ident_model)
        monkeypatch.setattr(svc, "db", SimpleNamespace(session=fake_session))

        # Make flush assign an id like SQLAlchemy would after INSERT
        def flush_and_assign_id():
            fake_session.flushed += 1
            # first added object is the user we created
            for obj in fake_session.added:
                if isinstance(obj, FakeUser) and obj.id is None:
                    obj.id = 1

        fake_session.flush = flush_and_assign_id  # type: ignore[method-assign]

        got = svc.get_or_create_user_from_oauth(
            provider="google",
            subject="sub-new",
            email="new@example.com",
            email_verified=True,
            username_hint="newuser",
        )

        assert isinstance(got, FakeUser)
        assert got.id == 1
        assert got.email == "new@example.com"
        assert got.username == "newuser"

        # Writes happened
        assert fake_session.committed == 1
        # identity row created with correct fields
        assert len(fake_ident_model.created_rows) == 1
        row = fake_ident_model.created_rows[0]
        assert row.user_id == 1
        assert row.provider == "google"
        assert row.subject == "sub-new"
        assert row.email == "new@example.com"
        assert row.email_verified is True


def test_get_or_create_user_does_not_link_if_provider_not_trusted(app, monkeypatch):
    with app.app_context():
        existing = FakeUser(email="linkme@example.com", username="existing", id=10)

        app.config["AUTH_LINK_BY_EMAIL"] = True
        app.config["AUTH_TRUSTED_EMAIL_PROVIDERS"] = ["google"]  # github not trusted

        fake_user_model = FakeUserModel(existing_user_by_email=existing)
        fake_ident_model = FakeAuthIdentityModel(existing_identity=None)
        fake_session = FakeSession()

        monkeypatch.setattr(svc, "User", fake_user_model)
        monkeypatch.setattr(svc, "auth_identity", fake_ident_model)
        monkeypatch.setattr(svc, "db", SimpleNamespace(session=fake_session))

        def flush_assign():
            fake_session.flushed += 1
            for obj in fake_session.added:
                if isinstance(obj, FakeUser) and obj.id is None:
                    obj.id = 2

        fake_session.flush = flush_assign  # type: ignore[method-assign]

        got = svc.get_or_create_user_from_oauth(
            provider="github",
            subject="sub-gh",
            email="linkme@example.com",
            email_verified=True,
            username_hint="hint",
        )

        # provider not trusted => do NOT use existing
        assert got.id == 2
        assert got.email == "linkme@example.com"


def test_get_or_create_user_does_not_link_if_email_not_verified(app, monkeypatch):
    with app.app_context():
        existing = FakeUser(email="linkme2@example.com", username="existing2", id=11)

        app.config["AUTH_LINK_BY_EMAIL"] = True
        app.config["AUTH_TRUSTED_EMAIL_PROVIDERS"] = ["google"]

        fake_user_model = FakeUserModel(existing_user_by_email=existing)
        fake_ident_model = FakeAuthIdentityModel(existing_identity=None)
        fake_session = FakeSession()

        monkeypatch.setattr(svc, "User", fake_user_model)
        monkeypatch.setattr(svc, "auth_identity", fake_ident_model)
        monkeypatch.setattr(svc, "db", SimpleNamespace(session=fake_session))

        def flush_assign():
            fake_session.flushed += 1
            for obj in fake_session.added:
                if isinstance(obj, FakeUser) and obj.id is None:
                    obj.id = 3

        fake_session.flush = flush_assign  # type: ignore[method-assign]

        got = svc.get_or_create_user_from_oauth(
            provider="google",
            subject="sub-unverified",
            email="linkme2@example.com",
            email_verified=False,  # key
            username_hint="hint",
        )

        assert got.id == 3
        assert got.email == "linkme2@example.com"


def test_get_or_create_user_links_existing_user_by_email_when_allowed_and_trusted(app, monkeypatch):
    with app.app_context():
        existing = FakeUser(email="trusted@example.com", username="existing3", id=12)

        app.config["AUTH_LINK_BY_EMAIL"] = True
        app.config["AUTH_TRUSTED_EMAIL_PROVIDERS"] = ["google"]

        fake_user_model = FakeUserModel(existing_user_by_email=existing)
        fake_ident_model = FakeAuthIdentityModel(existing_identity=None)
        fake_session = FakeSession()

        monkeypatch.setattr(svc, "User", fake_user_model)
        monkeypatch.setattr(svc, "auth_identity", fake_ident_model)
        monkeypatch.setattr(svc, "db", SimpleNamespace(session=fake_session))

        got = svc.get_or_create_user_from_oauth(
            provider="google",
            subject="sub-linked",
            email="trusted@example.com",
            email_verified=True,
            username_hint="ignored",
        )

        # linked to existing user
        assert got is existing
        assert fake_session.committed == 1
        assert len(fake_ident_model.created_rows) == 1
        assert fake_ident_model.created_rows[0].user_id == 12


# ----------------------------
# complete_login
# ----------------------------


def test_complete_login_returns_safe_next_url(app, monkeypatch):
    # don't hit flask-login internals; unit-test routing logic
    monkeypatch.setattr(svc, "login_user", lambda user: None)

    u = FakeUser(email="login1@example.com", username="u1", id=1)

    with app.test_request_context("/any?next=/admin"):
        target = svc.complete_login(u)
        assert target == "/admin"


def test_complete_login_falls_back_to_default_when_next_unsafe(app, monkeypatch):
    monkeypatch.setattr(svc, "login_user", lambda user: None)

    u = FakeUser(email="login2@example.com", username="u2", id=2)

    with app.test_request_context("/any?next=https://evil.com/phish"):
        target = svc.complete_login(u)
        assert target == app.config.get("AUTH_DEFAULT_REDIRECT", "/admin")


def test_complete_login_falls_back_to_default_when_next_missing(app, monkeypatch):
    monkeypatch.setattr(svc, "login_user", lambda user: None)

    u = FakeUser(email="login3@example.com", username="u3", id=3)

    with app.test_request_context("/any"):
        target = svc.complete_login(u)
        assert target == app.config.get("AUTH_DEFAULT_REDIRECT", "/admin")
