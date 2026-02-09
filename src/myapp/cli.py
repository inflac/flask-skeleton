import click

from .extensions import db
from .models import User


def register_cli(app):
    @app.cli.command("create-admin")
    @click.argument("email")
    @click.password_option()
    def create_admin(email, password):
        email = email.lower().strip()
        user = User.query.filter_by(email=email).first()
        if user:
            raise click.ClickException("User already exists.")

        user = User(email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Admin created.")
