"""لوحة الشرطة — استقبال الشكاوى وإدارتها."""
from flask import (
    Blueprint, abort, flash, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import select

from app.extensions import db
from app.forms.complaint import (
    COMPLAINT_TYPES,
    INDIRECT_CATEGORIES,
    REPORT_MODES,
)
from app.forms.complaint_admin import (
    ASSIGNMENT_CHOICES,
    COMPLAINT_STATUSES,
    ComplaintAssignForm,
    ComplaintStatusForm,
)
from app.models import Complaint, ComplaintStatusEvent

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _current_user_role() -> str:
    return current_user.role.name if getattr(current_user, "role", None) else ""


def _require_staff() -> None:
    """يمنع المواطن من الوصول إلى اللوحة."""
    if _current_user_role() == "citizen":
        abort(403)


def _suggest_assignment(complaint: Complaint) -> str:
    """اقتراح جهة بناءً على نوع الشكوى. يعيد مفتاحًا أو ''."""
    if complaint.category in {"security", "cybercrime"}:
        return "police"
    if complaint.category == "natural_disaster":
        return "civil_protection"
    if complaint.category == "road_safety":
        return "gendarme"
    if complaint.complaint_type in {"domestic", "lost"}:
        return "police"
    return ""


@dashboard_bp.route("/", methods=["GET"])
@login_required
def index():
    _require_staff()

    category_filter = (request.args.get("category") or "").strip()
    mode_filter = (request.args.get("mode") or "").strip()
    assignment_filter = (request.args.get("assigned") or "").strip()

    stmt = select(Complaint).order_by(Complaint.created_at.desc())

    if category_filter and category_filter in INDIRECT_CATEGORIES:
        stmt = stmt.where(Complaint.category == category_filter)
    else:
        category_filter = ""

    if mode_filter and mode_filter in REPORT_MODES:
        stmt = stmt.where(Complaint.report_mode == mode_filter)
    else:
        mode_filter = ""

    valid_assign = {key for key, _ in ASSIGNMENT_CHOICES if key}
    if assignment_filter and assignment_filter in valid_assign:
        stmt = stmt.where(Complaint.assigned_to == assignment_filter)
    else:
        assignment_filter = ""

    complaints = db.session.execute(stmt).scalars().all()

    return render_template(
        "dashboard/complaints.html",
        complaints=complaints,
        category_filter=category_filter,
        mode_filter=mode_filter,
        assignment_filter=assignment_filter,
        categories=INDIRECT_CATEGORIES,
        complaint_types=dict(COMPLAINT_TYPES),
        modes=REPORT_MODES,
        assignments=ASSIGNMENT_CHOICES,
    )


@dashboard_bp.route("/complaints/<int:complaint_id>", methods=["GET"])
@login_required
def complaint_detail(complaint_id: int):
    _require_staff()
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        abort(404)

    form = ComplaintStatusForm()
    form.status.data = complaint.status

    assign_form = ComplaintAssignForm()
    assign_form.assigned_to.data = complaint.assigned_to or ""
    suggested = _suggest_assignment(complaint)

    events = db.session.execute(
        select(ComplaintStatusEvent)
        .where(ComplaintStatusEvent.complaint_id == complaint.id)
        .order_by(ComplaintStatusEvent.created_at)
    ).scalars().all()

    return render_template(
        "dashboard/complaint.html",
        complaint=complaint,
        form=form,
        assign_form=assign_form,
        suggested_assignment=suggested,
        events=events,
        statuses=COMPLAINT_STATUSES,
        assignments=ASSIGNMENT_CHOICES,
    )


@dashboard_bp.route("/complaints/<int:complaint_id>/status", methods=["POST"])
@login_required
def update_status(complaint_id: int):
    _require_staff()
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        abort(404)

    form = ComplaintStatusForm()
    if form.validate_on_submit():
        new_status = form.status.data
        valid_values = {value for value, _ in COMPLAINT_STATUSES}
        if new_status not in valid_values:
            flash("الحالة المحددة غير صحيحة.", "danger")
            return redirect(url_for("dashboard.complaint_detail", complaint_id=complaint.id))

        note = (form.note.data or "").strip()
        if new_status != complaint.status or note:
            complaint.status = new_status
            db.session.add(ComplaintStatusEvent(
                complaint_id=complaint.id,
                status=new_status,
                note=note or None,
            ))
            db.session.commit()
            flash("تم تحديث الحالة.", "success")
        else:
            flash("لم يحدث أي تغيير.", "info")

    return redirect(url_for("dashboard.complaint_detail", complaint_id=complaint.id))


@dashboard_bp.route("/complaints/<int:complaint_id>/assign", methods=["POST"])
@login_required
def assign_complaint(complaint_id: int):
    _require_staff()
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        abort(404)

    form = ComplaintAssignForm()
    if form.validate_on_submit():
        new_assign = form.assigned_to.data or None
        valid_keys = {key for key, _ in ASSIGNMENT_CHOICES if key}
        if new_assign and new_assign not in valid_keys:
            flash("الجهة المحددة غير صحيحة.", "danger")
            return redirect(url_for("dashboard.complaint_detail", complaint_id=complaint.id))

        note = (form.note.data or "").strip()
        changed = new_assign != complaint.assigned_to

        if changed or note:
            complaint.assigned_to = new_assign

            if new_assign and complaint.status != "تم التوجيه":
                complaint.status = "تم التوجيه"

            if new_assign:
                label = complaint.assigned_to_label
                event_note = f"تم التوجيه إلى {label}"
            else:
                event_note = "تم إلغاء التوجيه"

            if note:
                event_note = f"{event_note} — {note}"

            db.session.add(ComplaintStatusEvent(
                complaint_id=complaint.id,
                status=complaint.status,
                note=event_note,
            ))
            db.session.commit()
            flash("تم حفظ التوجيه.", "success")
        else:
            flash("لم يحدث أي تغيير.", "info")

    return redirect(url_for("dashboard.complaint_detail", complaint_id=complaint.id))