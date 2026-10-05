"""لوحة الشرطة — استقبال الشكاوى وأحداث الزلازل والحرائق."""
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
from app.forms.sensor import SensorEventForm
from app.models import Complaint, ComplaintStatusEvent, SensorEvent
from app.models.sensor_event import EVENT_TYPES, SEVERITY_LEVELS

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _current_user_role() -> str:
    return current_user.role.name if getattr(current_user, "role", None) else ""


def _require_staff() -> None:
    if _current_user_role() == "citizen":
        abort(403)


def _suggest_assignment(complaint: Complaint) -> str:
    if complaint.category in {"security", "cybercrime"}:
        return "police"
    if complaint.category == "natural_disaster":
        return "civil_protection"
    if complaint.category == "road_safety":
        return "gendarme"
    if complaint.complaint_type in {"domestic", "lost"}:
        return "police"
    return ""


# ===================== الشكاوى =====================

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


# ===================== الزلازل والحرائق =====================

@dashboard_bp.route("/sensors", methods=["GET"])
@login_required
def sensors_list():
    _require_staff()

    type_filter = (request.args.get("type") or "").strip()
    severity_filter = (request.args.get("severity") or "").strip()

    stmt = select(SensorEvent).order_by(SensorEvent.detected_at.desc())

    if type_filter and type_filter in EVENT_TYPES:
        stmt = stmt.where(SensorEvent.event_type == type_filter)
    else:
        type_filter = ""

    if severity_filter and severity_filter in SEVERITY_LEVELS:
        stmt = stmt.where(SensorEvent.severity == severity_filter)
    else:
        severity_filter = ""

    events = db.session.execute(stmt).scalars().all()

    return render_template(
        "dashboard/sensors.html",
        events=events,
        type_filter=type_filter,
        severity_filter=severity_filter,
        event_types=EVENT_TYPES,
        severities=SEVERITY_LEVELS,
    )


@dashboard_bp.route("/sensors/new", methods=["GET", "POST"])
@login_required
def sensor_new():
    _require_staff()

    form = SensorEventForm()
    if form.validate_on_submit():
        event = SensorEvent(
            event_type=form.event_type.data,
            severity=form.severity.data,
            magnitude=float(form.magnitude.data) if form.magnitude.data is not None else None,
            location_description=form.location_description.data or None,
            latitude=float(form.latitude.data) if form.latitude.data is not None else None,
            longitude=float(form.longitude.data) if form.longitude.data is not None else None,
            detected_at=form.detected_at.data,
            details=form.details.data or None,
            reported_by_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(event)
        db.session.commit()
        flash("تم تسجيل الحدث بنجاح.", "success")
        return redirect(url_for("dashboard.sensor_detail", event_id=event.id))

    return render_template(
        "dashboard/sensor_new.html",
        form=form,
        event_types=EVENT_TYPES,
        severities=SEVERITY_LEVELS,
    )


@dashboard_bp.route("/sensors/<int:event_id>", methods=["GET"])
@login_required
def sensor_detail(event_id: int):
    _require_staff()
    event = db.session.get(SensorEvent, event_id)
    if not event:
        abort(404)
    return render_template("dashboard/sensor_detail.html", event=event)


@dashboard_bp.route("/sensors/<int:event_id>/delete", methods=["POST"])
@login_required
def sensor_delete(event_id: int):
    _require_staff()
    event = db.session.get(SensorEvent, event_id)
    if not event:
        abort(404)
    db.session.delete(event)
    db.session.commit()
    flash("تم حذف الحدث.", "success")
    return redirect(url_for("dashboard.sensors_list"))