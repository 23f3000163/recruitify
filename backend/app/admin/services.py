"""Service layer for admin dashboard and management operations."""

from math import ceil

from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from app.models import Application, Company, PlacementDrive, Student, User, db


ALLOWED_ORDER_VALUES = {"asc", "desc"}


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


def _company_to_dict(company):
    payload = company.to_dict()
    payload.update(
        {
            "id": company.company_id,
            "name": company.company_name,
            "industry": None,
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


def approve_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return _error("Company not found", 404)

    try:
        company.approval_status = "approved"
        db.session.commit()
        return _ok(_company_to_dict(company))
    except Exception:
        db.session.rollback()
        return _error("Failed to approve company", 500)


def reject_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return _error("Company not found", 404)

    try:
        company.approval_status = "rejected"
        db.session.commit()
        return _ok(_company_to_dict(company))
    except Exception:
        db.session.rollback()
        return _error("Failed to reject company", 500)


def _set_company_inactive(company_id, action_error_message, success_payload):
    company = db.session.get(Company, company_id)
    if not company:
        return _error("Company not found", 404)

    if not company.user:
        return _error("Company user not found", 404)

    try:
        company.user.is_active = False
        db.session.commit()
        return _ok(success_payload(company))
    except Exception:
        db.session.rollback()
        return _error(action_error_message, 500)


def deactivate_company(company_id):
    return _set_company_inactive(
        company_id=company_id,
        action_error_message="Failed to deactivate company",
        success_payload=_company_to_dict,
    )


def soft_delete_company(company_id):
    return _set_company_inactive(
        company_id=company_id,
        action_error_message="Failed to delete company",
        success_payload=lambda _company: {"message": "Company deactivated successfully"},
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


def deactivate_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return _error("Student not found", 404)

    if not student.user:
        return _error("Student user not found", 404)

    try:
        student.user.is_active = False
        db.session.commit()
        return _ok(_student_to_dict(student))
    except Exception:
        db.session.rollback()
        return _error("Failed to deactivate student", 500)


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


def approve_job(job_id):
    job = db.session.get(PlacementDrive, job_id)
    if not job:
        return _error("Job not found", 404)

    try:
        job.status = "approved"
        db.session.commit()
        return _ok(_job_to_dict(job))
    except Exception:
        db.session.rollback()
        return _error("Failed to approve job", 500)


def reject_job(job_id):
    job = db.session.get(PlacementDrive, job_id)
    if not job:
        return _error("Job not found", 404)

    try:
        job.status = "closed"
        db.session.commit()
        return _ok(_job_to_dict(job))
    except Exception:
        db.session.rollback()
        return _error("Failed to reject job", 500)


def soft_delete_job(job_id):
    job = db.session.get(PlacementDrive, job_id)
    if not job:
        return _error("Job not found", 404)

    try:
        job.status = "closed"
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
