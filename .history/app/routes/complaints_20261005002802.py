"""مسارات عامة: تقديم بلاغ، متابعة بلاغ برقم المرجع (بدون حساب)."""
import mimetypes
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
from app.forms.complaint import INDIRECT_CATEGORIES, ComplaintForm
from app.models import Complaint, ComplaintAttachment, ComplaintStatusEvent

complaints_bp = Blueprint("complaints", __name__)


ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO_MIMES = {"video/mp4", "video/webm", "video/quicktime"}


def _validate_mime(file_storage, allowed_mimes: set) -> str | None:
    declared = (file_storage.mimetype or "").lower()
    if declared and declared in allowed_mimes:
        return declared
    guessed, _ = mimetypes.guess_type(file_storage.filename or "")
    if guessed and guessed in allowed_mimes:
        return guessed
    return None


def _save_attachment(complaint: Complaint, file_storage, kind: str) -> None:
    """يحفظ مرفقًا واحدًا ويسجّله في جدول complaint_attachments."""
    if not file_storage or not file_storage.filename:
        return

    ext = (file_storage.filename.rsplit(".", 1)[-1] or "").lower()
    if not ext:
        return

    if kind == "image":
        allowed_ext = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
        allowed_mime = ALLOWED_IMAGE_MIMES
    else:
        allowed_ext = current_app.config["ALLOWED_VIDEO_EXTENSIONS"]
        allowed_mime = ALLOWED_VIDEO_MIMES

    if ext not in allowed_ext:
        return
    mime = _validate_mime(file_storage, allowed_mime)
    if not mime:
        return

    token = secrets.token_hex(8)
    filename = f"{kind}_{token}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file_storage.save(path)

    original = secure_filename(file_storage.filename)

    db.session.add(ComplaintAttachment(
        complaint=complaint,
        kind=kind,
        stored_filename=filename,
        original_filename=original[:255] if original else None,
        mime_type=mime,
        size_bytes=os.path.getsize(path),
    ))


def _persist_complaint(form, report_mode: str, category: str | None) -> Complaint:
    complaint = Complaint(
        citizen_name=form.citizen_name.data,
        citizen_phone=form.citizen_phone.data,
        complaint_type=form.complaint_type.data or (category or report_mode),
        report_mode=report_mode,
        category=category,
        description=form.description.data,
        location_description=form.location_description.data or None,
        latitude=float(form.latitude.data) if form.latitude.data is not None else None,
        longitude=float(form.longitude.data) if form.longitude.data is not None else None,
        incident_datetime=form.incident_datetime.data,
        status="تم الاستلام",
    )
    db.session.add(complaint)
    db.session.flush()

    _save_attachment(complaint, form.image.data, "image")
    _save_attachment(complaint, form.video.data, "video")

    db.session.add(ComplaintStatusEvent(
        complaint_id=complaint.id,
        status="تم الاستلام",
        note="تم استلام البلاغ وحفظه في النظام.",
    ))

    db.session.commit()
    return complaint


@complaints_bp.route("/complaint")
def choose():
    return render_template("complaint/choose.html")


@complaints_bp.route("/complaint/direct", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def direct():
    form = ComplaintForm()
    form.report_mode.data = "direct"
    if form.validate_on_submit():
        complaint = _persist_complaint(form, report_mode="direct", category=None)
        return redirect(url_for("complaints.success", reference=complaint.reference_number))
    return render_template("complaint/direct.html", form=form)


@complaints_bp.route("/complaint/indirect")
def indirect():
    return render_template("complaint/indirect.html", categories=INDIRECT_CATEGORIES)


@complaints_bp.route("/complaint/indirect/<category>", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def indirect_category(category: str):
    if category not in INDIRECT_CATEGORIES:
        abort(404)

    form = ComplaintForm()
    form.report_mode.data = "indirect"
    form.category.data = category

    if form.validate_on_submit():
        complaint = _persist_complaint(form, report_mode="indirect", category=category)
        return redirect(url_for("complaints.success", reference=complaint.reference_number))

    return render_template(
        "complaint/indirect_form.html",
        form=form,
        category=category,
        category_label=INDIRECT_CATEGORIES[category],
    )


@complaints_bp.route("/complaint/success/<reference>")
def success(reference: str):
    complaint = db.session.execute(
        select(Complaint).where(Complaint.reference_number == reference)
    ).scalar_one_or_none()
    if not complaint:
        abort(404)
    return render_template("complaint/success.html", complaint=complaint)


@complaints_bp.route("/track", methods=["GET", "POST"])
@limiter.limit("30 per hour", methods=["POST"])
def track():
    reference = None
    complaint = None
    events = []
    if request.method == "POST":
        reference = (request.form.get("reference") or "").strip().upper()
        if reference:
            complaint = db.session.execute(
                select(Complaint).where(Complaint.reference_number == reference)
            ).scalar_one_or_none()
            if complaint:
                events = db.session.execute(
                    select(ComplaintStatusEvent)
                    .where(ComplaintStatusEvent.complaint_id == complaint.id)
                    .order_by(ComplaintStatusEvent.created_at)
                ).scalars().all()
            else:
                flash("لم يتم العثور على بلاغ بهذا الرقم المرجعي.", "warning")
        else:
            flash("يرجى إدخال الرقم المرجعي.", "warning")

    return render_template(
        "complaint/track.html",
        reference=reference,
        complaint=complaint,
        events=events,
    )


@complaints_bp.route("/complaint/media/<int:attachment_id>")
def media(attachment_id: int):
    if not current_user.is_authenticated:
        abort(403)
    att = db.session.get(ComplaintAttachment, attachment_id)
    if not att:
        abort(404)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        att.stored_filename,
        as_attachment=False,
        download_name=att.original_filename or att.stored_filename,
    )