"""نماذج تسجيل الدخول الداخلي (رسائل الأخطاء بالعربية)."""
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField
from wtforms.validators import DataRequired, Regexp

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _normalize_email(value):
    return value.strip().lower() if isinstance(value, str) else value


class LoginForm(FlaskForm):
    email = EmailField(
        "البريد الإلكتروني",
        filters=[_normalize_email],
        validators=[
            DataRequired(message="يرجى إدخال البريد الإلكتروني."),
            Regexp(EMAIL_PATTERN, message="صيغة البريد الإلكتروني غير صحيحة."),
        ],
    )
    password = PasswordField(
        "كلمة المرور",
        validators=[DataRequired(message="يرجى إدخال كلمة المرور.")],
    )