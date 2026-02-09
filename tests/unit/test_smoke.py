def test_login_page_ok(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200
