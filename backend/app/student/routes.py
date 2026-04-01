"""Student profile and dashboard routes."""

from datetime import datetime, timezone
from math import ceil

from flask import Blueprint, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, or_

from app.auth.utils import role_required
from app.auth.validators import validate_required_fields
from app.models import (
    ActivityLog,
    Application,
    Company,
    Interview,
    Notification,
    Placement,
    PlacementDrive,
    PlacementOffer,
    Student,
    db,
)

student_bp = Blueprint("student", __name__)

# ✅ Allowed ENUM values (MUST match your DB)
VALID_BRANCHES = {"CSE", "ECE", "MECH", "EE", "OTHER"}

# ✅ Mapping user input → enum
BRANCH_MAP = {
    "cse": "CSE",
    "computer science": "CSE",
    "ece": "ECE",
    "electronics": "ECE",
    "mech": "MECH",
    "mechanical": "MECH",
    "ee": "EE",
    "electrical": "EE",
    "other": "OTHER",
}

MAX_LIMIT = 100
ALLOWED_APPLICATION_STATUSES = {
    "applied",
    "shortlisted",
    "selected",
    "interviewed",
    "rejected",
    "waitlisted",
}
ALLOWED_OFFER_RESPONSE_STATUSES = {"accepted", "rejected"}


def _json_error(message, status_code=400):
    """Return a consistent JSON error payload."""
    return jsonify({"success": False, "error": message}), status_code


def _normalized_json_payload():
    """Return request JSON with surrounding whitespace trimmed from string values."""
    data = request.get_json(silent=True) or {}
    return {
        key: value.strip() if isinstance(value, str) else value
        for key, value in data.items()
    }


def _validate_student_profile_payload(data):
    """Validate and normalize student profile fields used by the dashboard."""
    required_fields = ["college_name", "branch", "year", "cgpa", "roll_number"]
    missing_message = validate_required_fields(data, required_fields)
    if missing_message:
        return missing_message, None

    branch_raw = str(data.get("branch") or "").strip()
    normalized_branch = BRANCH_MAP.get(branch_raw.lower(), branch_raw.upper())
    if normalized_branch not in VALID_BRANCHES:
        return "Invalid branch value", None

    college_name = str(data.get("college_name") or "").strip()
    roll_number = str(data.get("roll_number") or "").strip()

    try:
        year = int(data.get("year"))
    except (TypeError, ValueError):
        return "Year must be a valid integer", None
    if year <= 0:
        return "Year must be greater than 0", None

    try:
        cgpa = float(data.get("cgpa"))
    except (TypeError, ValueError):
        return "CGPA must be a valid number", None
    if cgpa < 0 or cgpa > 10:
        return "CGPA must be between 0 and 10", None

    phone = str(data.get("phone") or "").strip()
    if phone and len(phone) > 20:
        return "Phone must be 20 characters or fewer", None

    resume_url = str(data.get("resume_url") or "").strip()
    if resume_url and len(resume_url) > 500:
        return "Resume URL must be 500 characters or fewer", None

    skills_raw = data.get("skills")
    if isinstance(skills_raw, list):
        normalized_skills = ", ".join(
            [str(item).strip() for item in skills_raw if str(item).strip()]
        )
    else:
        normalized_skills = str(skills_raw or "").strip()

    experience_summary = str(data.get("experience_summary") or "").strip()

    normalized = {
        "college_name": college_name,
        "branch": normalized_branch,
        "year": year,
        "cgpa": cgpa,
        "roll_number": roll_number,
        "phone": phone or None,
        "resume_url": resume_url or None,
        "skills": normalized_skills or None,
        "experience_summary": experience_summary or None,
    }

    return None, normalized


def _student_profile_payload(student):
    payload = student.to_dict()
    payload.update(
        {
            "skills": payload.get("skills") or "",
            "experience_summary": payload.get("experience_summary") or "",
            "resume_url": payload.get("resume_url") or "",
            "phone": payload.get("phone") or "",
        }
    )
    return payload

    return None, year, cgpa


def _current_user_id():
    identity = get_jwt_identity()
    raw_user_id = identity.get("user_id") if isinstance(identity, dict) else identity
    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        return None


def _student_for_user(user_id):
    return Student.query.filter_by(user_id=user_id).first()


def _append_student_activity(user_id, action, target=None, status="info"):
    try:
        actor_id = int(user_id)
    except (TypeError, ValueError):
        return

    db.session.add(
        ActivityLog(
            user_id=actor_id,
            action=(action or "Student Action").strip(),
            target=(target or "").strip() or None,
            status=(status or "info").strip().lower() or "info",
        )
    )


def _create_company_notification(
    company_id,
    title,
    message,
    sender_id=None,
    resource_type="offer",
    resource_id=None,
):
    company = db.session.get(Company, company_id)
    if not company or not company.user_id:
        return

    db.session.add(
        Notification(
            recipient_id=company.user_id,
            sender_id=sender_id,
            notification_type="in_app",
            title=(title or "Update").strip()[:200],
            message=(message or "").strip() or "You have a new update.",
            related_resource_type=(resource_type or "offer").strip()[:100],
            related_resource_id=resource_id,
            delivery_status="sent",
        )
    )


def _parse_pagination():
    page_raw = request.args.get("page", "1")
    limit_raw = request.args.get("limit", "10")

    try:
        page = int(page_raw)
        limit = int(limit_raw)
    except (TypeError, ValueError):
        return None, None, _json_error("page and limit must be integers", 400)

    if page < 1:
        return None, None, _json_error("page must be greater than 0", 400)
    if limit < 1:
        return None, None, _json_error("limit must be greater than 0", 400)

    return page, min(limit, MAX_LIMIT), None


def _parse_bool_param(value, default=False):
    raw = str(value if value is not None else "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y"}


def _normalized_upper_set(values):
    if not isinstance(values, list):
        return set()
    return {
        str(item).strip().upper()
        for item in values
        if str(item).strip()
    }


def _normalized_int_set(values):
    if not isinstance(values, list):
        return set()

    normalized = set()
    for item in values:
        try:
            normalized.add(int(item))
        except (TypeError, ValueError):
            continue
    return normalized


def _coerce_utc(value):
    if not value:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_drive_open_for_student(drive):
    if not drive or drive.status != "approved":
        return False

    deadline = _coerce_utc(drive.application_deadline)
    if not deadline:
        return False

    return deadline >= datetime.now(timezone.utc)


def _student_eligibility_for_drive(student, drive):
    reasons = []

    if not student:
        return False, ["Student profile not found"]

    if student.is_blacklisted:
        reasons.append("Student profile is restricted")

    if not student.profile_completed:
        reasons.append("Complete your profile first")

    student_branch = str(student.branch or "").strip().upper()
    student_year = student.year
    student_cgpa = student.cgpa

    allowed_branches = _normalized_upper_set(drive.eligible_branches)
    allowed_years = _normalized_int_set(drive.eligible_years)

    if allowed_branches and student_branch not in allowed_branches:
        reasons.append("Branch not eligible")

    if allowed_years and student_year not in allowed_years:
        reasons.append("Year not eligible")

    min_cgpa = float(drive.min_cgpa or 0)
    if student_cgpa is None or float(student_cgpa) < min_cgpa:
        reasons.append(f"Minimum CGPA is {min_cgpa:g}")

    return len(reasons) == 0, reasons


def _text_download_response(filename, content):
    response = make_response(content, 200)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _serialize_datetime(value):
    return value.isoformat() if value else None


def _status_label(status):
    labels = {
        "applied": "Applied",
        "shortlisted": "Shortlisted",
        "interviewed": "Interviewed",
        "selected": "Selected",
        "waitlisted": "Waitlisted",
        "rejected": "Rejected",
        "offered": "Offer Released",
        "accepted": "Offer Accepted",
        "pending": "Pending",
        "pass": "Passed",
        "fail": "Not Selected",
    }
    normalized = str(status or "").strip().lower()
    if not normalized:
        return "Updated"
    return labels.get(normalized, normalized.capitalize())


def _timeline_event(event_id, label, timestamp, message, tone="info"):
    return {
        "id": event_id,
        "label": label,
        "timestamp": _serialize_datetime(timestamp),
        "message": message,
        "tone": tone,
    }


def _build_application_timeline(application, latest_interview=None, offer=None):
    events = []

    if application.application_date:
        events.append(
            _timeline_event(
                f"{application.application_id}-applied",
                "Applied",
                application.application_date,
                "Application submitted successfully.",
                "info",
            )
        )

    if application.status == "shortlisted":
        shortlist_message = "Application moved to shortlist."
        if application.notes:
            shortlist_message = f"{shortlist_message} Note: {application.notes}"
        events.append(
            _timeline_event(
                f"{application.application_id}-shortlisted",
                "Shortlisted",
                application.updated_at,
                shortlist_message,
                "success",
            )
        )

    if latest_interview:
        interview_message = "Interview round was scheduled."
        if latest_interview.result and latest_interview.result != "pending":
            interview_message = (
                f"Interview result: {_status_label(latest_interview.result)}."
            )
        if latest_interview.feedback:
            interview_message = f"{interview_message} Feedback: {latest_interview.feedback}"

        events.append(
            _timeline_event(
                f"{application.application_id}-interview-{latest_interview.interview_id}",
                "Interview Update",
                latest_interview.interview_date or latest_interview.updated_at,
                interview_message,
                "info",
            )
        )

    if offer:
        offer_tone = "info"
        if offer.status == "accepted":
            offer_tone = "success"
        elif offer.status == "rejected":
            offer_tone = "error"

        events.append(
            _timeline_event(
                f"{application.application_id}-offer-{offer.offer_id}",
                _status_label(offer.status),
                offer.created_at,
                f"Offer for {offer.position} with salary INR {offer.salary:,.0f}.",
                offer_tone,
            )
        )

    if application.status == "rejected":
        rejected_message = "Application was not selected."
        if application.rejection_reason:
            rejected_message = f"Reason: {application.rejection_reason}"
        events.append(
            _timeline_event(
                f"{application.application_id}-rejected",
                "Rejected",
                application.updated_at,
                rejected_message,
                "error",
            )
        )
    elif application.status in {"selected", "waitlisted", "interviewed"}:
        status_message = f"Current status: {_status_label(application.status)}."
        if application.notes:
            status_message = f"{status_message} Note: {application.notes}"
        events.append(
            _timeline_event(
                f"{application.application_id}-{application.status}",
                _status_label(application.status),
                application.updated_at,
                status_message,
                "success" if application.status == "selected" else "info",
            )
        )

    sorted_events = sorted(
        events,
        key=lambda event: event.get("timestamp") or "",
    )
    return sorted_events


def _application_to_student_payload(
    application,
    drive=None,
    company=None,
    latest_interview=None,
    offer=None,
):
    drive_obj = drive or application.drive
    company_obj = company or (drive_obj.company if drive_obj else None)
    offer_obj = offer or application.placement_offer

    payload = application.to_dict()
    payload.update(
        {
            "id": application.application_id,
            "application_id": application.application_id,
            "status_label": _status_label(application.status),
            "drive": {
                "id": drive_obj.drive_id if drive_obj else application.drive_id,
                "title": drive_obj.job_title if drive_obj else None,
                "location": drive_obj.job_location if drive_obj else None,
                "application_deadline": (
                    _serialize_datetime(drive_obj.application_deadline)
                    if drive_obj
                    else None
                ),
                "salary_lpa": drive_obj.salary_lpa if drive_obj else None,
                "experience_required": (
                    drive_obj.experience_required if drive_obj else None
                ),
            },
            "company": {
                "id": company_obj.company_id if company_obj else None,
                "name": company_obj.company_name if company_obj else None,
                "industry": company_obj.industry if company_obj else None,
            },
            "latest_interview": (
                {
                    "interview_id": latest_interview.interview_id,
                    "interview_date": _serialize_datetime(
                        latest_interview.interview_date
                    ),
                    "interview_mode": latest_interview.interview_mode,
                    "interviewer_name": latest_interview.interviewer_name,
                    "result": latest_interview.result,
                    "feedback": latest_interview.feedback,
                }
                if latest_interview
                else None
            ),
            "offer": (
                {
                    "offer_id": offer_obj.offer_id,
                    "status": offer_obj.status,
                    "position": offer_obj.position,
                    "salary": offer_obj.salary,
                    "joining_date": (
                        offer_obj.joining_date.isoformat()
                        if offer_obj.joining_date
                        else None
                    ),
                    "created_at": _serialize_datetime(offer_obj.created_at),
                }
                if offer_obj
                else None
            ),
            "timeline": _build_application_timeline(
                application,
                latest_interview=latest_interview,
                offer=offer_obj,
            ),
        }
    )
    return payload


@student_bp.get("/profile")
@role_required("student")
def get_student_profile():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "student": _student_profile_payload(student),
                },
            }
        ),
        200,
    )


@student_bp.put("/profile")
@role_required("student")
def update_student_profile():
    """Complete or update student profile after initial registration."""
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    data = _normalized_json_payload()
    validation_error, normalized = _validate_student_profile_payload(data)
    if validation_error:
        return _json_error(validation_error, 400)

    student.college_name = normalized["college_name"]
    student.branch = normalized["branch"]
    student.year = normalized["year"]
    student.cgpa = normalized["cgpa"]
    student.roll_number = normalized["roll_number"]
    student.phone = normalized["phone"]
    student.resume_url = normalized["resume_url"]
    student.skills = normalized["skills"]
    student.experience_summary = normalized["experience_summary"]

    if normalized["resume_url"]:
        student.resume_uploaded_at = datetime.now(timezone.utc)

    student.profile_completed = True

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to update student profile", 500)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "message": "Student profile updated successfully",
                    "student": _student_profile_payload(student),
                },
            }
        ),
        200,
    )


@student_bp.get("/dashboard")
@role_required("student")
def student_dashboard():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    application_query = Application.query.filter(
        Application.student_id == student.student_id
    )

    summary = {
        "applications_total": application_query.count(),
        "applied": application_query.filter(Application.status == "applied").count(),
        "shortlisted": application_query.filter(
            Application.status == "shortlisted"
        ).count(),
        "interviewed": application_query.filter(
            Application.status == "interviewed"
        ).count(),
        "selected": application_query.filter(Application.status == "selected").count(),
        "waitlisted": application_query.filter(
            Application.status == "waitlisted"
        ).count(),
        "rejected": application_query.filter(Application.status == "rejected").count(),
        "offers_released": PlacementOffer.query.filter(
            PlacementOffer.student_id == student.student_id,
            PlacementOffer.status == "offered",
        ).count(),
        "offers_accepted": PlacementOffer.query.filter(
            PlacementOffer.student_id == student.student_id,
            PlacementOffer.status == "accepted",
        ).count(),
        "offers_rejected": PlacementOffer.query.filter(
            PlacementOffer.student_id == student.student_id,
            PlacementOffer.status == "rejected",
        ).count(),
    }

    unread_notifications = Notification.query.filter(
        Notification.recipient_id == user_id,
        Notification.notification_type == "in_app",
        Notification.is_read.is_(False),
    ).count()

    recent_rows = (
        db.session.query(Application, PlacementDrive, Company)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(Application.student_id == student.student_id)
        .order_by(Application.updated_at.desc(), Application.application_id.desc())
        .limit(6)
        .all()
    )

    recent_applications = []
    for application, drive, company in recent_rows:
        latest_interview = (
            Interview.query.filter_by(application_id=application.application_id)
            .order_by(Interview.interview_date.desc(), Interview.interview_id.desc())
            .first()
        )
        recent_applications.append(
            _application_to_student_payload(
                application,
                drive=drive,
                company=company,
                latest_interview=latest_interview,
                offer=application.placement_offer,
            )
        )

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "summary": summary,
                    "recent_applications": recent_applications,
                    "unread_notifications": unread_notifications,
                },
            }
        ),
        200,
    )


@student_bp.get("/applications")
@role_required("student")
def list_student_applications():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    status_filter = (request.args.get("status") or "all").strip().lower()
    query_text = (request.args.get("q") or "").strip()

    if status_filter != "all" and status_filter not in ALLOWED_APPLICATION_STATUSES:
        return _json_error("Invalid application status filter", 400)

    base_query = (
        db.session.query(Application, PlacementDrive, Company)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(Application.student_id == student.student_id)
    )

    if status_filter != "all":
        base_query = base_query.filter(Application.status == status_filter)

    if query_text:
        like_value = f"%{query_text}%"
        base_query = base_query.filter(
            or_(
                PlacementDrive.job_title.ilike(like_value),
                PlacementDrive.job_location.ilike(like_value),
                Company.company_name.ilike(like_value),
            )
        )

    ordered_query = base_query.order_by(
        Application.updated_at.desc(),
        Application.application_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    items = []
    for application, drive, company in rows:
        latest_interview = (
            Interview.query.filter_by(application_id=application.application_id)
            .order_by(Interview.interview_date.desc(), Interview.interview_id.desc())
            .first()
        )
        items.append(
            _application_to_student_payload(
                application,
                drive=drive,
                company=company,
                latest_interview=latest_interview,
                offer=application.placement_offer,
            )
        )

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "items": items,
                    "total": total,
                    "page": page,
                    "pages": pages,
                    "limit": limit,
                },
            }
        ),
        200,
    )


@student_bp.get("/notifications")
@role_required("student")
def list_student_notifications():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    is_read_filter = (request.args.get("is_read") or "all").strip().lower()
    if is_read_filter not in {"all", "true", "false"}:
        return _json_error("is_read must be one of all, true, or false", 400)

    base_query = Notification.query.filter(
        Notification.recipient_id == user_id,
        Notification.notification_type == "in_app",
    )

    if is_read_filter == "true":
        base_query = base_query.filter(Notification.is_read.is_(True))
    elif is_read_filter == "false":
        base_query = base_query.filter(Notification.is_read.is_(False))

    ordered_query = base_query.order_by(
        Notification.created_at.desc(),
        Notification.notification_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    unread_count = Notification.query.filter(
        Notification.recipient_id == user_id,
        Notification.notification_type == "in_app",
        Notification.is_read.is_(False),
    ).count()

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "items": [row.to_dict() for row in rows],
                    "total": total,
                    "page": page,
                    "pages": pages,
                    "limit": limit,
                    "unread_count": unread_count,
                },
            }
        ),
        200,
    )


@student_bp.put("/notifications/<int:notification_id>/read")
@role_required("student")
def mark_notification_read(notification_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    notification = Notification.query.filter(
        Notification.notification_id == notification_id,
        Notification.recipient_id == user_id,
        Notification.notification_type == "in_app",
    ).first()
    if not notification:
        return _json_error("Notification not found", 404)

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to update notification", 500)

    unread_count = Notification.query.filter(
        Notification.recipient_id == user_id,
        Notification.notification_type == "in_app",
        Notification.is_read.is_(False),
    ).count()

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "notification": notification.to_dict(),
                    "unread_count": unread_count,
                },
            }
        ),
        200,
    )


@student_bp.put("/notifications/read-all")
@role_required("student")
def mark_all_notifications_read():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    unread_notifications = Notification.query.filter(
        Notification.recipient_id == user_id,
        Notification.notification_type == "in_app",
        Notification.is_read.is_(False),
    ).all()

    if not unread_notifications:
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "updated_count": 0,
                        "unread_count": 0,
                    },
                }
            ),
            200,
        )

    read_time = datetime.now(timezone.utc)
    for notification in unread_notifications:
        notification.is_read = True
        notification.read_at = read_time

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to update notifications", 500)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "updated_count": len(unread_notifications),
                    "unread_count": 0,
                },
            }
        ),
        200,
    )


@student_bp.put("/offers/<int:offer_id>/respond")
@role_required("student")
def respond_to_offer(offer_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    offer = PlacementOffer.query.filter(
        PlacementOffer.offer_id == offer_id,
        PlacementOffer.student_id == student.student_id,
    ).first()
    if not offer:
        return _json_error("Offer not found", 404)

    payload = request.get_json(silent=True) or {}
    target_status = (payload.get("status") or "").strip().lower()
    if target_status not in ALLOWED_OFFER_RESPONSE_STATUSES:
        return _json_error("status must be accepted or rejected", 400)

    if offer.status == target_status and offer.status in ALLOWED_OFFER_RESPONSE_STATUSES:
        placement = None
        if target_status == "accepted":
            placement = Placement.query.filter_by(
                student_id=offer.student_id,
                company_id=offer.company_id,
                drive_id=offer.drive_id,
            ).first()
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "offer": offer.to_dict(),
                        "placement": placement.to_dict() if placement else None,
                    },
                }
            ),
            200,
        )

    if offer.status != "offered" and offer.status != target_status:
        return _json_error("Offer response already submitted", 400)

    try:
        offer.status = target_status

        application = db.session.get(Application, offer.application_id)
        if application:
            if target_status == "accepted":
                application.status = "selected"
            else:
                application.status = "rejected"
                if not application.rejection_reason:
                    application.rejection_reason = "Offer declined by student."
            application.updated_at = datetime.now(timezone.utc)

        placement_payload = None
        if target_status == "accepted":
            placement = Placement.query.filter_by(
                student_id=offer.student_id,
                company_id=offer.company_id,
                drive_id=offer.drive_id,
            ).first()
            if not placement:
                placement = Placement(
                    student_id=offer.student_id,
                    company_id=offer.company_id,
                    drive_id=offer.drive_id,
                    position=offer.position,
                    salary=offer.salary,
                    joining_date=offer.joining_date,
                )
                db.session.add(placement)

            db.session.flush()
            placement_payload = placement.to_dict()

        student_name = student.user.username if student.user else f"Student {student.student_id}"
        _create_company_notification(
            offer.company_id,
            "Offer Response Received",
            (
                f"{student_name} has {_status_label(target_status).lower()} "
                f"the offer for {offer.position}."
            ),
            sender_id=user_id,
            resource_type="offer",
            resource_id=offer.offer_id,
        )

        _append_student_activity(
            user_id,
            "Offer Response Submitted",
            f"Offer #{offer.offer_id} -> {target_status}",
            "success" if target_status == "accepted" else "info",
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to submit offer response", 500)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "offer": offer.to_dict(),
                    "placement": placement_payload,
                },
            }
        ),
        200,
    )


@student_bp.get("/drives")
@role_required("student")
def list_student_drives():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    query_text = (request.args.get("q") or "").strip()
    company_filter = (request.args.get("company") or "").strip()
    role_filter = (request.args.get("role") or "").strip()
    skills_filter = (request.args.get("skills") or "").strip()
    include_expired = _parse_bool_param(request.args.get("include_expired"), False)

    base_query = (
        db.session.query(PlacementDrive, Company)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(
            PlacementDrive.status == "approved",
            Company.approval_status == "approved",
            Company.is_blacklisted.is_(False),
        )
    )

    if not include_expired:
        base_query = base_query.filter(
            PlacementDrive.application_deadline >= datetime.now(timezone.utc)
        )

    if query_text:
        like_value = f"%{query_text}%"
        base_query = base_query.filter(
            or_(
                PlacementDrive.job_title.ilike(like_value),
                PlacementDrive.job_description.ilike(like_value),
                PlacementDrive.required_skills.ilike(like_value),
                PlacementDrive.job_location.ilike(like_value),
                Company.company_name.ilike(like_value),
            )
        )

    if company_filter:
        base_query = base_query.filter(Company.company_name.ilike(f"%{company_filter}%"))

    if role_filter:
        base_query = base_query.filter(PlacementDrive.job_title.ilike(f"%{role_filter}%"))

    if skills_filter:
        base_query = base_query.filter(
            PlacementDrive.required_skills.ilike(f"%{skills_filter}%")
        )

    ordered_query = base_query.order_by(
        PlacementDrive.application_deadline.asc(),
        PlacementDrive.drive_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    drive_ids = [drive.drive_id for drive, _ in rows]
    applied_drive_ids = set()
    if drive_ids:
        applied_rows = (
            db.session.query(Application.drive_id)
            .filter(
                Application.student_id == student.student_id,
                Application.drive_id.in_(drive_ids),
            )
            .all()
        )
        applied_drive_ids = {row.drive_id for row in applied_rows}

    items = []
    for drive, company in rows:
        is_eligible, reasons = _student_eligibility_for_drive(student, drive)
        payload = drive.to_dict()
        payload.update(
            {
                "id": drive.drive_id,
                "company": {
                    "company_id": company.company_id,
                    "name": company.company_name,
                    "industry": company.industry,
                },
                "already_applied": drive.drive_id in applied_drive_ids,
                "is_eligible": is_eligible,
                "ineligibility_reasons": reasons,
                "is_open": _is_drive_open_for_student(drive),
            }
        )
        items.append(payload)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "items": items,
                    "total": total,
                    "page": page,
                    "pages": pages,
                    "limit": limit,
                },
            }
        ),
        200,
    )


@student_bp.post("/drives/<int:drive_id>/apply")
@role_required("student")
def apply_to_drive(drive_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    drive_row = (
        db.session.query(PlacementDrive, Company)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(PlacementDrive.drive_id == drive_id)
        .first()
    )
    if not drive_row:
        return _json_error("Drive not found", 404)

    drive, company = drive_row

    if drive.status != "approved":
        return _json_error("Drive is not open for applications", 400)

    if company.approval_status != "approved" or company.is_blacklisted:
        return _json_error("Drive is not available for applications", 400)

    if not _is_drive_open_for_student(drive):
        return _json_error("Application deadline has passed", 400)

    is_eligible, reasons = _student_eligibility_for_drive(student, drive)
    if not is_eligible:
        reason_text = "; ".join(reasons) if reasons else "Not eligible for this drive"
        return _json_error(reason_text, 400)

    existing_application = Application.query.filter_by(
        student_id=student.student_id,
        drive_id=drive.drive_id,
    ).first()
    if existing_application:
        latest_interview = (
            Interview.query.filter_by(application_id=existing_application.application_id)
            .order_by(Interview.interview_date.desc(), Interview.interview_id.desc())
            .first()
        )
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "already_applied": True,
                        "application": _application_to_student_payload(
                            existing_application,
                            drive=drive,
                            company=company,
                            latest_interview=latest_interview,
                            offer=existing_application.placement_offer,
                        ),
                    },
                }
            ),
            200,
        )

    application = Application(
        student_id=student.student_id,
        drive_id=drive.drive_id,
        status="applied",
    )
    db.session.add(application)
    _append_student_activity(
        user_id,
        "Application Submitted",
        f"Drive #{drive.drive_id} - {drive.job_title}",
        "success",
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to submit application", 500)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "already_applied": False,
                    "application": _application_to_student_payload(
                        application,
                        drive=drive,
                        company=company,
                        latest_interview=None,
                        offer=None,
                    ),
                },
            }
        ),
        201,
    )


@student_bp.get("/history")
@role_required("student")
def student_history():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    query_text = (request.args.get("q") or "").strip()

    base_query = (
        db.session.query(Application, PlacementDrive, Company)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(Application.student_id == student.student_id)
    )

    if query_text:
        like_value = f"%{query_text}%"
        base_query = base_query.filter(
            or_(
                PlacementDrive.job_title.ilike(like_value),
                Company.company_name.ilike(like_value),
                PlacementDrive.job_location.ilike(like_value),
            )
        )

    ordered_query = base_query.order_by(
        Application.updated_at.desc(),
        Application.application_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    items = []
    for application, drive, company in rows:
        offer = application.placement_offer
        placement = (
            Placement.query.filter_by(
                student_id=student.student_id,
                company_id=company.company_id,
                drive_id=drive.drive_id,
            )
            .order_by(Placement.created_at.desc(), Placement.placement_id.desc())
            .first()
        )

        outcome = "in_progress"
        if placement or (offer and offer.status == "accepted"):
            outcome = "placed"
        elif offer and offer.status == "offered":
            outcome = "offer_released"
        elif application.status == "rejected":
            outcome = "rejected"

        items.append(
            {
                "application_id": application.application_id,
                "status": application.status,
                "status_label": _status_label(application.status),
                "updated_at": _serialize_datetime(application.updated_at),
                "drive": {
                    "drive_id": drive.drive_id,
                    "job_title": drive.job_title,
                    "job_location": drive.job_location,
                },
                "company": {
                    "company_id": company.company_id,
                    "company_name": company.company_name,
                },
                "offer": offer.to_dict() if offer else None,
                "placement": placement.to_dict() if placement else None,
                "outcome": outcome,
            }
        )

    offers_received = PlacementOffer.query.filter(
        PlacementOffer.student_id == student.student_id
    ).count()
    placements_count = Placement.query.filter(
        Placement.student_id == student.student_id
    ).count()
    highest_offer_salary = (
        db.session.query(func.max(PlacementOffer.salary))
        .filter(PlacementOffer.student_id == student.student_id)
        .scalar()
    )
    highest_placement_salary = (
        db.session.query(func.max(Placement.salary))
        .filter(Placement.student_id == student.student_id)
        .scalar()
    )

    highest_package = max(
        float(highest_offer_salary or 0),
        float(highest_placement_salary or 0),
    )

    summary = {
        "total_applied": Application.query.filter(
            Application.student_id == student.student_id
        ).count(),
        "offers_received": offers_received,
        "placements_count": placements_count,
        "highest_package": highest_package,
    }

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "summary": summary,
                    "items": items,
                    "total": total,
                    "page": page,
                    "pages": pages,
                    "limit": limit,
                },
            }
        ),
        200,
    )


@student_bp.get("/offers/<int:offer_id>/document")
@role_required("student")
def download_offer_document(offer_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    offer = PlacementOffer.query.filter(
        PlacementOffer.offer_id == offer_id,
        PlacementOffer.student_id == student.student_id,
    ).first()
    if not offer:
        return _json_error("Offer not found", 404)

    student_name = student.user.username if student.user else f"Student {student.student_id}"
    company_name = offer.company.company_name if offer.company else "Company"
    drive_title = offer.drive.job_title if offer.drive else "Placement Role"

    content = "\n".join(
        [
            "Recruitify Offer Letter",
            "-----------------------",
            f"Offer ID: {offer.offer_id}",
            f"Student: {student_name}",
            f"Company: {company_name}",
            f"Role: {offer.position}",
            f"Drive: {drive_title}",
            f"Salary: INR {float(offer.salary):,.0f}",
            f"Joining Date: {offer.joining_date.isoformat() if offer.joining_date else 'TBD'}",
            f"Status: {_status_label(offer.status)}",
            "",
            "This document is system-generated for placement workflow tracking.",
        ]
    )

    return _text_download_response(f"offer-letter-{offer.offer_id}.txt", content)


@student_bp.get("/placements/<int:placement_id>/document")
@role_required("student")
def download_placement_document(placement_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    placement = Placement.query.filter(
        Placement.placement_id == placement_id,
        Placement.student_id == student.student_id,
    ).first()
    if not placement:
        return _json_error("Placement not found", 404)

    student_name = student.user.username if student.user else f"Student {student.student_id}"
    company_name = placement.company.company_name if placement.company else "Company"
    drive_title = placement.drive.job_title if placement.drive else "Placement Role"

    content = "\n".join(
        [
            "Recruitify Placement Confirmation",
            "-------------------------------",
            f"Placement ID: {placement.placement_id}",
            f"Student: {student_name}",
            f"Company: {company_name}",
            f"Role: {placement.position}",
            f"Drive: {drive_title}",
            f"Package: INR {float(placement.salary):,.0f}",
            (
                f"Joining Date: {placement.joining_date.isoformat()}"
                if placement.joining_date
                else "Joining Date: TBD"
            ),
            f"Generated At: {_serialize_datetime(datetime.now(timezone.utc))}",
            "",
            "This is a system-generated placement confirmation for institutional records.",
        ]
    )

    return _text_download_response(
        f"placement-confirmation-{placement.placement_id}.txt",
        content,
    )


__all__ = ["student_bp"]
