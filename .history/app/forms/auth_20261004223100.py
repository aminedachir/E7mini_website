"""نماذج تسجيل الدخول والتسجيل (رسائل الأخطاء بالعربية)."""
from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import EmailField, PasswordField, StringField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, ValidationError

from app.extensions import db
from app.models import User

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _normalize_email(value):
    return value.strip().lower() if isinstance(value, str) else value


def _strip(value):
    return value.strip() if isinstance(value, str) else value


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


class RegisterForm(FlaskForm):
    name = StringField(
        "الاسم الكامل",
        filters=[_strip],
        validators=[
            DataRequired(message="يرجى إدخال الاسم الكامل."),
            Length(min=2, max=120, message="يجب أن يتراوح الاسم بين 2 و120 حرفًا."),
        ],
    )
    email = EmailField(
        "البريد الإلكتروني",
        filters=[_normalize_email],
        validators=[
            DataRequired(message="يرجى إدخال البريد الإلكتروني."),
            Length(max=254, message="البريد الإلكتروني طويل جدًا."),
            Regexp(EMAIL_PATTERN, message="صيغة البريد الإلكتروني غير صحيحة."),
        ],
    )
    password = PasswordField(
        "كلمة المرور",
        validators=[
            DataRequired(message="يرجى إدخال كلمة المرور."),
            Length(min=8, max=128, message="يجب أن تتكون كلمة المرور من 8 أحرف على الأقل."),
        ],
    )
    confirm_password = PasswordField(
        "تأكيد كلمة المرور",
        validators=[
            DataRequired(message="يرجى تأكيد كلمة المرور."),
            EqualTo("password", message="كلمتا المرور غير متطابقتين."),
        ],
    )

    def validate_email(self, field):
        exists = db.session.execute(
            select(User.id).where(User.email == field.data)
        ).first()
        if exists:
            raise ValidationError("هذا البريد الإلكتروني مسجّل مسبقًا.")
