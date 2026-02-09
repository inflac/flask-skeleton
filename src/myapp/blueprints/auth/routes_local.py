from __future__ import annotations

from flask import current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user

from ...auth.service import complete_login
from ...extensions import db
from ...models import User
from . import bp
from .forms import LoginForm, RegisterForm


@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(current_app.config.get("AUTH_DEFAULT_REDIRECT", "/admin"))
    form = LoginForm()
    providers = current_app.config.get("AUTH_PROVIDERS", ["local"])
    return render_template("auth/login.html", form=form, providers=providers)


@bp.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(current_app.config.get("AUTH_DEFAULT_REDIRECT", "/admin"))

    form = LoginForm()
    if not form.validate_on_submit():
        providers = current_app.config.get("AUTH_PROVIDERS", ["local"])
        return render_template("auth/login.html", form=form, providers=providers), 400

    email = form.email.data.lower().strip()
    user = User.query.filter_by(email=email).first()

    if not user or not user.is_active or not user.check_password(form.password.data):
        flash("Invalid credentials.", "error")
        providers = current_app.config.get("AUTH_PROVIDERS", ["local"])
        return render_template("auth/login.html", form=form, providers=providers), 401

    login_user(user, remember=bool(form.remember.data))
    return redirect(complete_login(user))


@bp.get("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@bp.get("/register")
def register():
    if not current_app.config.get("AUTH_ALLOW_REGISTRATION", False):
        return redirect(url_for("auth.login"))

    form = RegisterForm()
    return render_template("auth/register.html", form=form)


@bp.post("/register")
def register_post():
    if not current_app.config.get("AUTH_ALLOW_REGISTRATION", False):
        return redirect(url_for("auth.login"))

    form = RegisterForm()
    if not form.validate_on_submit():
        return render_template("auth/register.html", form=form), 400

    username = form.username.data.strip()
    email = form.email.data.lower().strip()

    if User.query.filter((User.email == email) | (User.username == username)).first():
        flash("User already exists.", "error")
        return render_template("auth/register.html", form=form), 409

    user = User(username=username, email=email)
    user.set_password(form.password.data)

    db.session.add(user)
    db.session.commit()

    login_user(user)
    return redirect(complete_login(user))
