"""Asynchronous CSV export workflow for student, company, and admin scopes."""

import csv
import hashlib
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

from flask import current_app
from sqlalchemy import func, or_

from app.models import (
    ActivityLog,
    Application,
    BackgroundJob,
    Company,
    ExportArtifact,
    Notification,
    Placement,
    PlacementDrive,
    Student,
    User,
    db,
)


ACTIVE_JOB_STATUSES = {"queued", "running"}
EXPORT_SCOPE_STUDENT_APPLICATIONS = "student_applications"
EXPORT_SCOPE_STUDENT_HISTORY = "student_history"
EXPORT_SCOPE_COMPANY_APPLICATIONS = "company_applications"
EXPORT_SCOPE_COMPANY_PLACEMENTS = "company_placements"
EXPORT_SCOPE_COMPANY_DRIVES = "company_drives"
EXPORT_SCOPE_ADMIN_COMPANIES = "admin_companies"
EXPORT_SCOPE_ADMIN_STUDENTS = "admin_students"
EXPORT_SCOPE_ADMIN_DRIVES = "admin_drives"
EXPORT_SCOPE_ADMIN_ANALYTICS = "admin_analytics"
EXPORT_SCOPE_ADMIN_AUDIT = "admin_audit"

STUDENT_EXPORT_SCOPES = {
    EXPORT_SCOPE_STUDENT_APPLICATIONS,
    EXPORT_SCOPE_STUDENT_HISTORY,
}
COMPANY_EXPORT_SCOPES = {
    EXPORT_SCOPE_COMPANY_APPLICATIONS,
    EXPORT_SCOPE_COMPANY_PLACEMENTS,
    EXPORT_SCOPE_COMPANY_DRIVES,
}
ADMIN_EXPORT_SCOPES = {
    EXPORT_SCOPE_ADMIN_COMPANIES,
    EXPORT_SCOPE_ADMIN_STUDENTS,
    EXPORT_SCOPE_ADMIN_DRIVES,
    EXPORT_SCOPE_ADMIN_ANALYTICS,
    EXPORT_SCOPE_ADMIN_AUDIT,
}
EXCLUDED_ADMIN_AUDIT_ACTIONS = {"Application Updated"}


def _utcnow():
    return datetime.now(timezone.utc)


def _student_for_user(user_id):
    return Student.query.filter_by(user_id=user_id).first()


def _company_for_user(user_id):
    return Company.query.filter_by(user_id=user_id).first()


def _active_export_job_for_user(user_id, export_scope):
    active_jobs = (
        BackgroundJob.query.filter(
            BackgroundJob.job_type == "export_csv",
            BackgroundJob.requested_by_user_id == user_id,
            BackgroundJob.status.in_(tuple(ACTIVE_JOB_STATUSES)),
        )
        .order_by(BackgroundJob.created_at.desc())
        .all()
    )

    for job in active_jobs:
        payload = job.payload or {}
        if payload.get("export_scope") == export_scope:
            return job
    return None


def create_student_export_job(user_id, export_scope=EXPORT_SCOPE_STUDENT_APPLICATIONS):
    """Create a new student export job unless one is already active for the same scope."""
    if export_scope not in STUDENT_EXPORT_SCOPES:
        return None, "Invalid export scope", None

    student = _student_for_user(user_id)
    if not student:
        return None, "Student profile not found", None

    active_job = _active_export_job_for_user(user_id, export_scope)
    if active_job:
        return active_job, None, True

    now_utc = _utcnow()
    job = BackgroundJob(
        job_type="export_csv",
        status="queued",
        requested_by_user_id=user_id,
        idempotency_key=(
            f"export:student:{student.student_id}:{export_scope}:"
            f"{now_utc.strftime('%Y%m%d%H%M%S')}"
        ),
        payload={
            "export_owner": "student",
            "export_scope": export_scope,
            "student_id": student.student_id,
            "requested_at": now_utc.isoformat(),
        },
    )
    db.session.add(job)
    db.session.commit()

    return job, None, False


def create_company_export_job(user_id, export_scope):
    """Create a new company export job unless one is already active for the same scope."""
    if export_scope not in COMPANY_EXPORT_SCOPES:
        return None, "Invalid export scope", None

    company = _company_for_user(user_id)
    if not company:
        return None, "Company profile not found", None

    active_job = _active_export_job_for_user(user_id, export_scope)
    if active_job:
        return active_job, None, True

    now_utc = _utcnow()
    job = BackgroundJob(
        job_type="export_csv",
        status="queued",
        requested_by_user_id=user_id,
        idempotency_key=(
            f"export:company:{company.company_id}:{export_scope}:"
            f"{now_utc.strftime('%Y%m%d%H%M%S')}"
        ),
        payload={
            "export_owner": "company",
            "export_scope": export_scope,
            "company_id": company.company_id,
            "requested_at": now_utc.isoformat(),
        },
    )
    db.session.add(job)
    db.session.commit()

    return job, None, False


def create_admin_export_job(user_id, export_scope):
    """Create a new admin export job unless one is already active for the same scope."""
    if export_scope not in ADMIN_EXPORT_SCOPES:
        return None, "Invalid export scope", None

    user = db.session.get(User, user_id)
    if not user or user.role != "admin":
        return None, "Admin profile not found", None

    active_job = _active_export_job_for_user(user_id, export_scope)
    if active_job:
        return active_job, None, True

    now_utc = _utcnow()
    job = BackgroundJob(
        job_type="export_csv",
        status="queued",
        requested_by_user_id=user_id,
        idempotency_key=(
            f"export:admin:{user_id}:{export_scope}:{now_utc.strftime('%Y%m%d%H%M%S')}"
        ),
        payload={
            "export_owner": "admin",
            "export_scope": export_scope,
            "requested_at": now_utc.isoformat(),
        },
    )
    db.session.add(job)
    db.session.commit()

    return job, None, False


def _build_student_applications_csv(student_id, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Student ID",
            "Company Name",
            "Drive Title",
            "Application Status",
            "Applied Date",
            "Updated Date",
        ]
    )

    for application, drive, company in rows:
        writer.writerow(
            [
                student_id,
                company.company_name if company else "",
                drive.job_title if drive else "",
                application.status,
                application.application_date.isoformat() if application.application_date else "",
                application.updated_at.isoformat() if application.updated_at else "",
            ]
        )

    return output.getvalue()


def _build_company_applications_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Student ID",
            "Student Name",
            "Student Email",
            "Drive Title",
            "Application Status",
            "Applied Date",
            "Updated Date",
        ]
    )

    for application, drive, student, user in rows:
        writer.writerow(
            [
                student.student_id if student else "",
                user.username if user else "",
                user.email if user else "",
                drive.job_title if drive else "",
                application.status,
                application.application_date.isoformat() if application.application_date else "",
                application.updated_at.isoformat() if application.updated_at else "",
            ]
        )

    return output.getvalue()


def _build_company_placements_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Student ID",
            "Student Name",
            "Student Email",
            "Drive Title",
            "Position",
            "Salary",
            "Joining Date",
            "Placement Date",
        ]
    )

    for placement, drive, student, user in rows:
        writer.writerow(
            [
                student.student_id if student else "",
                user.username if user else "",
                user.email if user else "",
                drive.job_title if drive else "",
                placement.position,
                placement.salary,
                placement.joining_date.isoformat() if placement.joining_date else "",
                placement.created_at.isoformat() if placement.created_at else "",
            ]
        )

    return output.getvalue()


def _build_company_drives_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Drive ID",
            "Job Title",
            "Status",
            "Salary LPA",
            "Applications Count",
            "Application Deadline",
            "Created Date",
        ]
    )

    for drive, applications_count in rows:
        writer.writerow(
            [
                drive.drive_id,
                drive.job_title,
                drive.status,
                drive.salary_lpa if drive.salary_lpa is not None else "",
                applications_count,
                drive.application_deadline.isoformat() if drive.application_deadline else "",
                drive.created_at.isoformat() if drive.created_at else "",
            ]
        )

    return output.getvalue()


def _build_student_history_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Application ID",
            "Drive Title",
            "Company Name",
            "Application Status",
            "Outcome",
            "Offer Status",
            "Offer Position",
            "Offer Salary",
            "Placement Position",
            "Placement Salary",
            "Updated Date",
        ]
    )

    for application, drive, company, offer, placement, outcome in rows:
        writer.writerow(
            [
                application.application_id,
                drive.job_title if drive else "",
                company.company_name if company else "",
                application.status,
                outcome,
                offer.status if offer else "",
                offer.position if offer else "",
                offer.salary if offer else "",
                placement.position if placement else "",
                placement.salary if placement else "",
                application.updated_at.isoformat() if application.updated_at else "",
            ]
        )

    return output.getvalue()


def _build_admin_companies_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Company ID",
            "Company Name",
            "Industry",
            "Website",
            "HR Contact Name",
            "HR Contact Email",
            "Approval Status",
            "Blacklisted",
            "Created Date",
        ]
    )

    for company, _user in rows:
        writer.writerow(
            [
                company.company_id,
                company.company_name,
                company.industry or "",
                company.website or "",
                company.hr_contact_name,
                company.hr_contact_email,
                company.approval_status,
                "yes" if company.is_blacklisted else "no",
                company.created_at.isoformat() if company.created_at else "",
            ]
        )

    return output.getvalue()


def _build_admin_students_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Student ID",
            "Student Name",
            "Student Email",
            "Roll Number",
            "Branch",
            "Year",
            "CGPA",
            "Profile Completed",
            "Blacklisted",
            "Created Date",
        ]
    )

    for student, user in rows:
        writer.writerow(
            [
                student.student_id,
                user.username if user else "",
                user.email if user else "",
                student.roll_number or "",
                student.branch or "",
                student.year or "",
                student.cgpa if student.cgpa is not None else "",
                "yes" if student.profile_completed else "no",
                "yes" if student.is_blacklisted else "no",
                student.created_at.isoformat() if student.created_at else "",
            ]
        )

    return output.getvalue()


def _build_admin_drives_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Drive ID",
            "Drive Title",
            "Company Name",
            "Status",
            "Salary LPA",
            "Applications Count",
            "Application Deadline",
            "Created Date",
        ]
    )

    for drive, company, applications_count in rows:
        writer.writerow(
            [
                drive.drive_id,
                drive.job_title,
                company.company_name if company else "",
                drive.status,
                drive.salary_lpa if drive.salary_lpa is not None else "",
                applications_count,
                drive.application_deadline.isoformat() if drive.application_deadline else "",
                drive.created_at.isoformat() if drive.created_at else "",
            ]
        )

    return output.getvalue()


def _build_admin_analytics_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])

    for metric, value in rows:
        writer.writerow([metric, value])

    return output.getvalue()


def _build_admin_audit_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Action", "Actor", "Target", "Status", "Timestamp"])

    for activity, user in rows:
        writer.writerow(
            [
                activity.action,
                user.username if user else "",
                activity.target or "",
                activity.status,
                activity.timestamp.isoformat() if activity.timestamp else "",
            ]
        )

    return output.getvalue()


def _write_export_artifact(file_prefix, csv_content, job_id=None):
    output_dir = Path(current_app.config.get("JOBS_EXPORT_OUTPUT_DIR"))
    output_dir.mkdir(parents=True, exist_ok=True)

    now_utc = _utcnow()
    timestamp = now_utc.strftime('%Y%m%d%H%M%S')
    if job_id:
        compact_job_id = str(job_id).replace("-", "")[:12]
        timestamp = f"{timestamp}-{compact_job_id}"

    filename = f"{file_prefix}-{timestamp}.csv"
    output_file = output_dir / filename
    output_file.write_text(csv_content, encoding="utf-8")

    return {
        "filename": filename,
        "path": str(output_file),
        "size_bytes": output_file.stat().st_size,
        "checksum": hashlib.sha256(csv_content.encode("utf-8")).hexdigest(),
    }


def _student_application_rows(student_id):
    return (
        db.session.query(Application, PlacementDrive, Company)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(Application.student_id == student_id)
        .order_by(Application.updated_at.desc(), Application.application_id.desc())
        .all()
    )


def _company_application_rows(company_id):
    return (
        db.session.query(Application, PlacementDrive, Student, User)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .join(Student, Application.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
        .filter(PlacementDrive.company_id == company_id)
        .order_by(Application.updated_at.desc(), Application.application_id.desc())
        .all()
    )


def _company_placement_rows(company_id):
    return (
        db.session.query(Placement, PlacementDrive, Student, User)
        .join(PlacementDrive, Placement.drive_id == PlacementDrive.drive_id)
        .join(Student, Placement.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
        .filter(Placement.company_id == company_id)
        .order_by(Placement.created_at.desc(), Placement.placement_id.desc())
        .all()
    )


def _company_drive_rows(company_id):
    drive_counts = (
        db.session.query(
            Application.drive_id,
            func.count(Application.application_id).label("applications_count"),
        )
        .group_by(Application.drive_id)
        .subquery()
    )

    return (
        db.session.query(
            PlacementDrive,
            func.coalesce(drive_counts.c.applications_count, 0),
        )
        .outerjoin(drive_counts, PlacementDrive.drive_id == drive_counts.c.drive_id)
        .filter(PlacementDrive.company_id == company_id)
        .order_by(PlacementDrive.created_at.desc(), PlacementDrive.drive_id.desc())
        .all()
    )


def _student_history_rows(student_id):
    history_rows = []
    for application, drive, company in _student_application_rows(student_id):
        offer = application.placement_offer
        placement = (
            Placement.query.filter_by(
                student_id=student_id,
                company_id=company.company_id if company else None,
                drive_id=drive.drive_id if drive else None,
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

        history_rows.append((application, drive, company, offer, placement, outcome))

    return history_rows


def _admin_company_rows():
    return (
        db.session.query(Company, User)
        .join(User, Company.user_id == User.user_id)
        .order_by(Company.created_at.desc(), Company.company_id.desc())
        .all()
    )


def _admin_student_rows():
    return (
        db.session.query(Student, User)
        .join(User, Student.user_id == User.user_id)
        .order_by(Student.created_at.desc(), Student.student_id.desc())
        .all()
    )


def _admin_drive_rows():
    drive_counts = (
        db.session.query(
            Application.drive_id,
            func.count(Application.application_id).label("applications_count"),
        )
        .group_by(Application.drive_id)
        .subquery()
    )

    return (
        db.session.query(
            PlacementDrive,
            Company,
            func.coalesce(drive_counts.c.applications_count, 0),
        )
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .outerjoin(drive_counts, PlacementDrive.drive_id == drive_counts.c.drive_id)
        .order_by(PlacementDrive.created_at.desc(), PlacementDrive.drive_id.desc())
        .all()
    )


def _admin_analytics_rows():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    total_placements = Placement.query.count()
    pending_companies = Company.query.filter_by(approval_status="pending").count()
    pending_drives = PlacementDrive.query.filter_by(status="pending").count()
    placed_students = (
        db.session.query(func.count(func.distinct(Placement.student_id))).scalar() or 0
    )

    return [
        ("Total Students", total_students),
        ("Total Companies", total_companies),
        ("Total Drives", total_drives),
        ("Total Applications", total_applications),
        ("Total Placements", total_placements),
        ("Placed Students", placed_students),
        ("Pending Company Approvals", pending_companies),
        ("Pending Drive Approvals", pending_drives),
    ]


def _admin_audit_rows():
    visible_log_filter = or_(
        ActivityLog.action.is_(None),
        ActivityLog.action.notin_(tuple(EXCLUDED_ADMIN_AUDIT_ACTIONS)),
    )

    return (
        db.session.query(ActivityLog, User)
        .join(User, ActivityLog.user_id == User.user_id)
        .filter(visible_log_filter)
        .order_by(ActivityLog.timestamp.desc(), ActivityLog.log_id.desc())
        .all()
    )


def _build_export_payload(job):
    payload = job.payload or {}
    export_scope = payload.get("export_scope")

    if export_scope == EXPORT_SCOPE_STUDENT_APPLICATIONS:
        student_id = int(payload.get("student_id"))
        student = db.session.get(Student, student_id)
        if not student:
            raise ValueError("Student profile not found")

        rows = _student_application_rows(student.student_id)
        return {
            "csv_content": _build_student_applications_csv(student.student_id, rows),
            "row_count": len(rows),
            "file_prefix": f"applications-export-student-{student.student_id}",
            "message": "Your applications export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_STUDENT_HISTORY:
        student_id = int(payload.get("student_id"))
        student = db.session.get(Student, student_id)
        if not student:
            raise ValueError("Student profile not found")

        rows = _student_history_rows(student.student_id)
        return {
            "csv_content": _build_student_history_csv(rows),
            "row_count": len(rows),
            "file_prefix": f"history-export-student-{student.student_id}",
            "message": "Your placement history export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_COMPANY_APPLICATIONS:
        company_id = int(payload.get("company_id"))
        company = db.session.get(Company, company_id)
        if not company:
            raise ValueError("Company profile not found")

        rows = _company_application_rows(company.company_id)
        return {
            "csv_content": _build_company_applications_csv(rows),
            "row_count": len(rows),
            "file_prefix": f"applications-export-company-{company.company_id}",
            "message": "Your company applications export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_COMPANY_PLACEMENTS:
        company_id = int(payload.get("company_id"))
        company = db.session.get(Company, company_id)
        if not company:
            raise ValueError("Company profile not found")

        rows = _company_placement_rows(company.company_id)
        return {
            "csv_content": _build_company_placements_csv(rows),
            "row_count": len(rows),
            "file_prefix": f"placements-export-company-{company.company_id}",
            "message": "Your company placements export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_COMPANY_DRIVES:
        company_id = int(payload.get("company_id"))
        company = db.session.get(Company, company_id)
        if not company:
            raise ValueError("Company profile not found")

        rows = _company_drive_rows(company.company_id)
        return {
            "csv_content": _build_company_drives_csv(rows),
            "row_count": len(rows),
            "file_prefix": f"drives-export-company-{company.company_id}",
            "message": "Your company drives export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_ADMIN_COMPANIES:
        rows = _admin_company_rows()
        return {
            "csv_content": _build_admin_companies_csv(rows),
            "row_count": len(rows),
            "file_prefix": "admin-export-companies",
            "message": "Your admin companies export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_ADMIN_STUDENTS:
        rows = _admin_student_rows()
        return {
            "csv_content": _build_admin_students_csv(rows),
            "row_count": len(rows),
            "file_prefix": "admin-export-students",
            "message": "Your admin students export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_ADMIN_DRIVES:
        rows = _admin_drive_rows()
        return {
            "csv_content": _build_admin_drives_csv(rows),
            "row_count": len(rows),
            "file_prefix": "admin-export-drives",
            "message": "Your admin drives export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_ADMIN_ANALYTICS:
        rows = _admin_analytics_rows()
        return {
            "csv_content": _build_admin_analytics_csv(rows),
            "row_count": len(rows),
            "file_prefix": "admin-export-analytics",
            "message": "Your admin analytics export is ready for download.",
            "scope": export_scope,
        }

    if export_scope == EXPORT_SCOPE_ADMIN_AUDIT:
        rows = _admin_audit_rows()
        return {
            "csv_content": _build_admin_audit_csv(rows),
            "row_count": len(rows),
            "file_prefix": "admin-export-audit",
            "message": "Your admin audit export is ready for download.",
            "scope": export_scope,
        }

    raise ValueError("Unsupported export scope")


def execute_export_job(job_id):
    """Generate CSV export for a queued job and persist delivery artifact metadata."""
    now_utc = _utcnow()
    job = db.session.get(BackgroundJob, job_id)
    if not job:
        return {"status": "failed", "error": "Job not found"}

    job.status = "running"
    job.started_at = now_utc
    job.error_message = None
    db.session.commit()

    try:
        export_payload = _build_export_payload(job)
        artifact_file = _write_export_artifact(
            export_payload["file_prefix"],
            export_payload["csv_content"],
            job_id=job.job_id,
        )

        ttl_hours = max(1, int(current_app.config.get("JOBS_EXPORT_ARTIFACT_TTL_HOURS", 24)))
        expires_at = _utcnow() + timedelta(hours=ttl_hours)

        artifact = ExportArtifact(
            job_id=job.job_id,
            requested_by_user_id=job.requested_by_user_id,
            filename=artifact_file["filename"],
            storage_path=artifact_file["path"],
            content_type="text/csv",
            file_size_bytes=artifact_file["size_bytes"],
            status="ready",
            checksum=artifact_file["checksum"],
            expires_at=expires_at,
        )
        db.session.add(artifact)
        db.session.flush()

        db.session.add(
            Notification(
                recipient_id=job.requested_by_user_id,
                notification_type="in_app",
                title="CSV Export Ready",
                message=export_payload["message"],
                related_resource_type="export_csv",
                related_resource_id=artifact.artifact_id,
                delivery_status="sent",
            )
        )

        job.status = "completed"
        job.finished_at = _utcnow()
        job.result_meta = {
            "rows_exported": export_payload["row_count"],
            "artifact_id": artifact.artifact_id,
            "filename": artifact.filename,
            "scope": export_payload["scope"],
            "expires_at": expires_at.isoformat(),
        }
        db.session.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "rows_exported": export_payload["row_count"],
            "artifact_id": artifact.artifact_id,
            "scope": export_payload["scope"],
        }
    except Exception as exc:
        db.session.rollback()

        failed_job = db.session.get(BackgroundJob, job.job_id)
        if failed_job:
            failed_job.status = "failed"
            failed_job.finished_at = _utcnow()
            failed_job.retry_count = int(failed_job.retry_count or 0) + 1
            failed_job.error_message = str(exc)[:1000]
            db.session.commit()

        return {
            "job_id": job.job_id,
            "status": "failed",
            "error": str(exc),
        }


def execute_student_applications_export(job_id):
    """Backward-compatible wrapper for the original student export task."""
    return execute_export_job(job_id)


def dispatch_export_job(job_id):
    """Dispatch an export job via Celery, or run inline for eager mode."""
    if current_app.config.get("JOBS_EAGER_EXECUTION"):
        return execute_export_job(job_id)

    celery_extension = current_app.extensions.get("celery")
    if celery_extension:
        celery_extension.send_task("jobs.export_applications_csv.run", args=[job_id])
        return {"job_id": job_id, "status": "queued"}

    return execute_export_job(job_id)
