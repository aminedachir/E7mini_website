"""مسارات المصادقة الداخلية: تسجيل الدخول، تسجيل الخروج."""
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select

from app.extensions import db
from app.forms.auth import LoginForm
from app.models import User

auth_bp = Blueprint("auth", __name__)


def _safe_next_url(target):
    """يقبل مسارًا داخليًا فقط لمنع إعادة التوجيه إلى مواقع خارجية."""
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    if "\\" in target:
        return None
    return target


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(
            select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()

        if user and user.is_active and user.check_password(form.password.data):
            login_user(user)
            return redirect(_safe_next_url(request.args.get("next")) or url_for("main.home"))

        flash("البريد الإلكتروني أو كلمة المرور غير صحيحة.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("تم تسجيل الخروج بنجاح.", "success")
    return redirect(url_for("main.home"))