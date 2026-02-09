def test_register_then_login(client):
    # register
    resp = client.post(
        "/auth/register",
        data={"username": "testuser", "email": "test@example.com", "password": "supersecret123"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)

    # logout
    client.post("/auth/logout")

    # login
    resp = client.post(
        "/auth/login",
        data={"email": "test@example.com", "password": "supersecret123"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
