"""ATS-compatible application routes with strict transition controls."""

import re
from datetime import datetime, timezone
from math import ceil
from urllib.parse import unquote, urlparse

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.models import (
    Application,
    Company,
    Interview,
    Placement,
    PlacementDrive,
    PlacementOffer,
    Student,
    User,
    db,
)
from app.applications.status_engine import (
    ATS_STATUSES,
    ATS_TO_LEGACY_STATUS,
    ATS_TRANSITIONS,
    application_ats_status,
    normalize_status_input,
    status_label,
)

applications_bp = Blueprint("applications", __name__)

MAX_LIMIT = 100
MAX_NOTES_LENGTH = 500
MAX_REJECTION_REASON_LENGTH = 300
MAX_SCREEN_KEYWORDS = 40

KEYWORD_ALIAS_MAP = {
    "node.js": "nodejs",
    "node js": "nodejs",
    "react.js": "react",
    "vue.js": "vue",
    "c plus plus": "c++",
    "cplusplus": "c++",
    "c sharp": "c#",
    "asp.net": "dotnet",
    ".net": "dotnet",
}

TITLE_STOP_WORDS = {
    "and",
    "for",
    "with",
    "the",
    "senior",
    "junior",
    "intern",
    "engineer",
    "developer",
    "specialist",
    "analyst",
    "associate",
}


def _json_error(message, status_code=400):
    return jsonify({"success": False, "error": message}), status_code


def _coerce_utc(value):
    if not value:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _current_user_id():
    identity = get_jwt_identity()
    raw_user_id = identity.get("user_id") if isinstance(identity, dict) else identity
    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        return None


def _current_role():
    claims = get_jwt()
    return str(claims.get("role") or "").strip().lower()


def _require_roles(*allowed_roles):
    current_role = _current_role()
    if current_role not in allowed_roles:
        return _json_error("Forbidden: insufficient permissions", 403)
    return None


def _student_for_user(user_id):
    return Student.query.filter_by(user_id=user_id).first()


def _company_for_user(user_id):
    return Company.query.filter_by(user_id=user_id).first()


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


def _normalize_status_input(raw_status):
    return normalize_status_input(raw_status)


def _status_label(status):
    return status_label(status)


def _normalize_optional_text(raw_value, field_name, max_length):
    if raw_value is None:
        return None, None
    if not isinstance(raw_value, str):
        return None, f"{field_name} must be a string"

    cleaned = raw_value.strip()
    if len(cleaned) > max_length:
        return None, f"{field_name} must be at most {max_length} characters"

    return cleaned or None, None


def _normalize_keyword(raw_value):
    normalized = re.sub(r"\s+", " ", str(raw_value or "").strip().lower())
    if not normalized:
        return ""
    return KEYWORD_ALIAS_MAP.get(normalized, normalized)


def _split_keywords(raw_text):
    text = str(raw_text or "").strip()
    if not text:
        return []

    tokens = re.split(r"[,;|\n/]+", text)
    items = []
    seen = set()
    for token in tokens:
        keyword = _normalize_keyword(token)
        if not keyword or keyword in seen:
            continue
        seen.add(keyword)
        items.append(keyword)
    return items


def _extract_word_keywords(raw_text):
    text = str(raw_text or "").strip().lower()
    if not text:
        return []

    words = re.findall(r"[a-z0-9][a-z0-9+#\.]{1,}", text)
    items = []
    seen = set()
    for word in words:
        keyword = _normalize_keyword(word)
        if not keyword or keyword in seen:
            continue
        seen.add(keyword)
        items.append(keyword)
    return items


def _resume_filename_keywords(resume_url):
    raw_url = str(resume_url or "").strip()
    if not raw_url:
        return []

    parsed_url = urlparse(raw_url)
    path = parsed_url.path or raw_url
    filename = unquote(path.split("/")[-1]).strip()
    if not filename:
        return []

    base_name = filename.rsplit(".", 1)[0]
    chunks = re.split(r"[^a-zA-Z0-9+#\.]+", base_name)

    items = []
    seen = set()
    for chunk in chunks:
        keyword = _normalize_keyword(chunk)
        if not keyword or keyword in seen:
            continue
        seen.add(keyword)
        items.append(keyword)
    return items


def _unique_keywords(*keyword_lists):
    items = []
    seen = set()
    for keyword_list in keyword_lists:
        for value in keyword_list:
            keyword = _normalize_keyword(value)
            if not keyword or keyword in seen:
                continue
            seen.add(keyword)
            items.append(keyword)
    return items


def _keywords_from_drive(drive, payload_keywords=None):
    payload_list = []
    if payload_keywords is not None:
        if isinstance(payload_keywords, list):
            payload_list = _unique_keywords(payload_keywords)
        elif isinstance(payload_keywords, str):
            payload_list = _split_keywords(payload_keywords)
        else:
            return [], "keywords must be a string or an array of strings"

    drive_keywords = _split_keywords(drive.required_skills)
    if not drive_keywords:
        fallback_keywords = [
            word
            for word in _extract_word_keywords(drive.job_title)
            if word not in TITLE_STOP_WORDS
        ]
        drive_keywords = fallback_keywords[:6]

    final_keywords = _unique_keywords(payload_list or drive_keywords)
    if not final_keywords:
        return [], "No target keywords available for this job"

    return final_keywords[:MAX_SCREEN_KEYWORDS], None


def _candidate_keywords_from_student(student):
    skill_keywords = _split_keywords(student.skills)
    experience_keywords = _extract_word_keywords(student.experience_summary)
    resume_keywords = _resume_filename_keywords(student.resume_url)
    return _unique_keywords(skill_keywords, experience_keywords, resume_keywords)


def _keyword_is_matched(target_keyword, candidate_keywords):
    if target_keyword in candidate_keywords:
        return True

    if " " in target_keyword:
        parts = [part for part in target_keyword.split(" ") if part]
        if parts and all(part in candidate_keywords for part in parts):
            return True

    return False


def _score_keyword_match(target_keywords, candidate_keywords):
    matched = []
    missing = []

    candidate_set = set(candidate_keywords)
    for keyword in target_keywords:
        if _keyword_is_matched(keyword, candidate_set):
            matched.append(keyword)
        else:
            missing.append(keyword)

    total = len(target_keywords)
    matched_count = len(matched)
    coverage_ratio = (matched_count / total) if total else 0.0
    score = round(coverage_ratio * 100, 2)

    if score >= 75:
        recommendation = "strong"
    elif score >= 50:
        recommendation = "moderate"
    else:
        recommendation = "needs-improvement"

    return {
        "score": score,
        "recommendation": recommendation,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "matched_count": matched_count,
        "total_keywords": total,
        "coverage_ratio": round(coverage_ratio, 4),
    }


def _parse_positive_int(raw_value, field_name):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be an integer"

    if value < 1:
        return None, f"{field_name} must be greater than 0"

    return value, None


def _application_ats_status(application):
    return application_ats_status(application)


def _apply_ats_status_filter(query, status_filter):
    if status_filter == "all":
        return query

    if status_filter == "applied":
        return query.filter(Application.status == "applied")

    if status_filter == "shortlisted":
        return query.filter(Application.status.in_(("shortlisted", "waitlisted")))

    if status_filter == "interview":
        return query.filter(Application.status == "interviewed")

    if status_filter == "offered":
        return query.filter(
            Application.status == "selected",
            or_(
                PlacementOffer.offer_id.is_(None),
                PlacementOffer.status == "offered",
            ),
        )

    if status_filter == "placed":
        return query.filter(
            Application.status == "selected",
            PlacementOffer.status == "accepted",
        )

    if status_filter == "rejected":
        return query.filter(
            or_(
                Application.status == "rejected",
                PlacementOffer.status == "rejected",
            )
        )

    return query


def _serialize_offer(offer):
    if not offer:
        return None

    return {
        "offer_id": offer.offer_id,
        "status": offer.status,
        "position": offer.position,
        "salary": offer.salary,
        "joining_date": offer.joining_date.isoformat() if offer.joining_date else None,
        "created_at": offer.created_at.isoformat() if offer.created_at else None,
    }


def _serialize_latest_interview(application_id):
    latest_interview = (
        Interview.query.filter_by(application_id=application_id)
        .order_by(Interview.interview_date.desc(), Interview.interview_id.desc())
        .first()
    )

    if not latest_interview:
        return None

    return {
        "interview_id": latest_interview.interview_id,
        "interview_date": (
            latest_interview.interview_date.isoformat()
            if latest_interview.interview_date
            else None
        ),
        "interview_mode": latest_interview.interview_mode,
        "interviewer_name": latest_interview.interviewer_name,
        "result": latest_interview.result,
        "feedback": latest_interview.feedback,
    }


def _serialize_application(
    application,
    drive=None,
    company=None,
    student=None,
    student_user=None,
    offer=None,
    include_student=False,
    include_interview=False,
):
    drive_obj = drive or application.drive
    company_obj = company or (drive_obj.company if drive_obj else None)
    offer_obj = offer or application.placement_offer

    ats_status = _application_ats_status(application)
    payload = application.to_dict()
    payload.update(
        {
            "id": application.application_id,
            "application_id": application.application_id,
            "job_id": application.drive_id,
            "drive_id": application.drive_id,
            "company_id": company_obj.company_id if company_obj else None,
            "status": ats_status,
            "legacy_status": application.status,
            "status_label": _status_label(ats_status),
            "applied_at": payload.get("applied_at") or payload.get("application_date"),
            "drive": {
                "id": drive_obj.drive_id if drive_obj else application.drive_id,
                "title": drive_obj.job_title if drive_obj else None,
                "location": drive_obj.job_location if drive_obj else None,
                "application_deadline": (
                    drive_obj.application_deadline.isoformat()
                    if drive_obj and drive_obj.application_deadline
                    else None
                ),
                "salary_lpa": drive_obj.salary_lpa if drive_obj else None,
            },
            "company": {
                "id": company_obj.company_id if company_obj else None,
                "name": company_obj.company_name if company_obj else None,
                "industry": company_obj.industry if company_obj else None,
            },
            "offer": _serialize_offer(offer_obj),
        }
    )

    if include_interview:
        payload["latest_interview"] = _serialize_latest_interview(application.application_id)

    if include_student:
        student_obj = student or application.student
        user_obj = student_user or (student_obj.user if student_obj else None)
        payload.update(
            {
                "student": {
                    "student_id": student_obj.student_id if student_obj else None,
                    "name": user_obj.username if user_obj else None,
                    "email": user_obj.email if user_obj else None,
                    "branch": student_obj.branch if student_obj else None,
                    "year": student_obj.year if student_obj else None,
                    "cgpa": student_obj.cgpa if student_obj else None,
                    "resume_url": student_obj.resume_url if student_obj else None,
                },
                "student_name": user_obj.username if user_obj else None,
                "student_email": user_obj.email if user_obj else None,
                "student_branch": student_obj.branch if student_obj else None,
                "student_year": student_obj.year if student_obj else None,
                "student_cgpa": student_obj.cgpa if student_obj else None,
                "resume_url": student_obj.resume_url if student_obj else None,
                "drive_title": drive_obj.job_title if drive_obj else None,
            }
        )

    return payload


def _ensure_transition_allowed(current_status, target_status):
    if current_status == target_status:
        return True

    return target_status in ATS_TRANSITIONS.get(current_status, set())


@applications_bp.post("/applications/screener")
@jwt_required()
def score_resume_keywords():
    role_error = _require_roles("student", "company", "admin")
    if role_error:
        return role_error

    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    payload = request.get_json(silent=True) or {}
    role = _current_role()

    application = None
    drive = None
    student = None

    if role == "student":
        job_id, job_error = _parse_positive_int(
            payload.get("job_id", payload.get("drive_id")),
            "job_id",
        )
        if job_error:
            return _json_error(job_error, 400)

        student = _student_for_user(user_id)
        if not student:
            return _json_error("Student profile not found", 404)

        drive = db.session.get(PlacementDrive, job_id)
        if not drive:
            return _json_error("Job not found", 404)
    else:
        application_id, application_error = _parse_positive_int(
            payload.get("application_id"),
            "application_id",
        )
        if application_error:
            return _json_error(application_error, 400)

        application = db.session.get(Application, application_id)
        if not application:
            return _json_error("Application not found", 404)

        drive = application.drive
        if not drive:
            return _json_error("Job not found for this application", 404)

        student = application.student
        if not student:
            return _json_error("Student profile not found", 404)

        if role == "company":
            company = _company_for_user(user_id)
            if not company:
                return _json_error("Company profile not found", 404)

            if drive.company_id != company.company_id:
                return _json_error("Forbidden: cannot screen applications for this job", 403)

    target_keywords, keyword_error = _keywords_from_drive(
        drive,
        payload_keywords=payload.get("keywords"),
    )
    if keyword_error:
        return _json_error(keyword_error, 400)

    candidate_keywords = _candidate_keywords_from_student(student)
    analysis = _score_keyword_match(target_keywords, candidate_keywords)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "job": {
                        "job_id": drive.drive_id,
                        "title": drive.job_title,
                        "required_skills": drive.required_skills,
                        "target_keywords": target_keywords,
                    },
                    "candidate": {
                        "student_id": student.student_id,
                        "application_id": (
                            application.application_id if application is not None else None
                        ),
                        "skills": student.skills,
                        "resume_url": student.resume_url,
                        "resume_uploaded_at": (
                            student.resume_uploaded_at.isoformat()
                            if student.resume_uploaded_at
                            else None
                        ),
                    },
                    "analysis": analysis,
                    "meta": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "role": role,
                    },
                },
            }
        ),
        200,
    )


@applications_bp.post("/applications")
@jwt_required()
def create_application():
    role_error = _require_roles("student")
    if role_error:
        return role_error

    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    student = _student_for_user(user_id)
    if not student:
        return _json_error("Student profile not found", 404)

    payload = request.get_json(silent=True) or {}
    raw_job_id = payload.get("job_id", payload.get("drive_id"))

    try:
        job_id = int(raw_job_id)
    except (TypeError, ValueError):
        return _json_error("job_id is required and must be an integer", 400)

    if job_id < 1:
        return _json_error("job_id must be greater than 0", 400)

    drive_row = (
        db.session.query(PlacementDrive, Company)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(PlacementDrive.drive_id == job_id)
        .first()
    )
    if not drive_row:
        return _json_error("Job not found", 404)

    drive, company = drive_row

    if company.approval_status != "approved" or company.is_blacklisted:
        return _json_error("Job is not available because the company is not approved", 400)

    if drive.status != "approved":
        return _json_error("Job is not approved", 400)

    deadline = _coerce_utc(drive.application_deadline)
    if not deadline or deadline < datetime.now(timezone.utc):
        return _json_error("Job is not active", 400)

    duplicate = Application.query.filter_by(
        student_id=student.student_id,
        drive_id=drive.drive_id,
    ).first()
    if duplicate:
        return _json_error("Student has already applied for this job", 409)

    application = Application(
        student_id=student.student_id,
        drive_id=drive.drive_id,
        status="applied",
    )

    try:
        db.session.add(application)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("Student has already applied for this job", 409)
    except Exception:
        db.session.rollback()
        return _json_error("Unable to create application", 500)

    return (
        jsonify(
            {
                "success": True,
                "data": _serialize_application(
                    application,
                    drive=drive,
                    company=company,
                    include_interview=True,
                ),
            }
        ),
        201,
    )


@applications_bp.get("/applications/student")
@jwt_required()
def list_student_applications():
    role_error = _require_roles("student")
    if role_error:
        return role_error

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
    if status_filter != "all":
        normalized_filter = _normalize_status_input(status_filter)
        if not normalized_filter:
            return _json_error("Invalid application status filter", 400)
        status_filter = normalized_filter

    query_text = (request.args.get("q") or "").strip()

    query = (
        db.session.query(Application, PlacementDrive, Company, PlacementOffer)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .outerjoin(PlacementOffer, Application.application_id == PlacementOffer.application_id)
        .filter(Application.student_id == student.student_id)
    )

    if query_text:
        like_value = f"%{query_text}%"
        query = query.filter(
            or_(
                PlacementDrive.job_title.ilike(like_value),
                PlacementDrive.job_location.ilike(like_value),
                Company.company_name.ilike(like_value),
            )
        )

    query = _apply_ats_status_filter(query, status_filter)
    query = query.order_by(Application.updated_at.desc(), Application.application_id.desc())

    total = query.count()
    pages = ceil(total / limit) if total else 0
    rows = query.offset((page - 1) * limit).limit(limit).all()

    items = [
        _serialize_application(
            application,
            drive=drive,
            company=company,
            offer=offer,
            include_interview=True,
        )
        for application, drive, company, offer in rows
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


@applications_bp.get("/applications/job/<int:job_id>")
@jwt_required()
def list_job_applications(job_id):
    role_error = _require_roles("company", "admin")
    if role_error:
        return role_error

    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    drive = db.session.get(PlacementDrive, job_id)
    if not drive:
        return _json_error("Job not found", 404)

    current_role = _current_role()
    if current_role == "company":
        company = _company_for_user(user_id)
        if not company:
            return _json_error("Company profile not found", 404)
        if drive.company_id != company.company_id:
            return _json_error("Forbidden: cannot view applications for this job", 403)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    status_filter = (request.args.get("status") or "all").strip().lower()
    if status_filter != "all":
        normalized_filter = _normalize_status_input(status_filter)
        if not normalized_filter:
            return _json_error("Invalid application status filter", 400)
        status_filter = normalized_filter

    query_text = (request.args.get("q") or "").strip()

    query = (
        db.session.query(Application, Student, User, PlacementOffer)
        .join(Student, Application.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
        .outerjoin(PlacementOffer, Application.application_id == PlacementOffer.application_id)
        .filter(Application.drive_id == drive.drive_id)
    )

    if query_text:
        like_value = f"%{query_text}%"
        query = query.filter(
            or_(
                User.username.ilike(like_value),
                User.email.ilike(like_value),
                Student.roll_number.ilike(like_value),
            )
        )

    query = _apply_ats_status_filter(query, status_filter)
    query = query.order_by(Application.updated_at.desc(), Application.application_id.desc())

    total = query.count()
    pages = ceil(total / limit) if total else 0
    rows = query.offset((page - 1) * limit).limit(limit).all()

    company = drive.company
    items = [
        _serialize_application(
            application,
            drive=drive,
            company=company,
            student=student,
            student_user=user,
            offer=offer,
            include_student=True,
        )
        for application, student, user, offer in rows
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


@applications_bp.patch("/applications/<int:application_id>")
@jwt_required()
def update_application_status(application_id):
    role_error = _require_roles("company", "admin")
    if role_error:
        return role_error

    user_id = _current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    application = db.session.get(Application, application_id)
    if not application:
        return _json_error("Application not found", 404)

    drive = application.drive
    if not drive:
        return _json_error("Job not found for this application", 404)

    current_role = _current_role()
    if current_role == "company":
        company = _company_for_user(user_id)
        if not company:
            return _json_error("Company profile not found", 404)
        if drive.company_id != company.company_id:
            return _json_error("Forbidden: cannot update applications for this job", 403)

    payload = request.get_json(silent=True) or {}

    if "status" not in payload:
        return _json_error("status is required", 400)

    target_status = _normalize_status_input(payload.get("status"))
    if not target_status:
        return _json_error("Invalid application status", 400)

    current_status = _application_ats_status(application)
    if not _ensure_transition_allowed(current_status, target_status):
        return _json_error(
            f"Invalid status transition: {current_status} -> {target_status}",
            400,
        )

    notes = None
    if "notes" in payload:
        notes, notes_error = _normalize_optional_text(
            payload.get("notes"),
            "notes",
            MAX_NOTES_LENGTH,
        )
        if notes_error:
            return _json_error(notes_error, 400)

    rejection_reason = None
    if "rejection_reason" in payload:
        rejection_reason, reason_error = _normalize_optional_text(
            payload.get("rejection_reason"),
            "rejection_reason",
            MAX_REJECTION_REASON_LENGTH,
        )
        if reason_error:
            return _json_error(reason_error, 400)

    if target_status == "rejected":
        effective_reason = rejection_reason
        if effective_reason is None:
            effective_reason = (application.rejection_reason or "").strip() or None
        if not effective_reason:
            return _json_error(
                "rejection_reason is required when status is rejected",
                400,
            )
    else:
        effective_reason = None

    if target_status == "placed" and not application.placement_offer:
        return _json_error("Cannot mark as placed before an offer is created", 400)

    try:
        application.status = ATS_TO_LEGACY_STATUS[target_status]

        if "notes" in payload:
            application.notes = notes

        if target_status == "rejected":
            application.rejection_reason = effective_reason
            if application.placement_offer and application.placement_offer.status == "offered":
                application.placement_offer.status = "rejected"
        else:
            application.rejection_reason = None

        if target_status == "placed":
            offer = application.placement_offer
            offer.status = "accepted"

            existing_placement = Placement.query.filter_by(
                student_id=application.student_id,
                company_id=drive.company_id,
                drive_id=drive.drive_id,
            ).first()
            if not existing_placement:
                db.session.add(
                    Placement(
                        student_id=application.student_id,
                        company_id=drive.company_id,
                        drive_id=drive.drive_id,
                        position=offer.position,
                        salary=offer.salary,
                        joining_date=offer.joining_date,
                    )
                )

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to update application status", 500)

    student = application.student
    student_user = student.user if student else None
    company = drive.company

    return (
        jsonify(
            {
                "success": True,
                "data": _serialize_application(
                    application,
                    drive=drive,
                    company=company,
                    student=student,
                    student_user=student_user,
                    include_student=True,
                    include_interview=True,
                ),
            }
        ),
        200,
    )


__all__ = ["applications_bp"]
