"""مسارات عامة: تقديم بلاغ، متابعة بلاغ برقم المرجع (بدون حساب)."""
import os
import secrets

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, send_from_directory, url_for,
)
from flask_login import current_user
from sqlalchemy import select
from werkzeug.utils import secure_filename

from app.extensions import db, limiter
from app.forms.complaint import ComplaintForm
from app.models import Complaint

complaints_bp = Blueprint("complaints", __name__)


def _public_status_label(status: str) -> str:
    return {
        "new": "تم الاستلام",
        "in_review": "قيد المراجعة",
        "assigned": "قيد المعالجة",
        "resolved": "تمت المعالجة",
        "closed": "مغلق",
    }.get(status, "قيد المعالجة")


def _save_upload(file_storage, prefix: str):
    if not file_storage or not file_storage.filename:
        return None
    original = secure_filename(file_storage.filename)
    if not original or "." not in original:
        return None
    ext = original.rsplit(".", 1)[-1].lower()
    token = secrets.token_hex(8)
    filename = f"{prefix}_{token}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return filename


@complaints_bp.route("/complaint", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def new():
    form = ComplaintForm()
    if form.validate_on_submit():
        image_name = _save_upload(form.image.data, "img")
        video_name = _save_upload(form.video.data, "vid")

        complaint = Complaint(
            citizen_name=form.citizen_name.data,
            citizen_phone=form.citizen_phone.data,
            complaint_type=form.complaint_type.data,
            description=form.description.data,
            location_description=form.location_description.data or None,
            latitude=float(form.latitude.data) if form.latitude.data is not None else None,
            longitude=float(form.longitude.data) if form.longitude.data is not None else None,
            incident_datetime=form.incident_datetime.data,
            image_filename=image_name,
            video_filename=video_name,
            status="new",
        )
        db.session.add(complaint)
        db.session.commit()
        return redirect(url_for("complaints.success", reference=complaint.reference_number))

    return render_template("complaint/new.html", form=form)


@complaints_bp.route("/complaint/success/<reference>")
def success(reference: str):
    complaint = db.session.execute(
        select(Complaint).where(Complaint.reference_number == reference)
    ).scalar_one_or_none()
    if not complaint:
        abort(404)
    return render_template(
        "complaint/success.html",
        complaint=complaint,
        status_label=_public_status_label(complaint.status),
    )


@complaints_bp.route("/track", methods=["GET", "POST"])
@limiter.limit("30 per hour", methods=["POST"])
def track():
    reference = None
    complaint = None
    if request.method == "POST":
        reference = (request.form.get("reference") or "").strip().upper()
        if reference:
            complaint = db.session.execute(
                select(Complaint).where(Complaint.reference_number == reference)
            ).scalar_one_or_none()
            if not complaint:
                flash("لم يتم العثور على بلاغ بهذا الرقم المرجعي.", "warning")
        else:
            flash("يرجى إدخال الرقم المرجعي.", "warning")

    return render_template(
        "complaint/track.html",
        reference=reference,
        complaint=complaint,
        status_label=_public_status_label(complaint.status) if complaint else None,
    )


@complaints_bp.route("/complaint/media/<int:complaint_id>/<kind>")
def media(complaint_id: int, kind: str):
    if not current_user.is_authenticated:
        abort(403)
    if kind not in {"image", "video"}:
        abort(404)
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        abort(404)
    filename = complaint.image_filename if kind == "image" else complaint.video_filename
    if not filename:
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)