"""نماذج لوحة الشرطة — تحديث حالة الشكوى."""
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import Length, Optional


COMPLAINT_STATUSES = [
    ("تم الاستلام", "تم الاستلام"),
    ("قيد المراجعة", "قيد المراجعة"),
    ("تم التوجيه", "تم التوجيه"),
    ("قيد المعالجة", "قيد المعالجة"),
    ("مغلقة", "مغلقة"),
]


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class ComplaintStatusForm(FlaskForm):
    status = SelectField(
        "الحالة الجديدة",
        choices=COMPLAINT_STATUSES,
        validators=[Optional()],
    )
    note = StringField(
        "ملاحظة (اختياري)",
        filters=[_strip],
        validators=[Optional(), Length(max=255, message="الملاحظة طويلة جدًا.")],
    )
    submit = SubmitField("تحديث الحالة")