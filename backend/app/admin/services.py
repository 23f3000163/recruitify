"""Service layer for admin dashboard and management operations."""

from datetime import datetime, timezone
from math import ceil

from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from app.models import (
    ActivityLog,
    Application,
    Company,
    Notification,
    PlacementDrive,
    Student,
    User,
    db,
)


ALLOWED_ORDER_VALUES = {"asc", "desc"}
ALLOWED_APPLICATION_STATUSES = {
    "applied",
    "shortlisted",
    "selected",
    "interviewed",
    "rejected",
    "waitlisted",
}
ALLOWED_ACTIVITY_STATUSES = {"success", "danger", "warning", "info"}
ALLOWED_NOTIFICATION_READ_FILTERS = {"all", "true", "false"}


def _ok(data, status_code=200):
    return {"success": True, "data": data}, status_code


def _error(message, status_code=400):
    return {"success": False, "error": message}, status_code


def _apply_sort(query, model, sort_by, order, default_sort_field):
    sort_column_name = sort_by or default_sort_field
    if not hasattr(model, sort_column_name):
        sort_column_name = default_sort_field

    if order not in ALLOWED_ORDER_VALUES:
        order = "desc"

    sort_column = getattr(model, sort_column_name)
    sort_expression = sort_column.asc() if order == "asc" else sort_column.desc()
    return query.order_by(sort_expression), None


def _paginate_query(query, page, limit):
    total = query.count()
    pages = ceil(total / limit) if total else 0
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total, pages


def _paginated_result(items, total, page, pages):
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
    }


def _append_activity_log(actor_user_id, action, target=None, status="info"):
    try:
        user_id = int(actor_user_id)
    except (TypeError, ValueError):
        return

    normalized_status = status if status in ALLOWED_ACTIVITY_STATUSES else "info"
    db.session.add(
        ActivityLog(
            user_id=user_id,
            action=(action or "Action").strip(),
            target=(target or "").strip() or None,
            status=normalized_status,
        )
    )


def _company_to_dict(company):
    payload = company.to_dict()
    payload.update(
        {
            "id": company.company_id,
            "name": company.company_name,
            "industry": company.industry,
            "status": company.approval_status,
            "is_active": bool(company.user and company.user.is_active),
        }
    )
    return payload


def _student_to_dict(student):
    payload = student.to_dict()
    payload.update(
        {
            "id": student.student_id,
            "name": student.user.username if student.user else None,
            "email": student.user.email if student.user else None,
            "is_active": bool(student.user and student.user.is_active),
        }
    )
    return payload


def _job_to_dict(job):
    payload = job.to_dict()
    payload.update(
        {
            "id": job.drive_id,
            "title": job.job_title,
            "status": job.status,
        }
    )
    return payload


def _application_to_dict(application):
    payload = application.to_dict()
    payload.update(
        {
            "id": application.application_id,
            "student": _student_to_dict(application.student)
            if application.student
            else None,
            "job": _job_to_dict(application.drive) if application.drive else None,
        }
    )
    return payload


def _activity_log_to_dict(log):
    status = (log.status or "info").strip().lower()
    if status not in ALLOWED_ACTIVITY_STATUSES:
        status = "info"

    return {
        "id": log.log_id,
        "log_id": log.log_id,
        "user_id": log.user_id,
        "action": log.action,
        "actor": log.user.username if log.user else f"User #{log.user_id}",
        "target": log.target or "-",
        "status": status,
        "time": log.timestamp.isoformat() if log.timestamp else None,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
    }


def _notification_query_for_admin(admin_user_id):
    return Notification.query.filter(
        Notification.recipient_id == admin_user_id,
        Notification.notification_type == "in_app",
    )


def _notification_to_dict(notification):
    return notification.to_dict()


def list_notifications(admin_user_id, page, limit, is_read="all"):
    read_filter = (is_read or "all").strip().lower()
    if read_filter not in ALLOWED_NOTIFICATION_READ_FILTERS:
        return _error("is_read must be one of all, true, or false", 400)

    query = _notification_query_for_admin(admin_user_id)
    if read_filter == "true":
        query = query.filter(Notification.is_read.is_(True))
    elif read_filter == "false":
        query = query.filter(Notification.is_read.is_(False))

    ordered_query = query.order_by(
        Notification.created_at.desc(),
        Notification.notification_id.desc(),
    )
    items, total, pages = _paginate_query(ordered_query, page, limit)

    unread_count = _notification_query_for_admin(admin_user_id).filter(
        Notification.is_read.is_(False)
    ).count()

    return _ok(
        {
            "items": [_notification_to_dict(item) for item in items],
            "total": total,
            "page": page,
            "pages": pages,
            "limit": limit,
            "unread_count": unread_count,
        }
    )


def mark_notification_read(admin_user_id, notification_id):
    notification = _notification_query_for_admin(admin_user_id).filter(
        Notification.notification_id == notification_id
    ).first()
    if not notification:
        return _error("Notification not found", 404)

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _error("Unable to update notification", 500)

    unread_count = _notification_query_for_admin(admin_user_id).filter(
        Notification.is_read.is_(False)
    ).count()

    return _ok(
        {
            "notification": _notification_to_dict(notification),
            "unread_count": unread_count,
        }
    )


def mark_all_notifications_read(admin_user_id):
    unread_notifications = _notification_query_for_admin(admin_user_id).filter(
        Notification.is_read.is_(False)
    ).all()

    if not unread_notifications:
        return _ok({"updated_count": 0, "unread_count": 0})

    read_time = datetime.now(timezone.utc)
    for notification in unread_notifications:
        notification.is_read = True
        notification.read_at = read_time

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _error("Unable to update notifications", 500)

    return _ok(
        {
            "updated_count": len(unread_notifications),
            "unread_count": 0,
        }
    )


def get_dashboard_stats():
    total_students = db.session.query(func.count(Student.student_id)).scalar() or 0
    total_companies = db.session.query(func.count(Company.company_id)).scalar() or 0
    total_jobs = db.session.query(func.count(PlacementDrive.drive_id)).scalar() or 0
    total_applications = (
        db.session.query(func.count(Application.application_id)).scalar() or 0
    )

    return _ok(
        {
            "total_students": total_students,
            "total_companies": total_companies,
            "total_jobs": total_jobs,
            "total_applications": total_applications,
        }
    )


def list_activity_logs(limit=20):
    try:
        parsed_limit = int(limit)
    except (TypeError, ValueError):
        parsed_limit = 20

    parsed_limit = max(1, min(parsed_limit, 200))

    query = ActivityLog.query.options(selectinload(ActivityLog.user)).order_by(
        ActivityLog.timestamp.desc(),
        ActivityLog.log_id.desc(),
    )
    logs = query.limit(parsed_limit).all()
    total = db.session.query(func.count(ActivityLog.log_id)).scalar() or 0

    return _ok(
        {
            "items": [_activity_log_to_dict(log) for log in logs],
            "total": total,
            "limit": parsed_limit,
        }
    )


def list_companies(page, limit, sort_by, order):
    query = Company.query
    query, sort_error = _apply_sort(
        query=query,
        model=Company,
        sort_by=sort_by,
        order=order,
        default_sort_field="created_at",
    )
    if sort_error:
        return sort_error

    companies, total, pages = _paginate_query(query, page, limit)
    items = [_company_to_dict(company) for company in companies]
    return _ok(_paginated_result(items, total, page, pages))


def approve_company(company_id, actor_user_id=None):
    company = db.session.get(Company, company_id)
    if not company:
        return _error("Company not found", 404)

    try:
        company.approval_status = "approved"
        _append_activity_log(actor_user_id, "Company Approved", company.company_name, "success")
        db.session.commit()
        return _ok(_company_to_dict(company))
    except Exception:
        db.session.rollback()
        return _error("Failed to approve company", 500)


def reject_company(company_id, actor_user_id=None):
    company = db.session.get(Company, company_id)
    if not company:
        return _error("Company not found", 404)

    try:
        company.approval_status = "rejected"
        _append_activity_log(actor_user_id, "Company Rejected", company.company_name, "danger")
        db.session.commit()
        return _ok(_company_to_dict(company))
    except Exception:
        db.session.rollback()
        return _error("Failed to reject company", 500)


def _set_company_inactive(
    company_id,
    action_error_message,
    success_payload,
    actor_user_id=None,
    audit_action="Company Deactivated",
    audit_status="warning",
):
    company = db.session.get(Company, company_id)
    if not company:
        return _error("Company not found", 404)

    if not company.user:
        return _error("Company user not found", 404)

    try:
        company.user.is_active = False
        _append_activity_log(actor_user_id, audit_action, company.company_name, audit_status)
        db.session.commit()
        return _ok(success_payload(company))
    except Exception:
        db.session.rollback()
        return _error(action_error_message, 500)


def deactivate_company(company_id, actor_user_id=None):
    return _set_company_inactive(
        company_id=company_id,
        action_error_message="Failed to deactivate company",
        success_payload=_company_to_dict,
        actor_user_id=actor_user_id,
        audit_action="Company Deactivated",
        audit_status="warning",
    )


def activate_company(company_id, actor_user_id=None):
    company = db.session.get(Company, company_id)
    if not company:
        return _error("Company not found", 404)

    if not company.user:
        return _error("Company user not found", 404)

    try:
        company.user.is_active = True
        company.approval_status = "approved"
        _append_activity_log(actor_user_id, "Company Activated", company.company_name, "success")
        db.session.commit()
        return _ok(_company_to_dict(company))
    except Exception:
        db.session.rollback()
        return _error("Failed to activate company", 500)


def soft_delete_company(company_id, actor_user_id=None):
    return _set_company_inactive(
        company_id=company_id,
        action_error_message="Failed to delete company",
        success_payload=lambda _company: {"message": "Company deactivated successfully"},
        actor_user_id=actor_user_id,
        audit_action="Company Removed",
        audit_status="warning",
    )


def list_students(page, limit, sort_by, order):
    query = Student.query
    query, sort_error = _apply_sort(
        query=query,
        model=Student,
        sort_by=sort_by,
        order=order,
        default_sort_field="created_at",
    )
    if sort_error:
        return sort_error

    students, total, pages = _paginate_query(query, page, limit)
    items = [_student_to_dict(student) for student in students]
    return _ok(_paginated_result(items, total, page, pages))


def deactivate_student(student_id, actor_user_id=None):
    student = db.session.get(Student, student_id)
    if not student:
        return _error("Student not found", 404)

    if not student.user:
        return _error("Student user not found", 404)

    try:
        student.user.is_active = False
        student_name = student.user.username if student.user else f"Student #{student.student_id}"
        _append_activity_log(actor_user_id, "Student Deactivated", student_name, "warning")
        db.session.commit()
        return _ok(_student_to_dict(student))
    except Exception:
        db.session.rollback()
        return _error("Failed to deactivate student", 500)


def activate_student(student_id, actor_user_id=None):
    student = db.session.get(Student, student_id)
    if not student:
        return _error("Student not found", 404)

    if not student.user:
        return _error("Student user not found", 404)

    try:
        student.user.is_active = True
        student_name = student.user.username if student.user else f"Student #{student.student_id}"
        _append_activity_log(actor_user_id, "Student Activated", student_name, "success")
        db.session.commit()
        return _ok(_student_to_dict(student))
    except Exception:
        db.session.rollback()
        return _error("Failed to activate student", 500)


def list_jobs(page, limit, sort_by, order, company_id=None):
    query = PlacementDrive.query
    if company_id is not None:
        query = query.filter(PlacementDrive.company_id == company_id)

    query, sort_error = _apply_sort(
        query=query,
        model=PlacementDrive,
        sort_by=sort_by,
        order=order,
        default_sort_field="created_at",
    )
    if sort_error:
        return sort_error

    jobs, total, pages = _paginate_query(query, page, limit)
    items = [_job_to_dict(job) for job in jobs]
    return _ok(_paginated_result(items, total, page, pages))


def approve_job(job_id, actor_user_id=None):
    job = db.session.get(PlacementDrive, job_id)
    if not job:
        return _error("Job not found", 404)

    try:
        job.status = "approved"
        _append_activity_log(actor_user_id, "Drive Approved", job.job_title, "success")
        db.session.commit()
        return _ok(_job_to_dict(job))
    except Exception:
        db.session.rollback()
        return _error("Failed to approve job", 500)


def reject_job(job_id, actor_user_id=None):
    job = db.session.get(PlacementDrive, job_id)
    if not job:
        return _error("Job not found", 404)

    try:
        job.status = "closed"
        _append_activity_log(actor_user_id, "Drive Rejected", job.job_title, "danger")
        db.session.commit()
        return _ok(_job_to_dict(job))
    except Exception:
        db.session.rollback()
        return _error("Failed to reject job", 500)


def soft_delete_job(job_id, actor_user_id=None):
    job = db.session.get(PlacementDrive, job_id)
    if not job:
        return _error("Job not found", 404)

    try:
        job.status = "closed"
        _append_activity_log(actor_user_id, "Drive Removed", job.job_title, "warning")
        db.session.commit()
        return _ok({"message": "Job deleted successfully"})
    except Exception:
        db.session.rollback()
        return _error("Failed to delete job", 500)


def search_companies(query_text, page, limit, sort_by, order):
    query_text = query_text.strip()
    query = Company.query.join(User, Company.user_id == User.user_id).filter(
        or_(
            Company.company_name.ilike(f"%{query_text}%"),
            Company.industry.ilike(f"%{query_text}%"),
            Company.company_description.ilike(f"%{query_text}%"),
        )
    )

    query, sort_error = _apply_sort(
        query=query,
        model=Company,
        sort_by=sort_by,
        order=order,
        default_sort_field="created_at",
    )
    if sort_error:
        return sort_error

    companies, total, pages = _paginate_query(query, page, limit)
    items = [_company_to_dict(company) for company in companies]
    return _ok(_paginated_result(items, total, page, pages))


def search_students(query_text, page, limit, sort_by, order):
    query_text = query_text.strip()
    search_conditions = [
        User.username.ilike(f"%{query_text}%"),
        User.email.ilike(f"%{query_text}%"),
        Student.roll_number.ilike(f"%{query_text}%"),
    ]

    if hasattr(Student, "phone"):
        search_conditions.append(Student.phone.ilike(f"%{query_text}%"))
    if hasattr(User, "phone"):
        search_conditions.append(User.phone.ilike(f"%{query_text}%"))

    query = Student.query.join(User, Student.user_id == User.user_id).filter(
        or_(*search_conditions)
    )

    query, sort_error = _apply_sort(
        query=query,
        model=Student,
        sort_by=sort_by,
        order=order,
        default_sort_field="created_at",
    )
    if sort_error:
        return sort_error

    students, total, pages = _paginate_query(query, page, limit)
    items = [_student_to_dict(student) for student in students]
    return _ok(_paginated_result(items, total, page, pages))


def list_applications(page, limit, sort_by, order):
    query = Application.query.options(
        selectinload(Application.student).selectinload(Student.user),
        selectinload(Application.drive),
    )
    query, sort_error = _apply_sort(
        query=query,
        model=Application,
        sort_by=sort_by,
        order=order,
        default_sort_field="created_at",
    )
    if sort_error:
        return sort_error

    applications, total, pages = _paginate_query(query, page, limit)
    items = [_application_to_dict(application) for application in applications]
    return _ok(_paginated_result(items, total, page, pages))


def update_application_status(
    application_id,
    status,
    rejection_reason=None,
    notes=None,
    actor_user_id=None,
):
    application = db.session.get(Application, application_id)
    if not application:
        return _error("Application not found", 404)

    target_status = (status or "").strip().lower()
    if target_status not in ALLOWED_APPLICATION_STATUSES:
        return _error("Invalid application status", 400)

    try:
        application.status = target_status

        if target_status == "rejected":
            cleaned_reason = (
                rejection_reason.strip()
                if isinstance(rejection_reason, str)
                else rejection_reason
            )
            application.rejection_reason = cleaned_reason or application.rejection_reason
        else:
            application.rejection_reason = None

        if notes is not None:
            cleaned_notes = notes.strip() if isinstance(notes, str) else notes
            application.notes = cleaned_notes or None

        _append_activity_log(
            actor_user_id,
            "Application Updated",
            f"#{application.application_id} -> {target_status}",
            "success",
        )

        db.session.commit()
        return _ok(_application_to_dict(application))
    except Exception:
        db.session.rollback()
        return _error("Failed to update application status", 500)
