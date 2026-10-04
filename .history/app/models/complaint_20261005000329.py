"""نموذج البلاغ/الشكوى — بيانات المواطن مباشرة دون حساب."""
import secrets
from datetime import datetime, timezone

from app.extensions import db


def _generate_reference() -> str:
    year = datetime.now(timezone.utc).year
    token = secrets.token_hex(4).upper()  # 8 خانات
    return f"DZ-{year}-{token}"


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(
        db.String(32), unique=True, index=True, nullable=False,
        default=_generate_reference,
    )

    # بيانات المواطن (مباشرة، بدون ربط بحساب)
    citizen_name = db.Column(db.String(120), nullable=False)
    citizen_phone = db.Column(db.String(32), nullable=False, index=True)

    # نوع التبليغ: direct أو indirect
    report_kind = db.Column(db.String(16), nullable=False, default="indirect", index=True)
    # الفئة للتبليغ غير المباشر فقط: security / cyber / disaster / traffic
    category = db.Column(db.String(32), nullable=True, index=True)

    complaint_type = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_description = db.Column(db.String(255), nullable=True)

    incident_datetime = db.Column(db.DateTime(timezone=True), nullable=False)

    # أسماء الملفات داخل UPLOAD_FOLDER (بدون كشف عام)
    image_filename = db.Column(db.String(255), nullable=True)
    video_filename = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(32), nullable=False, default="new", index=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Complaint {self.reference_number}>"