"""نموذج البلاغ/الشكوى — بيانات المواطن مباشرة دون حساب."""
import secrets
from datetime import datetime, timezone

from app.extensions import db


def _generate_reference() -> str:
    year = datetime.now(timezone.utc).year
    token = secrets.token_hex(4).upper()
    return f"DZ-{year}-{token}"


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(
        db.String(32), unique=True, index=True, nullable=False,
        default=_generate_reference,
    )

    # بيانات المواطن
    citizen_name = db.Column(db.String(120), nullable=False)
    citizen_phone = db.Column(db.String(32), nullable=False, index=True)

    # وضع التبليغ والفئة
    report_mode = db.Column(db.String(16), nullable=False, default="indirect", index=True)
    # "direct" | "indirect"
    category = db.Column(db.String(32), nullable=True, index=True)
    # "security" | "cybercrime" | "natural_disaster" | "road_safety"

    complaint_type = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_description = db.Column(db.String(255), nullable=True)

    incident_datetime = db.Column(db.DateTime(timezone=True), nullable=False)

    # الحالة بالعربية
    status = db.Column(db.String(32), nullable=False, default="تم الاستلام", index=True)

    # الجهة الموجَّه إليها
    assigned_to = db.Column(db.String(32), nullable=True, index=True)
    # "police" | "gendarme" | "civil_protection" | "drone" | NULL

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # علاقات
    attachments = db.relationship(
        "ComplaintAttachment", back_populates="complaint",
        cascade="all, delete-orphan", lazy="selectin",
    )
    status_events = db.relationship(
        "ComplaintStatusEvent", cascade="all, delete-orphan",
        order_by="ComplaintStatusEvent.created_at", lazy="selectin",
    )

    ASSIGNMENT_LABELS = {
        "police": "الشرطة",
        "gendarme": "الدرك الوطني",
        "civil_protection": "الحماية المدنية",
        "drone": "وحدة الدرون",
    }

    @property
    def assigned_to_label(self) -> str:
        return self.ASSIGNMENT_LABELS.get(self.assigned_to or "", "—")

    def __repr__(self) -> str:
        return f"<Complaint {self.reference_number}>"


class ComplaintAttachment(db.Model):
    __tablename__ = "complaint_attachments"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    kind = db.Column(db.String(16), nullable=False)  # "image" | "video"
    stored_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    mime_type = db.Column(db.String(128), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    complaint = db.relationship("Complaint", back_populates="attachments")


class ComplaintStatusEvent(db.Model):
    __tablename__ = "complaint_status_events"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    status = db.Column(db.String(32), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )