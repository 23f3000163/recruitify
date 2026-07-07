"""Service layer for company application listing operations."""

from math import ceil

from sqlalchemy import or_

from app.models import Application, PlacementDrive, Student, User, db


ALLOWED_APPLICATION_STATUSES = {
    "applied",
    "shortlisted",
    "selected",
    "interviewed",
    "rejected",
    "waitlisted",
}


def _ok(data, status_code=200):
    return {"success": True, "data": data}, status_code


def _error(message, status_code=400):
    return {"success": False, "error": message}, status_code


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


def list_company_applications(company, *, status="all", q="", drive_id="all", page=1, limit=10):
    status_filter = (status or "all").strip().lower()
    query_text = (q or "").strip()
    drive_id_raw = str(drive_id if drive_id is not None else "all").strip().lower()

    base_query = (
        db.session.query(Application, Student, User, PlacementDrive)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Student, Application.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
        .filter(PlacementDrive.company_id == company.company_id)
    )

    if status_filter != "all":
        if status_filter not in ALLOWED_APPLICATION_STATUSES:
            return _error("Invalid application status filter", 400)
        base_query = base_query.filter(Application.status == status_filter)

    if drive_id_raw != "all":
        try:
            drive_id_value = int(drive_id_raw)
        except (TypeError, ValueError):
            return _error("drive_id must be an integer", 400)

        base_query = base_query.filter(PlacementDrive.drive_id == drive_id_value)

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

    return _ok(
        {
            "items": items,
            "total": total,
            "page": page,
            "pages": pages,
            "limit": limit,
            "drive_options": _company_drive_options(company.company_id),
        }
    )
