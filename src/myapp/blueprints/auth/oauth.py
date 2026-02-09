from __future__ import annotations

from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_oauth(app) -> None:
    oauth.init_app(app)

    # GitHub
    if "github" in app.config.get("AUTH_PROVIDERS", []):
        oauth.register(
            name="github",
            client_id=app.config["GITHUB_CLIENT_ID"],
            client_secret=app.config["GITHUB_CLIENT_SECRET"],
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        )

    # Google (OpenID Connect)
    if "google" in app.config.get("AUTH_PROVIDERS", []):
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
