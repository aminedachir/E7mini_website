"""نموذج أحداث الزلازل والحرائق — يُدخله الموظف يدويًا من تطبيقَي القياس."""
from datetime import datetime, timezone

from app.extensions import db


EVENT_TYPES = {
    "earthquake": "زلزال",
    "fire": "حريق",
}

SEVERITY_LEVELS = {
    "low": "منخفضة",
    "medium": "متوسطة",
    "high": "عالية",
    "critical": "حرجة",
}


class SensorEvent(db.Model):
    __tablename__ = "sensor_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(16), nullable=False, index=True)
    # "earthquake" | "fire"

    severity = db.Column(db.String(16), nullable=False, default="medium", index=True)
    # "low" | "medium" | "high" | "critical"

    magnitude = db.Column(db.Float, nullable=True)
    # يُستخدم للزلازل فقط. يُترك فارغًا للحرائق.

    location_description = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    detected_at = db.Column(db.DateTime(timezone=True), nullable=False)
    details = db.Column(db.Text, nullable=True)

    reported_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    reported_by = db.relationship("User", lazy="joined")

    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def event_type_label(self) -> str:
        return EVENT_TYPES.get(self.event_type or "", "—")

    @property
    def severity_label(self) -> str:
        return SEVERITY_LEVELS.get(self.severity or "", "—")

    def __repr__(self) -> str:
        return f"<SensorEvent {self.event_type} {self.severity}>"