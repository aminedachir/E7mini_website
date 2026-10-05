"""Decorators لإدارة الصلاحيات."""
from functools import wraps

from flask import abort, current_app
from flask_login import current_user


def role_required(*allowed_roles: str):
    """يسمح بالوصول فقط لمن لديه دور من القائمة.

    - غير مسجّل → يوجّهه Flask-Login إلى صفحة الدخول.
    - مسجّل بلا صلاحية → 403.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if not current_user.has_role(*allowed_roles):
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(view):
    return role_required("administrator")(view)


def police_required(view):
    return role_required(
        "police_officer", "operations_manager", "director", "administrator"
    )(view)


def operations_required(view):
    return role_required(
        "operations_manager", "director", "administrator"
    )(view)


def director_required(view):
    return role_required("director", "administrator")(view)