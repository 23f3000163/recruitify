"""Asynchronous CSV export workflow for student and company history."""

import csv
import hashlib
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

from flask import current_app

from app.models import (
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
EXPORT_SCOPE_COMPANY_APPLICATIONS = "company_applications"
EXPORT_SCOPE_COMPANY_PLACEMENTS = "company_placements"


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


def create_student_export_job(user_id):
    """Create a new student applications export job unless one is already active."""
    student = _student_for_user(user_id)
    if not student:
        return None, "Student profile not found", None

    export_scope = EXPORT_SCOPE_STUDENT_APPLICATIONS
    active_job = _active_export_job_for_user(user_id, export_scope)
    if active_job:
        return active_job, None, True

    now_utc = _utcnow()
    job = BackgroundJob(
        job_type="export_csv",
        status="queued",
        requested_by_user_id=user_id,
        idempotency_key=f"export:student:{student.student_id}:{now_utc.strftime('%Y%m%d%H%M%S')}",
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
    if export_scope not in {EXPORT_SCOPE_COMPANY_APPLICATIONS, EXPORT_SCOPE_COMPANY_PLACEMENTS}:
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


def _write_export_artifact(file_prefix, csv_content):
    output_dir = Path(current_app.config.get("JOBS_EXPORT_OUTPUT_DIR"))
    output_dir.mkdir(parents=True, exist_ok=True)

    now_utc = _utcnow()
    filename = f"{file_prefix}-{now_utc.strftime('%Y%m%d%H%M%S')}.csv"
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
