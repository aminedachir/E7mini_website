"""نموذج تقديم بلاغ/شكوى من المواطن (بدون حساب)."""
from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileSize
from wtforms import (
    DateTimeLocalField, DecimalField, HiddenField, SelectField,
    StringField, TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

PHONE_PATTERN = r"^[0-9+\s\-()]{6,20}$"

COMPLAINT_TYPES = [
    ("", "— اختر النوع —"),
    ("theft", "سرقة"),
    ("assault", "اعتداء"),
    ("accident", "حادث مروري"),
    ("fraud", "نصب واحتيال"),
    ("vandalism", "تخريب"),
    ("domestic", "عنف أسري"),
    ("lost", "مفقودات"),
    ("other", "أخرى"),
]

INDIRECT_CATEGORIES = {
    "security": "أمني",
    "cybercrime": "جرائم سيبرانية",
    "natural_disaster": "الكوارث الطبيعية",
    "road_safety": "أمن الطرقات",
}

REPORT_MODES = {
    "direct": "تبليغ مباشر",
    "indirect": "تبليغ غير مباشر",
}


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class ComplaintForm(FlaskForm):
    report_mode = HiddenField(default="indirect")
    category = HiddenField(default="")

    citizen_name = StringField(
        "الاسم الكامل",
        filters=[_strip],
        validators=[
            DataRequired(message="يرجى إدخال الاسم الكامل."),
            Length(min=2, max=120, message="يجب أن يتراوح الاسم بين 2 و120 حرفًا."),
        ],
    )
    citizen_phone = StringField(
        "رقم الهاتف",
        filters=[_strip],
        validators=[
            DataRequired(message="يرجى إدخال رقم الهاتف."),
            Regexp(PHONE_PATTERN, message="صيغة رقم الهاتف غير صحيحة."),
        ],
    )
    complaint_type = SelectField(
        "نوع البلاغ",
        choices=COMPLAINT_TYPES,
        validators=[Optional()],
    )
    description = TextAreaField(
        "وصف البلاغ",
        filters=[_strip],
        validators=[
            DataRequired(message="يرجى كتابة وصف البلاغ."),
            Length(min=10, max=5000, message="يجب أن يتراوح الوصف بين 10 و5000 حرف."),
        ],
    )
    location_description = StringField(
        "وصف الموقع / العنوان",
        filters=[_strip],
        validators=[Optional(), Length(max=255, message="وصف الموقع طويل جدًا.")],
    )
    latitude = DecimalField("خط العرض", places=6, validators=[Optional()])
    longitude = DecimalField("خط الطول", places=6, validators=[Optional()])
    incident_datetime = DateTimeLocalField(
        "تاريخ ووقت الحادث",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message="يرجى تحديد تاريخ ووقت الحادث.")],
    )

    image = FileField(
        "صورة (اختياري)",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"], "صيغة الصورة غير مدعومة."),
            FileSize(max_size=10 * 1024 * 1024, message="حجم الصورة يتجاوز 10 ميغابايت."),
        ],
    )
    video = FileField(
        "فيديو (اختياري)",
        validators=[
            FileAllowed(["mp4", "webm", "mov"], "صيغة الفيديو غير مدعومة."),
            FileSize(max_size=25 * 1024 * 1024, message="حجم الفيديو يتجاوز 25 ميغابايت."),
        ],
    )

    def validate_incident_datetime(self, field):
        value = field.data
        if value is None:
            return
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value > now:
            raise ValidationError("لا يمكن أن يكون وقت الحادث في المستقبل.")