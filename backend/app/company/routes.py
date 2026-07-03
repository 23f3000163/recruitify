"""Company routes for drive, application, interview, and offer management."""

from datetime import date, datetime, timezone
from html import escape
from math import ceil

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, or_


from app.applications.status_engine import (
    ATS_TO_LEGACY_STATUS,
    ATS_TRANSITIONS,
    application_ats_status,
    normalize_status_input,
)
from app.cache import (
    CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH,
    CACHE_NAMESPACE_ADMIN_JOBS,
    invalidate_api_cache_namespaces,
)
from app.auth.utils import role_required
from app.auth.validators import validate_email
from app.models import (
    ActivityLog,
    Application,
    Company,
    Interview,
    Notification,
    PlacementDrive,
    PlacementOffer,
    Student,
    User,
    db,
)

company_bp = Blueprint("company_bp", __name__)

MAX_LIMIT = 100
ALLOWED_DRIVE_STATUSES = {"pending", "approved", "closed"}
ALLOWED_APPLICATION_STATUSES = {
    "applied",
    "shortlisted",
    "selected",
    "interviewed",
    "rejected",
    "waitlisted",
}
ALLOWED_INTERVIEW_MODES = {"online", "offline", "both"}
ALLOWED_INTERVIEW_RECORD_MODES = {"online", "offline"}
ALLOWED_INTERVIEW_RESULTS = {"pending", "pass", "fail"}
ALLOWED_OFFER_STATUSES = {"offered", "accepted", "rejected"}
ALLOWED_BRANCHES = {"CSE", "ECE", "MECH", "EE", "OTHER"}
ALLOWED_NOTIFICATION_READ_FILTERS = {"all", "true", "false"}
MAX_APPLICATION_NOTES_LENGTH = 500
MAX_REJECTION_REASON_LENGTH = 300
MAX_DESC_LENGTH = 3000
MAX_TITLE_LENGTH = 200
DIRECT_STATUS_UPDATE_BLOCKED_STATUSES = {"interview", "offered", "placed"}
DIRECT_STATUS_UPDATE_BLOCKED_MESSAGE = (
    "Direct status updates to interview, offered, or placed are not allowed. "
    "Use interview and offer workflow APIs."
)


def _json_error(message, status_code=400):
    return jsonify({"success": False, "error": message}), status_code


def _invalidate_admin_cache(*namespaces):
    cache = current_app.extensions.get("redis_cache")
    invalidate_api_cache_namespaces(cache, *namespaces)


def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def _company_for_user(user_id):
    return Company.query.filter_by(user_id=user_id).first()


def _parse_deadline(raw_deadline):
    if not isinstance(raw_deadline, str) or not raw_deadline.strip():
        return None, "application_deadline is required"

    raw_text = raw_deadline.strip()
    if len(raw_text) == 10:
        raw_text = f"{raw_text}T23:59:59+00:00"
    elif raw_text.endswith("Z"):
        raw_text = f"{raw_text[:-1]}+00:00"

    try:
        parsed_deadline = datetime.fromisoformat(raw_text)
    except ValueError:
        return None, "application_deadline must be a valid ISO datetime"

    if parsed_deadline.tzinfo is None:
        parsed_deadline = parsed_deadline.replace(tzinfo=timezone.utc)
    else:
        parsed_deadline = parsed_deadline.astimezone(timezone.utc)

    if parsed_deadline <= datetime.now(timezone.utc):
        return None, "application_deadline must be in the future"

    return parsed_deadline, None


def _normalize_branches(raw_branches):
    if not isinstance(raw_branches, list) or not raw_branches:
        return None, "eligible_branches must be a non-empty array"

    normalized = []
    for branch in raw_branches:
        normalized_branch = str(branch or "").strip().upper()
        if not normalized_branch:
            continue
        if normalized_branch not in ALLOWED_BRANCHES:
            return None, f"Unsupported branch: {normalized_branch}"
        if normalized_branch not in normalized:
            normalized.append(normalized_branch)

    if not normalized:
        return None, "eligible_branches must include at least one valid branch"

    return normalized, None


def _normalize_years(raw_years):
    if not isinstance(raw_years, list) or not raw_years:
        return None, "eligible_years must be a non-empty array"

    normalized = []
    for year in raw_years:
        try:
            parsed_year = int(year)
        except (TypeError, ValueError):
            return None, "eligible_years must contain integers"

        if parsed_year < 1 or parsed_year > 4:
            return None, "eligible_years values must be between 1 and 4"
        if parsed_year not in normalized:
            normalized.append(parsed_year)

    return normalized, None


def _append_company_activity(user_id, action, target=None, status="info"):
    try:
        actor_id = int(user_id)
    except (TypeError, ValueError):
        return

    db.session.add(
        ActivityLog(
            user_id=actor_id,
            action=(action or "Drive Action").strip(),
            target=(target or "").strip() or None,
            status=(status or "info").strip().lower() or "info",
        )
    )


def _status_label(status):
    status_map = {
        "applied": "Applied",
        "shortlisted": "Shortlisted",
        "interviewed": "Interviewed",
        "selected": "Selected",
        "waitlisted": "Waitlisted",
        "rejected": "Rejected",
        "pending": "Pending",
        "pass": "Passed",
        "fail": "Not Selected",
        "offered": "Offer Released",
        "accepted": "Offer Accepted",
    }
    normalized = str(status or "").strip().lower()
    if not normalized:
        return "Updated"
    return status_map.get(normalized, normalized.capitalize())


def _validate_transition(application, target_ats_status):
    current_ats_status = application_ats_status(application)
    if target_ats_status == current_ats_status:
        return None

    allowed_targets = ATS_TRANSITIONS.get(current_ats_status, set())
    if target_ats_status in allowed_targets:
        return None

    return f"Invalid status transition: {current_ats_status} -> {target_ats_status}"


def _create_student_notification(
    application,
    title,
    message,
    sender_id=None,
    resource_type="application",
    resource_id=None,
):
    if not application:
        return

    student = db.session.get(Student, application.student_id)
    if not student or not student.user_id:
        return

    db.session.add(
        Notification(
            recipient_id=student.user_id,
            sender_id=sender_id,
            notification_type="in_app",
            title=(title or "Update").strip()[:200],
            message=(message or "").strip() or "You have a new recruitment update.",
            related_resource_type=(resource_type or "application").strip()[:100],
            related_resource_id=resource_id,
            delivery_status="sent",
        )
    )


def _create_admin_notifications(
    title,
    message,
    sender_id=None,
    resource_type="drive",
    resource_id=None,
):
    admin_users = User.query.filter(
        User.role == "admin",
        User.is_active.is_(True),
    ).all()

    for admin_user in admin_users:
        db.session.add(
            Notification(
                recipient_id=admin_user.user_id,
                sender_id=sender_id,
                notification_type="in_app",
                title=(title or "Update").strip()[:200],
                message=(message or "").strip() or "You have a new update.",
                related_resource_type=(resource_type or "drive").strip()[:100],
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


def _parse_datetime_value(raw_value, field_name, must_be_future=False):
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None, f"{field_name} is required"

    raw_text = raw_value.strip()
    if len(raw_text) == 10:
        raw_text = f"{raw_text}T09:00:00+00:00"
    elif raw_text.endswith("Z"):
        raw_text = f"{raw_text[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(raw_text)
    except ValueError:
        return None, f"{field_name} must be a valid ISO datetime"

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    if must_be_future and parsed <= datetime.now(timezone.utc):
        return None, f"{field_name} must be in the future"

    return parsed, None


def _parse_date_value(raw_value, field_name):
    if raw_value in (None, ""):
        return None, None

    if not isinstance(raw_value, str):
        return None, f"{field_name} must be a valid date"

    try:
        return date.fromisoformat(raw_value.strip()), None
    except ValueError:
        return None, f"{field_name} must be a valid date"


def _parse_optional_text(raw_value, field_name, max_length):
    if raw_value is None:
        return None, None

    if not isinstance(raw_value, str):
        return None, f"{field_name} must be a string"

    cleaned = raw_value.strip()
    if len(cleaned) > max_length:
        return None, f"{field_name} must be at most {max_length} characters"

    return cleaned or None, None


def _notification_query_for_company(company_user_id):
    return Notification.query.filter(
        Notification.recipient_id == company_user_id,
        Notification.notification_type == "in_app",
    )


def _drive_to_dict(drive, applications_count=0):
    payload = drive.to_dict()
    payload.update(
        {
            "id": drive.drive_id,
            "title": drive.job_title,
            "deadline": payload.get("application_deadline"),
            "applications_count": int(applications_count or 0),
        }
    )
    return payload


def _application_to_dict(application, student=None, student_user=None, drive=None):
    student_obj = student or application.student
    user_obj = student_user or (student_obj.user if student_obj else None)
    drive_obj = drive or application.drive

    has_offer = bool(application.placement_offer)
    interviews_count = application.interviews.count() if hasattr(application, "interviews") else 0

    payload = application.to_dict()
    payload.update(
        {
            "id": application.application_id,
            "application_id": application.application_id,
            "student_name": user_obj.username if user_obj else "Candidate",
            "student_email": user_obj.email if user_obj else None,
            "student_branch": student_obj.branch if student_obj else None,
            "student_year": student_obj.year if student_obj else None,
            "student_cgpa": student_obj.cgpa if student_obj else None,
            "resume_url": student_obj.resume_url if student_obj else None,
            "drive_id": drive_obj.drive_id if drive_obj else application.drive_id,
            "drive_title": drive_obj.job_title if drive_obj else None,
            "has_offer": has_offer,
            "interviews_count": interviews_count,
        }
    )
    return payload


def _interview_to_dict(interview, application=None, student=None, student_user=None, drive=None):
    application_obj = application or interview.application
    student_obj = student or (application_obj.student if application_obj else None)
    user_obj = student_user or (student_obj.user if student_obj else None)
    drive_obj = drive or interview.drive

    payload = interview.to_dict()
    payload.update(
        {
            "id": interview.interview_id,
            "interview_id": interview.interview_id,
            "application_id": interview.application_id,
            "drive_id": interview.drive_id,
            "drive_title": drive_obj.job_title if drive_obj else None,
            "student_name": user_obj.username if user_obj else "Candidate",
            "student_email": user_obj.email if user_obj else None,
            "application_status": application_obj.status if application_obj else None,
        }
    )
    return payload


def _offer_to_dict(offer, application=None, student=None, student_user=None, drive=None):
    application_obj = application or offer.application
    student_obj = student or offer.student
    user_obj = student_user or (student_obj.user if student_obj else None)
    drive_obj = drive or offer.drive

    payload = offer.to_dict()
    payload.update(
        {
            "id": offer.offer_id,
            "offer_id": offer.offer_id,
            "application_id": offer.application_id,
            "drive_id": offer.drive_id,
            "drive_title": drive_obj.job_title if drive_obj else None,
            "student_name": user_obj.username if user_obj else "Candidate",
            "student_email": user_obj.email if user_obj else None,
            "application_status": application_obj.status if application_obj else None,
        }
    )
    return payload


def _company_drive_options(company_id):
    drives = (
        PlacementDrive.query.filter_by(company_id=company_id)
        .order_by(PlacementDrive.created_at.desc(), PlacementDrive.drive_id.desc())
        .all()
    )
    return [
        {
            "id": drive.drive_id,
            "title": drive.job_title,
            "status": drive.status,
        }
        for drive in drives
    ]


def _company_profile_payload(company):
    payload = company.to_dict()
    if company.user:
        payload["username"] = company.user.username
        payload["email"] = company.user.email
    return payload


@company_bp.get("/profile")
@role_required("company")
def get_company_profile():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    return jsonify({"success": True, "data": _company_profile_payload(company)}), 200


@company_bp.patch("/profile")
@role_required("company")
def update_company_profile():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _json_error("Invalid request body", 400)

    updatable_keys = {
        "company_name",
        "website",
        "hr_contact_name",
        "hr_contact_email",
        "hr_contact_phone",
        "industry",
        "location",
        "company_description",
    }
    provided_keys = [key for key in updatable_keys if key in payload]
    if not provided_keys:
        return _json_error("No profile fields provided for update", 400)

    if "company_name" in payload:
        company_name = str(payload.get("company_name") or "").strip()
        if not company_name:
            return _json_error("company_name cannot be empty", 400)
        if len(company_name) > 200:
            return _json_error("company_name must be at most 200 characters", 400)

        duplicate_name = Company.query.filter(
            Company.company_name == company_name,
            Company.company_id != company.company_id,
        ).first()
        if duplicate_name:
            return _json_error("Company name already exists", 409)

        company.company_name = company_name

    if "hr_contact_name" in payload:
        hr_contact_name = str(payload.get("hr_contact_name") or "").strip()
        if not hr_contact_name:
            return _json_error("hr_contact_name cannot be empty", 400)
        if len(hr_contact_name) > 120:
            return _json_error("hr_contact_name must be at most 120 characters", 400)
        company.hr_contact_name = hr_contact_name

    if "hr_contact_email" in payload:
        hr_contact_email = str(payload.get("hr_contact_email") or "").strip().lower()
        if not hr_contact_email:
            return _json_error("hr_contact_email cannot be empty", 400)

        email_error = validate_email(hr_contact_email)
        if email_error:
            return _json_error("Invalid HR contact email format", 400)

        duplicate_hr_email = Company.query.filter(
            Company.hr_contact_email == hr_contact_email,
            Company.company_id != company.company_id,
        ).first()
        if duplicate_hr_email:
            return _json_error("HR contact email already exists", 409)

        company.hr_contact_email = hr_contact_email

    if "website" in payload:
        website = str(payload.get("website") or "").strip() or None
        if website and len(website) > 300:
            return _json_error("website must be at most 300 characters", 400)
        company.website = website

    if "hr_contact_phone" in payload:
        hr_contact_phone = str(payload.get("hr_contact_phone") or "").strip() or None
        if hr_contact_phone and len(hr_contact_phone) > 20:
            return _json_error("hr_contact_phone must be at most 20 characters", 400)
        if hr_contact_phone is None:
            return _json_error("hr_contact_phone cannot be empty", 400)
        company.hr_contact_phone = hr_contact_phone

    if "industry" in payload:
        industry = str(payload.get("industry") or "").strip() or None
        if industry and len(industry) > 120:
            return _json_error("industry must be at most 120 characters", 400)
        company.industry = industry

    if "location" in payload:
        location = str(payload.get("location") or "").strip() or None
        if location and len(location) > 160:
            return _json_error("location must be at most 160 characters", 400)
        company.location = location

    if "company_description" in payload:
        company_description = str(payload.get("company_description") or "").strip() or None
        if company_description and len(company_description) > MAX_DESC_LENGTH:
            return _json_error(f"company_description must be at most {MAX_DESC_LENGTH} characters", 400)
        if company_description:
            company_description = escape(company_description)
        company.company_description = company_description

    try:
        _append_company_activity(user_id, "Company Profile Updated", company.company_name, "info")
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to update company profile", 500)

    _invalidate_admin_cache(CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH)

    return jsonify({"success": True, "data": _company_profile_payload(company)}), 200


@company_bp.get("/drives")
@role_required("company")
def list_drives():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    status_filter = (request.args.get("status") or "all").strip().lower()
    query_text = (request.args.get("q") or "").strip()
    sort_by = (request.args.get("sort_by") or "created_at").strip().lower()
    order = (request.args.get("order") or "desc").strip().lower()

    query = PlacementDrive.query.filter(PlacementDrive.company_id == company.company_id)

    if status_filter and status_filter != "all":
        if status_filter not in ALLOWED_DRIVE_STATUSES:
            return _json_error("Invalid status filter", 400)
        query = query.filter(PlacementDrive.status == status_filter)

    if query_text:
        like_value = f"%{query_text}%"
        query = query.filter(
            or_(
                PlacementDrive.job_title.ilike(like_value),
                PlacementDrive.job_location.ilike(like_value),
                PlacementDrive.required_skills.ilike(like_value),
            )
        )

    sort_map = {
        "created_at": PlacementDrive.created_at,
        "updated_at": PlacementDrive.updated_at,
        "application_deadline": PlacementDrive.application_deadline,
        "job_title": PlacementDrive.job_title,
        "status": PlacementDrive.status,
    }
    sort_column = sort_map.get(sort_by, PlacementDrive.created_at)
    is_ascending = order == "asc"
    query = query.order_by(sort_column.asc() if is_ascending else sort_column.desc())

    total = query.count()
    pages = ceil(total / limit) if total else 0
    drives = query.offset((page - 1) * limit).limit(limit).all()

    drive_ids = [drive.drive_id for drive in drives]
    applications_count_map = {}
    if drive_ids:
        rows = (
            db.session.query(Application.drive_id, func.count(Application.application_id))
            .filter(Application.drive_id.in_(drive_ids))
            .group_by(Application.drive_id)
            .all()
        )
        applications_count_map = {
            int(drive_id): int(total_apps) for drive_id, total_apps in rows
        }

    items = [
        _drive_to_dict(drive, applications_count_map.get(drive.drive_id, 0))
        for drive in drives
    ]

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


@company_bp.post("/drives")
@role_required("company")
def create_drive():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)
    if company.approval_status != "approved" or company.is_blacklisted:
        return _json_error("Only approved companies can create jobs", 403)

    payload = request.get_json(silent=True) or {}

    job_title = (payload.get("job_title") or "").strip()
    if not job_title:
        return _json_error("job_title is required", 400)
    if len(job_title) > MAX_TITLE_LENGTH:
        return _json_error(f"job_title must be at most {MAX_TITLE_LENGTH} characters", 400)

    job_description = (payload.get("job_description") or "").strip()
    if not job_description:
        return _json_error("job_description is required", 400)
    if len(job_description) > MAX_DESC_LENGTH:
        return _json_error(f"job_description must be at most {MAX_DESC_LENGTH} characters", 400)

    experience_required = (payload.get("experience_required") or "").strip()
    if not experience_required:
        return _json_error("experience_required is required", 400)
    if len(experience_required) > 120:
        return _json_error("experience_required cannot exceed 120 characters", 400)

    benefits = (payload.get("benefits") or "").strip()
    if not benefits:
        return _json_error("benefits is required", 400)
    if len(benefits) > MAX_DESC_LENGTH:
        return _json_error(f"benefits must be at most {MAX_DESC_LENGTH} characters", 400)

    try:
        min_cgpa = float(payload.get("min_cgpa"))
    except (TypeError, ValueError):
        return _json_error("min_cgpa must be a number", 400)
    if min_cgpa < 0 or min_cgpa > 10:
        return _json_error("min_cgpa must be between 0 and 10", 400)

    eligible_branches, branch_error = _normalize_branches(payload.get("eligible_branches"))
    if branch_error:
        return _json_error(branch_error, 400)

    eligible_years, year_error = _normalize_years(payload.get("eligible_years"))
    if year_error:
        return _json_error(year_error, 400)

    interview_mode = (payload.get("interview_mode") or "").strip().lower()
    if interview_mode not in ALLOWED_INTERVIEW_MODES:
        return _json_error("interview_mode must be online, offline, or both", 400)

    application_deadline, deadline_error = _parse_deadline(
        payload.get("application_deadline")
    )
    if deadline_error:
        return _json_error(deadline_error, 400)

    salary_raw = payload.get("salary_lpa")
    salary_lpa = None
    if salary_raw not in (None, ""):
        try:
            salary_lpa = float(salary_raw)
        except (TypeError, ValueError):
            return _json_error("salary_lpa must be a number", 400)
        if salary_lpa < 0:
            return _json_error("salary_lpa cannot be negative", 400)

    job_description = escape(job_description)
    benefits = escape(benefits)
    job_title = escape(job_title)
    drive = PlacementDrive(
        company_id=company.company_id,
        job_title=job_title,
        job_description=job_description,
        required_skills=(payload.get("required_skills") or "").strip() or None,
        experience_required=experience_required,
        benefits=benefits,
        min_cgpa=min_cgpa,
        eligible_branches=eligible_branches,
        eligible_years=eligible_years,
        salary_lpa=salary_lpa,
        job_location=(payload.get("job_location") or "").strip() or None,
        application_deadline=application_deadline,
        interview_mode=interview_mode,
        status="pending",
    )

    try:
        db.session.add(drive)
        db.session.flush()

        _create_admin_notifications(
            "New Drive Submitted",
            f"{company.company_name} submitted {drive.job_title} for review.",
            sender_id=user_id,
            resource_type="drive",
            resource_id=drive.drive_id,
        )

        _append_company_activity(user_id, "Drive Created", drive.job_title, "info")
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create drive", 500)

    _invalidate_admin_cache(CACHE_NAMESPACE_ADMIN_JOBS)

    return jsonify({"success": True, "data": _drive_to_dict(drive, 0)}), 201


@company_bp.put("/drives/<int:drive_id>/close")
@role_required("company")
def close_drive(drive_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    drive = PlacementDrive.query.filter_by(
        drive_id=drive_id,
        company_id=company.company_id,
    ).first()
    if not drive:
        return _json_error("Drive not found", 404)

    if drive.status != "closed":
        try:
            drive.status = "closed"
            _append_company_activity(user_id, "Drive Closed", drive.job_title, "warning")
            db.session.commit()
        except Exception:
            db.session.rollback()
            return _json_error("Failed to close drive", 500)

        _invalidate_admin_cache(CACHE_NAMESPACE_ADMIN_JOBS)

    applications_count = (
        db.session.query(func.count(Application.application_id))
        .filter(Application.drive_id == drive.drive_id)
        .scalar()
        or 0
    )

    return jsonify({"success": True, "data": _drive_to_dict(drive, applications_count)}), 200


@company_bp.get("/applications")
@role_required("company")
def list_applications():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    status_filter = (request.args.get("status") or "all").strip().lower()
    query_text = (request.args.get("q") or "").strip()
    drive_id_raw = (request.args.get("drive_id") or "all").strip().lower()

    base_query = (
        db.session.query(Application, Student, User, PlacementDrive)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Student, Application.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
        .filter(PlacementDrive.company_id == company.company_id)
    )

    if status_filter != "all":
        if status_filter not in ALLOWED_APPLICATION_STATUSES:
            return _json_error("Invalid application status filter", 400)
        base_query = base_query.filter(Application.status == status_filter)

    if drive_id_raw != "all":
        try:
            drive_id = int(drive_id_raw)
        except (TypeError, ValueError):
            return _json_error("drive_id must be an integer", 400)

        base_query = base_query.filter(PlacementDrive.drive_id == drive_id)

    if query_text:
        like_value = f"%{query_text}%"
        base_query = base_query.filter(
            or_(
                User.username.ilike(like_value),
                User.email.ilike(like_value),
                PlacementDrive.job_title.ilike(like_value),
            )
        )

    ordered_query = base_query.order_by(
        Application.updated_at.desc(),
        Application.application_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    items = [
        _application_to_dict(application, student, user, drive)
        for application, student, user, drive in rows
    ]

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
                    "drive_options": _company_drive_options(company.company_id),
                },
            }
        ),
        200,
    )


@company_bp.put("/applications/<int:application_id>/status")
@role_required("company")
def update_application_status(application_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    application = (
        db.session.query(Application)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .filter(
            Application.application_id == application_id,
            PlacementDrive.company_id == company.company_id,
        )
        .first()
    )
    if not application:
        return _json_error("Application not found", 404)

    payload = request.get_json(silent=True) or {}
    target_ats_status = normalize_status_input(payload.get("status"))
    if not target_ats_status:
        return _json_error("Invalid application status", 400)

    if target_ats_status in DIRECT_STATUS_UPDATE_BLOCKED_STATUSES:
        return _json_error(DIRECT_STATUS_UPDATE_BLOCKED_MESSAGE, 400)

    current_ats_status = application_ats_status(application)
    if target_ats_status != current_ats_status:
        allowed_targets = ATS_TRANSITIONS.get(current_ats_status, set())
        if target_ats_status not in allowed_targets:
            return _json_error(
                f"Invalid status transition: {current_ats_status} -> {target_ats_status}",
                400,
            )

    target_status = ATS_TO_LEGACY_STATUS[target_ats_status]

    notes, notes_error = _parse_optional_text(
        payload.get("notes"),
        "notes",
        MAX_APPLICATION_NOTES_LENGTH,
    )
    if notes_error:
        return _json_error(notes_error, 400)

    rejection_reason, rejection_reason_error = _parse_optional_text(
        payload.get("rejection_reason"),
        "rejection_reason",
        MAX_REJECTION_REASON_LENGTH,
    )
    if rejection_reason_error:
        return _json_error(rejection_reason_error, 400)

    if target_ats_status == "rejected" and not rejection_reason:
        return _json_error("rejection_reason is required when status is rejected", 400)

    try:
        previous_status = application.status
        application.status = target_status

        if "notes" in payload:
            application.notes = notes

        if target_ats_status == "rejected":
            application.rejection_reason = rejection_reason
        else:
            application.rejection_reason = None

        drive = db.session.get(PlacementDrive, application.drive_id)
        drive_title = drive.job_title if drive else "the selected drive"
        should_notify = (
            previous_status != target_status
            or ("notes" in payload and bool(notes))
            or (target_ats_status == "rejected" and bool(rejection_reason))
        )
        if should_notify:
            update_message = (
                f"Your application for {drive_title} is now "
                f"{_status_label(target_status).lower()}."
            )
            if target_ats_status == "rejected" and rejection_reason:
                update_message = f"{update_message} Reason: {rejection_reason}"
            elif notes:
                update_message = f"{update_message} Note: {notes}"

            _create_student_notification(
                application,
                "Application Update",
                update_message,
                sender_id=user_id,
                resource_type="application",
                resource_id=application.application_id,
            )

        _append_company_activity(
            user_id,
            "Application Status Updated",
            f"#{application.application_id} -> {target_status}",
            "success",
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update application status", 500)

    return jsonify({"success": True, "data": _application_to_dict(application)}), 200


@company_bp.get("/interviews")
@role_required("company")
def list_interviews():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    result_filter = (request.args.get("result") or "all").strip().lower()
    drive_id_raw = (request.args.get("drive_id") or "all").strip().lower()

    base_query = (
        db.session.query(Interview, Application, Student, User, PlacementDrive)
        .join(Application, Interview.application_id == Application.application_id)
        .join(PlacementDrive, Interview.drive_id == PlacementDrive.drive_id)
        .join(Student, Application.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
        .filter(Interview.company_id == company.company_id)
    )

    if result_filter != "all":
        if result_filter not in ALLOWED_INTERVIEW_RESULTS:
            return _json_error("Invalid interview result filter", 400)
        base_query = base_query.filter(Interview.result == result_filter)

    if drive_id_raw != "all":
        try:
            drive_id = int(drive_id_raw)
        except (TypeError, ValueError):
            return _json_error("drive_id must be an integer", 400)

        base_query = base_query.filter(Interview.drive_id == drive_id)

    ordered_query = base_query.order_by(
        Interview.interview_date.desc(),
        Interview.interview_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    items = [
        _interview_to_dict(interview, application, student, user, drive)
        for interview, application, student, user, drive in rows
    ]

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
                    "drive_options": _company_drive_options(company.company_id),
                },
            }
        ),
        200,
    )


@company_bp.post("/interviews")
@role_required("company")
def schedule_interview():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    payload = request.get_json(silent=True) or {}

    application_id = payload.get("application_id")
    try:
        application_id = int(application_id)
    except (TypeError, ValueError):
        return _json_error("application_id is required", 400)

    application = (
        db.session.query(Application)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .filter(
            Application.application_id == application_id,
            PlacementDrive.company_id == company.company_id,
        )
        .first()
    )
    if not application:
        return _json_error("Application not found", 404)

    interview_date, date_error = _parse_datetime_value(
        payload.get("interview_date"),
        "interview_date",
        must_be_future=False,
    )
    if date_error:
        return _json_error(date_error, 400)

    interview_mode = (payload.get("interview_mode") or "").strip().lower()
    if interview_mode not in ALLOWED_INTERVIEW_RECORD_MODES:
        return _json_error("interview_mode must be online or offline", 400)

    transition_error = _validate_transition(application, "interview")
    if transition_error:
        return _json_error(transition_error, 400)

    interview = Interview(
        application_id=application.application_id,
        company_id=company.company_id,
        drive_id=application.drive_id,
        interview_date=interview_date,
        interview_mode=interview_mode,
        interview_link=(payload.get("interview_link") or "").strip() or None,
        interview_location=(payload.get("interview_location") or "").strip() or None,
        interviewer_name=(payload.get("interviewer_name") or "").strip() or None,
        result="pending",
    )

    try:
        db.session.add(interview)
        application.status = ATS_TO_LEGACY_STATUS["interview"]
        db.session.flush()

        drive = db.session.get(PlacementDrive, application.drive_id)
        drive_title = drive.job_title if drive else "the selected drive"
        scheduled_time_text = interview_date.strftime("%d %b %Y, %I:%M %p UTC")
        _create_student_notification(
            application,
            "Interview Scheduled",
            (
                f"Interview scheduled for {drive_title} on {scheduled_time_text} "
                f"({_status_label(interview_mode)} mode)."
            ),
            sender_id=user_id,
            resource_type="interview",
            resource_id=interview.interview_id,
        )

        _append_company_activity(
            user_id,
            "Interview Scheduled",
            f"Application #{application.application_id}",
            "info",
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to schedule interview", 500)

    return jsonify({"success": True, "data": _interview_to_dict(interview)}), 201


@company_bp.put("/interviews/<int:interview_id>/result")
@role_required("company")
def update_interview_result(interview_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    interview = Interview.query.filter_by(
        interview_id=interview_id,
        company_id=company.company_id,
    ).first()
    if not interview:
        return _json_error("Interview not found", 404)

    payload = request.get_json(silent=True) or {}
    target_result = (payload.get("result") or "").strip().lower()
    if target_result not in ALLOWED_INTERVIEW_RESULTS:
        return _json_error("Invalid interview result", 400)

    target_ats_status = {
        "pending": "interview",
        "pass": "offered",
        "fail": "rejected",
    }[target_result]

    application = db.session.get(Application, interview.application_id)
    if application:
        transition_error = _validate_transition(application, target_ats_status)
        if transition_error:
            return _json_error(transition_error, 400)

    try:
        interview.result = target_result
        cleaned_feedback = None

        feedback = payload.get("feedback")
        if feedback is not None:
            cleaned_feedback = feedback.strip() if isinstance(feedback, str) else feedback
            interview.feedback = cleaned_feedback or None

        rating = payload.get("rating")
        if rating not in (None, ""):
            try:
                interview.rating = float(rating)
            except (TypeError, ValueError):
                return _json_error("rating must be a number", 400)

        if application:
            application.status = ATS_TO_LEGACY_STATUS[target_ats_status]
            if target_ats_status == "rejected":
                application.rejection_reason = (
                    application.rejection_reason or "Rejected after interview"
                )
            else:
                application.rejection_reason = None

            drive = db.session.get(PlacementDrive, application.drive_id)
            drive_title = drive.job_title if drive else "the selected drive"
            interview_message = (
                f"Interview result for {drive_title}: {_status_label(target_result)}."
            )
            if cleaned_feedback:
                interview_message = f"{interview_message} Feedback: {cleaned_feedback}"

            _create_student_notification(
                application,
                "Interview Result Update",
                interview_message,
                sender_id=user_id,
                resource_type="interview",
                resource_id=interview.interview_id,
            )

        _append_company_activity(
            user_id,
            "Interview Result Updated",
            f"Interview #{interview.interview_id} -> {target_result}",
            "success",
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update interview result", 500)

    return jsonify({"success": True, "data": _interview_to_dict(interview)}), 200


@company_bp.get("/offers")
@role_required("company")
def list_offers():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    status_filter = (request.args.get("status") or "all").strip().lower()
    query_text = (request.args.get("q") or "").strip()
    drive_id_raw = (request.args.get("drive_id") or "all").strip().lower()

    base_query = (
        db.session.query(PlacementOffer, Application, Student, User, PlacementDrive)
        .join(Application, PlacementOffer.application_id == Application.application_id)
        .join(PlacementDrive, PlacementOffer.drive_id == PlacementDrive.drive_id)
        .join(Student, PlacementOffer.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
        .filter(PlacementOffer.company_id == company.company_id)
    )

    if status_filter != "all":
        if status_filter not in ALLOWED_OFFER_STATUSES:
            return _json_error("Invalid offer status filter", 400)
        base_query = base_query.filter(PlacementOffer.status == status_filter)

    if drive_id_raw != "all":
        try:
            drive_id = int(drive_id_raw)
        except (TypeError, ValueError):
            return _json_error("drive_id must be an integer", 400)

        base_query = base_query.filter(PlacementOffer.drive_id == drive_id)

    if query_text:
        like_value = f"%{query_text}%"
        base_query = base_query.filter(
            or_(
                User.username.ilike(like_value),
                PlacementOffer.position.ilike(like_value),
                PlacementDrive.job_title.ilike(like_value),
            )
        )

    ordered_query = base_query.order_by(
        PlacementOffer.created_at.desc(),
        PlacementOffer.offer_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    items = [
        _offer_to_dict(offer, application, student, user, drive)
        for offer, application, student, user, drive in rows
    ]

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
                    "drive_options": _company_drive_options(company.company_id),
                },
            }
        ),
        200,
    )


@company_bp.post("/offers")
@role_required("company")
def create_offer():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    payload = request.get_json(silent=True) or {}

    application_id = payload.get("application_id")
    try:
        application_id = int(application_id)
    except (TypeError, ValueError):
        return _json_error("application_id is required", 400)

    application = (
        db.session.query(Application)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .filter(
            Application.application_id == application_id,
            PlacementDrive.company_id == company.company_id,
        )
        .first()
    )
    if not application:
        return _json_error("Application not found", 404)

    existing_offer = PlacementOffer.query.filter_by(
        application_id=application.application_id
    ).first()
    if existing_offer:
        return _json_error("Offer already exists for this application", 400)

    salary_raw = payload.get("salary")
    try:
        salary = float(salary_raw)
    except (TypeError, ValueError):
        return _json_error("salary must be a number", 400)
    if salary <= 0:
        return _json_error("salary must be greater than 0", 400)

    position = (payload.get("position") or "").strip()
    if not position:
        drive = db.session.get(PlacementDrive, application.drive_id)
        position = drive.job_title if drive else "Placement Offer"

    joining_date, date_error = _parse_date_value(payload.get("joining_date"), "joining_date")
    if date_error:
        return _json_error(date_error, 400)

    transition_error = _validate_transition(application, "offered")
    if transition_error:
        return _json_error(transition_error, 400)

    offer = PlacementOffer(
        application_id=application.application_id,
        student_id=application.student_id,
        company_id=company.company_id,
        drive_id=application.drive_id,
        salary=salary,
        position=position,
        joining_date=joining_date,
        status="offered",
    )

    try:
        db.session.add(offer)
        application.status = ATS_TO_LEGACY_STATUS["offered"]
        db.session.flush()

        drive = db.session.get(PlacementDrive, application.drive_id)
        drive_title = drive.job_title if drive else position
        salary_text = f"INR {salary:,.0f}"
        _create_student_notification(
            application,
            "Offer Released",
            (
                f"You received an offer for {position} at {company.company_name} "
                f"({drive_title}). Package: {salary_text}."
            ),
            sender_id=user_id,
            resource_type="offer",
            resource_id=offer.offer_id,
        )

        _append_company_activity(
            user_id,
            "Offer Released",
            f"Application #{application.application_id}",
            "success",
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create offer", 500)

    return jsonify({"success": True, "data": _offer_to_dict(offer)}), 201


@company_bp.get("/notifications")
@role_required("company")
def list_notifications():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    read_filter = (request.args.get("is_read") or "all").strip().lower()
    if read_filter not in ALLOWED_NOTIFICATION_READ_FILTERS:
        return _json_error("is_read must be one of all, true, or false", 400)

    base_query = _notification_query_for_company(company.user_id)
    if read_filter == "true":
        base_query = base_query.filter(Notification.is_read.is_(True))
    elif read_filter == "false":
        base_query = base_query.filter(Notification.is_read.is_(False))

    ordered_query = base_query.order_by(
        Notification.created_at.desc(),
        Notification.notification_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    unread_count = _notification_query_for_company(company.user_id).filter(
        Notification.is_read.is_(False)
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


@company_bp.put("/notifications/<int:notification_id>/read")
@role_required("company")
def mark_notification_read(notification_id):
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    notification = _notification_query_for_company(company.user_id).filter(
        Notification.notification_id == notification_id
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

    unread_count = _notification_query_for_company(company.user_id).filter(
        Notification.is_read.is_(False)
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


@company_bp.put("/notifications/read-all")
@role_required("company")
def mark_all_notifications_read():
    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    company = _company_for_user(user_id)
    if not company:
        return _json_error("Company profile not found", 404)

    unread_notifications = _notification_query_for_company(company.user_id).filter(
        Notification.is_read.is_(False)
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


__all__ = ["company_bp"]