"""لوحة الشرطة — استقبال الشكاوى وعرضها."""
from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import select

from app.extensions import db
from app.models import Complaint
from app.forms.complaint import INDIRECT_CATEGORIES, COMPLAINT_TYPES, REPORT_MODES

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _current_user_role() -> str:
    return current_user.role.name if getattr(current_user, "role", None) else ""


def _require_staff() -> None:
    """يمنع المواطن من الوصول إلى اللوحة."""
    if _current_user_role() == "citizen":
        abort(403)


@dashboard_bp.route("/", methods=["GET"])
@login_required
def index():
    _require_staff()

    category_filter = (request.args.get("category") or "").strip()
    mode_filter = (request.args.get("mode") or "").strip()

    stmt = select(Complaint).order_by(Complaint.created_at.desc())

    if category_filter and category_filter in INDIRECT_CATEGORIES:
        stmt = stmt.where(Complaint.category == category_filter)
    else:
        category_filter = ""

    if mode_filter and mode_filter in REPORT_MODES:
        stmt = stmt.where(Complaint.report_mode == mode_filter)
    else:
        mode_filter = ""

    complaints = db.session.execute(stmt).scalars().all()

    # ترجمات للعرض
    category_labels = INDIRECT_CATEGORIES
    type_labels = dict(COMPLAINT_TYPES)
    mode_labels = REPORT_MODES

    return render_template(
        "dashboard/complaints.html",
        complaints=complaints,
        category_filter=category_filter,
        mode_filter=mode_filter,
        categories=category_labels,
        complaint_types=type_labels,
        modes=mode_labels,
    )