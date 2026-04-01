"""Student profile and dashboard routes."""

from datetime import datetime, timezone
from math import ceil

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import or_

from app.auth.utils import role_required
from app.auth.validators import validate_required_fields
from app.models import (
    Application,
    Company,
    Interview,
    Notification,
    PlacementDrive,
    PlacementOffer,
    Student,
    db,
)

student_bp = Blueprint("student", __name__)

# ✅ Allowed ENUM values (MUST match your DB)
VALID_BRANCHES = {"CSE", "ECE", "MECH", "OTHER"}

# ✅ Mapping user input → enum
BRANCH_MAP = {
    "cse": "CSE",
    "computer science": "CSE",
    "ece": "ECE",
    "electronics": "ECE",
    "mech": "MECH",
    "mechanical": "MECH",
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
    """Validate required student profile fields and value ranges."""
    required_fields = ["college_name", "branch", "year", "cgpa", "roll_number"]
    missing_message = validate_required_fields(data, required_fields)
    if missing_message:
        return missing_message, None, None

    try:
        year = int(data.get("year"))
    except (TypeError, ValueError):
        return "Year must be a valid integer", None, None
    if year <= 0:
        return "Year must be greater than 0", None, None

    try:
        cgpa = float(data.get("cgpa"))
    except (TypeError, ValueError):
        return "CGPA must be a valid number", None, None
    if cgpa < 0 or cgpa > 10:
        return "CGPA must be between 0 and 10", None, None

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
        events.append(
            _timeline_event(
                f"{application.application_id}-offer-{offer.offer_id}",
                _status_label(offer.status),
                offer.created_at,
                f"Offer for {offer.position} with salary INR {offer.salary:,.0f}.",
                "success",
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
    validation_error, year, cgpa = _validate_student_profile_payload(data)
    if validation_error:
        return _json_error(validation_error, 400)

    student.college_name = data["college_name"]
    student.branch = data["branch"]
    student.year = year
    student.cgpa = cgpa
    student.roll_number = data["roll_number"]
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
                    "student": student.to_dict(),
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


__all__ = ["student_bp"]
