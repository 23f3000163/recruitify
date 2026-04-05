"""Asynchronous CSV export workflow for student application history."""

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
    PlacementDrive,
    Student,
    db,
)


ACTIVE_JOB_STATUSES = {"queued", "running"}


def _utcnow():
    return datetime.now(timezone.utc)


def _student_for_user(user_id):
    return Student.query.filter_by(user_id=user_id).first()


def create_student_export_job(user_id):
    """Create a new export job unless one is already active for the user."""
    student = _student_for_user(user_id)
    if not student:
        return None, "Student profile not found", None

    active_job = (
        BackgroundJob.query.filter(
            BackgroundJob.job_type == "export_csv",
            BackgroundJob.requested_by_user_id == user_id,
            BackgroundJob.status.in_(tuple(ACTIVE_JOB_STATUSES)),
        )
        .order_by(BackgroundJob.created_at.desc())
        .first()
    )
    if active_job:
        return active_job, None, True

    now_utc = _utcnow()
    job = BackgroundJob(
        job_type="export_csv",
        status="queued",
        requested_by_user_id=user_id,
        idempotency_key=f"export:{student.student_id}:{now_utc.strftime('%Y%m%d%H%M%S')}",
        payload={
            "student_id": student.student_id,
            "requested_at": now_utc.isoformat(),
        },
    )
    db.session.add(job)
    db.session.commit()

    return job, None, False


def _build_csv_content(student_id, rows):
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


def _write_export_artifact(student_id, csv_content):
    output_dir = Path(current_app.config.get("JOBS_EXPORT_OUTPUT_DIR"))
    output_dir.mkdir(parents=True, exist_ok=True)

    now_utc = _utcnow()
    filename = f"applications-export-student-{student_id}-{now_utc.strftime('%Y%m%d%H%M%S')}.csv"
    output_file = output_dir / filename
    output_file.write_text(csv_content, encoding="utf-8")

    return {
        "filename": filename,
        "path": str(output_file),
        "size_bytes": output_file.stat().st_size,
        "checksum": hashlib.sha256(csv_content.encode("utf-8")).hexdigest(),
    }


def execute_student_applications_export(job_id):
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
        student_id = int((job.payload or {}).get("student_id"))
        student = db.session.get(Student, student_id)
        if not student:
            raise ValueError("Student profile not found")

        rows = (
            db.session.query(Application, PlacementDrive, Company)
            .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
            .join(Company, PlacementDrive.company_id == Company.company_id)
            .filter(Application.student_id == student.student_id)
            .order_by(Application.updated_at.desc(), Application.application_id.desc())
            .all()
        )

        csv_content = _build_csv_content(student.student_id, rows)
        artifact_file = _write_export_artifact(student.student_id, csv_content)

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
                message="Your applications export is ready for download.",
                related_resource_type="export_csv",
                related_resource_id=artifact.artifact_id,
                delivery_status="sent",
            )
        )

        job.status = "completed"
        job.finished_at = _utcnow()
        job.result_meta = {
            "rows_exported": len(rows),
            "artifact_id": artifact.artifact_id,
            "filename": artifact.filename,
            "expires_at": expires_at.isoformat(),
        }
        db.session.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "rows_exported": len(rows),
            "artifact_id": artifact.artifact_id,
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


def dispatch_export_job(job_id):
    """Dispatch an export job via Celery, or run inline for eager mode."""
    if current_app.config.get("JOBS_EAGER_EXECUTION"):
        return execute_student_applications_export(job_id)

    celery_extension = current_app.extensions.get("celery")
    if celery_extension:
        celery_extension.send_task("jobs.export_applications_csv.run", args=[job_id])
        return {"job_id": job_id, "status": "queued"}

    return execute_student_applications_export(job_id)
