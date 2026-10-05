"""نموذج الأدوار — أدوار ثابتة يُشار إليها بالاسم البرمجي."""
from datetime import datetime, timezone

from app.extensions import db


ROLE_NAMES = {
    "citizen": "مواطن",
    "police_officer": "ضابط شرطة",
    "operations_manager": "مدير عمليات",
    "director": "مدير عام",
    "administrator": "مسؤول النظام",
}


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, index=True, nullable=False)
    label = db.Column(db.String(64), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    users = db.relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self):
        return f"<Role {self.name}>"