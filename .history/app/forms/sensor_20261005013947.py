"""نموذج إدخال أحداث الزلازل والحرائق."""
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (
    DateTimeLocalField, DecimalField, SelectField,
    StringField, TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from app.models.sensor_event import EVENT_TYPES, SEVERITY_LEVELS


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class SensorEventForm(FlaskForm):
    event_type = SelectField(
        "نوع الحدث",
        choices=[("", "— اختر النوع —")] + list(EVENT_TYPES.items()),
        validators=[DataRequired(message="يرجى اختيار نوع الحدث.")],
    )

    severity = SelectField(
        "درجة الخطورة",
        choices=list(SEVERITY_LEVELS.items()),
        validators=[DataRequired(message="يرجى اختيار درجة الخطورة.")],
    )

    magnitude = DecimalField(
        "قوة الزلزال (Richter) — للزلازل فقط",
        places=1,
        validators=[Optional(), NumberRange(min=0, max=12, message="القيمة يجب أن تكون بين 0 و12.")],
    )

    location_description = StringField(
        "وصف الموقع",
        filters=[_strip],
        validators=[DataRequired(message="يرجى إدخال وصف الموقع."),
                    Length(max=255, message="الوصف طويل جدًا.")],
    )

    latitude = DecimalField("خط العرض", places=6, validators=[Optional()])
    longitude = DecimalField("خط الطول", places=6, validators=[Optional()])

    detected_at = DateTimeLocalField(
        "وقت الكشف",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message="يرجى تحديد وقت الكشف.")],
    )

    details = TextAreaField(
        "تفاصيل إضافية",
        filters=[_strip],
        validators=[Optional(), Length(max=5000, message="النص طويل جدًا.")],
    )

    def validate_detected_at(self, field):
        value = field.data
        if value is None:
            return
        now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
        if value > now:
            raise ValidationError("لا يمكن أن يكون وقت الكشف في المستقبل.")

    def validate_magnitude(self, field):
        # قوة الزلزال مطلوبة فقط عند النوع "زلزال"
        if self.event_type.data == "earthquake":
            if field.data is None:
                raise ValidationError("يرجى إدخال قوة الزلزال.")