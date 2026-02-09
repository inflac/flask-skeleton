from tests.helpers import create_user, login


def test_admin_redirects_to_login_when_anonymous(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "/auth/login" in resp.headers["Location"]


def test_admin_forbidden_for_non_admin(app, client, db):
    with app.app_context():
        create_user(db, email="u@example.com", username="u1", is_admin=False)

    login(client, email="u@example.com")

    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 403


def test_admin_ok_for_admin_user(app, client, db):
    with app.app_context():
        create_user(db, email="admin@example.com", username="admin", is_admin=True)

    login(client, email="admin@example.com")

    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 200
