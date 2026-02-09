from myapp.models import User


def create_user(
    db, *, email: str, username: str = "u", password: str = "supersecret123", is_admin: bool = False
):
    user = User(email=email, username=username, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, *, email: str, password: str = "supersecret123"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
