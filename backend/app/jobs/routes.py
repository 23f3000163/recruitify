"""Routes for background jobs health and operational checks."""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity

from app.auth.utils import role_required
from app.jobs.exports import (
    EXPORT_SCOPE_COMPANY_APPLICATIONS,
    EXPORT_SCOPE_COMPANY_PLACEMENTS,
    create_company_export_job,
    create_student_export_job,
    dispatch_export_job,
)
from app.jobs.monthly_report import execute_monthly_activity_report
from app.models import BackgroundJob, Company, ExportArtifact, Student, db

jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs")


def _sanitize_broker_url(raw_url):
    """Return a safe-to-display broker URL without credentials."""
    if not raw_url:
        return None

    parsed = urlparse(raw_url)
    host = parsed.hostname or "localhost"
    port = f":{parsed.port}" if parsed.port else ""
    db_path = parsed.path or ""
    return f"{parsed.scheme}://{host}{port}{db_path}"


def _redis_ping(redis_url):
    """Ping Redis using a short timeout to avoid blocking health requests."""
    if not redis_url:
        return {"reachable": False, "message": "Redis URL not configured"}

    try:
        import redis
    except ModuleNotFoundError:
        return {"reachable": False, "message": "redis package not installed"}

    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        client.ping()
        return {"reachable": True, "message": "ok"}
    except Exception as exc:
        return {"reachable": False, "message": str(exc)}


def _current_user_id():
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def _latest_export_artifact(job_id):
    return (
        ExportArtifact.query.filter(ExportArtifact.job_id == job_id)
        .order_by(ExportArtifact.created_at.desc(), ExportArtifact.artifact_id.desc())
        .first()
    )


def _job_for_user(job_id, user_id):
    return BackgroundJob.query.filter(
        BackgroundJob.job_id == job_id,
        BackgroundJob.requested_by_user_id == user_id,
    ).first()


def _company_for_user(user_id):
    return Company.query.filter_by(user_id=user_id).first()


def _job_matches_owner(job, owner_key):
    payload = (job.payload or {}) if job else {}
    return payload.get("export_owner") == owner_key


def _expire_if_needed(artifact):
    if not artifact or not artifact.expires_at:
        return False

    expires_at = artifact.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = expires_at.astimezone(timezone.utc)

    if artifact.status == "ready" and expires_at <= datetime.now(timezone.utc):
        artifact.status = "expired"
        db.session.commit()
        return True
    return False


@jobs_bp.get("/health")
def jobs_health_check():
    """Return the queue/scheduler readiness for background jobs."""
    broker_url = current_app.config.get("CELERY_BROKER_URL")
    backend_url = current_app.config.get("CELERY_RESULT_BACKEND")
    celery_extension = current_app.extensions.get("celery")

    broker_health = _redis_ping(broker_url)
    backend_health = _redis_ping(backend_url)

    status = "ok"
    if not celery_extension or not broker_health["reachable"] or not backend_health["reachable"]:
        status = "degraded"

    payload = {
        "success": True,
        "data": {
            "status": status,
            "celery_initialized": bool(celery_extension),
            "broker": {
                "url": _sanitize_broker_url(broker_url),
                **broker_health,
            },
            "result_backend": {
                "url": _sanitize_broker_url(backend_url),
                **backend_health,
            },
            "schedules": {
                "daily_reminder": current_app.config.get("JOBS_DAILY_REMINDER_CRON"),
                "interview_reminder": current_app.config.get("JOBS_INTERVIEW_REMINDER_CRON"),
                "monthly_report": current_app.config.get("JOBS_MONTHLY_REPORT_CRON"),
            },
            "reminders": {
                "lookahead_days": current_app.config.get("JOBS_REMINDER_LOOKAHEAD_DAYS"),
                "channels": current_app.config.get("JOBS_REMINDER_CHANNELS"),
                "interview_enabled": current_app.config.get("JOBS_INTERVIEW_REMINDER_ENABLED"),
                "interview_window_hours": current_app.config.get("JOBS_INTERVIEW_REMINDER_WINDOW_HOURS"),
                "interview_channels": current_app.config.get("JOBS_INTERVIEW_REMINDER_CHANNELS"),
            },
            "reports": {
                "audience": current_app.config.get("JOBS_MONTHLY_REPORT_AUDIENCE"),
                "format": current_app.config.get("JOBS_MONTHLY_REPORT_FORMAT"),
            },
            "exports": {
                "company_enabled": current_app.config.get("JOBS_COMPANY_EXPORT_ENABLED"),
                "placement_history_enabled": current_app.config.get(
                    "JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY"
                ),
            },
        },
    }
    return jsonify(payload), 200


@jobs_bp.post("/reports/monthly/run")
@role_required("admin")
def trigger_monthly_report_run():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    audience = (request.args.get("audience") or "").strip().lower() or None
    if audience and audience not in {"admin", "company", "both"}:
        return jsonify({"success": False, "error": "audience must be admin, company, or both"}), 400

    report_format = (request.args.get("format") or "").strip().lower() or None
    if report_format and report_format not in {"html", "pdf"}:
        return jsonify({"success": False, "error": "format must be html or pdf"}), 400

    task_request_id = f"admin:{user_id}:{datetime.now(timezone.utc).isoformat()}"
    if current_app.config.get("JOBS_EAGER_EXECUTION"):
        result = execute_monthly_activity_report(
            task_request_id=task_request_id,
            audience=audience,
            report_format=report_format,
        )
        return jsonify({"success": True, "data": result}), 200

    celery_extension = current_app.extensions.get("celery")
    if celery_extension:
        celery_extension.send_task(
            "jobs.monthly_report.run",
            kwargs={
                "task_request_id": task_request_id,
                "audience": audience,
                "report_format": report_format,
            },
        )
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "status": "queued",
                        "message": "Monthly report job queued",
                    },
                }
            ),
            202,
        )

    result = execute_monthly_activity_report(
        task_request_id=task_request_id,
        audience=audience,
        report_format=report_format,
    )
    return jsonify({"success": True, "data": result}), 200


@jobs_bp.post("/reports/monthly/company/run")
@role_required("company")
def trigger_company_monthly_report_run():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    company = _company_for_user(user_id)
    if not company:
        return jsonify({"success": False, "error": "Company profile not found"}), 404

    if company.approval_status != "approved" or company.is_blacklisted:
        return jsonify({"success": False, "error": "Company is not allowed to run reports"}), 403

    report_format = (request.args.get("format") or "").strip().lower() or None
    if report_format and report_format not in {"html", "pdf"}:
        return jsonify({"success": False, "error": "format must be html or pdf"}), 400

    task_request_id = f"company:{company.company_id}:{datetime.now(timezone.utc).isoformat()}"

    if current_app.config.get("JOBS_EAGER_EXECUTION"):
        result = execute_monthly_activity_report(
            task_request_id=task_request_id,
            audience="company",
            report_format=report_format,
        )
        return jsonify({"success": True, "data": result}), 200

    celery_extension = current_app.extensions.get("celery")
    if celery_extension:
        celery_extension.send_task(
            "jobs.monthly_report.run",
            kwargs={
                "task_request_id": task_request_id,
                "audience": "company",
                "report_format": report_format,
            },
        )
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "status": "queued",
                        "message": "Company monthly report job queued",
                    },
                }
            ),
            202,
        )

    result = execute_monthly_activity_report(
        task_request_id=task_request_id,
        audience="company",
        report_format=report_format,
    )
    return jsonify({"success": True, "data": result}), 200


@jobs_bp.post("/exports/applications")
@role_required("student")
def trigger_applications_export():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"success": False, "error": "Student profile not found"}), 404

    job, error_message, reused_existing = create_student_export_job(user_id)
    if error_message:
        return jsonify({"success": False, "error": error_message}), 400

    dispatch_result = {"status": job.status}
    if not reused_existing:
        dispatch_result = dispatch_export_job(job.job_id)

    latest_job = db.session.get(BackgroundJob, job.job_id)
    payload = {
        "job_id": job.job_id,
        "status": latest_job.status if latest_job else job.status,
        "requested_by_user_id": user_id,
        "dispatched": dispatch_result.get("status") in {"queued", "running", "completed"},
        "active_job_reused": bool(reused_existing),
    }
    status_code = 200 if payload["active_job_reused"] else 202
    return jsonify({"success": True, "data": payload}), status_code


@jobs_bp.get("/exports/<string:job_id>")
@role_required("student")
def get_export_status(job_id):
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    job = _job_for_user(job_id, user_id)
    if not job or not _job_matches_owner(job, "student"):
        return jsonify({"success": False, "error": "Export job not found"}), 404

    artifact = _latest_export_artifact(job.job_id)
    if artifact:
        _expire_if_needed(artifact)

    payload = {
        "job": job.to_dict(),
        "artifact": artifact.to_dict() if artifact else None,
    }
    return jsonify({"success": True, "data": payload}), 200


@jobs_bp.get("/exports/<string:job_id>/download")
@role_required("student")
def download_export_artifact(job_id):
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    job = _job_for_user(job_id, user_id)
    if not job or not _job_matches_owner(job, "student"):
        return jsonify({"success": False, "error": "Export job not found"}), 404

    artifact = _latest_export_artifact(job.job_id)
    if not artifact:
        return jsonify({"success": False, "error": "Export artifact not ready"}), 404

    if _expire_if_needed(artifact) or artifact.status == "expired":
        return jsonify({"success": False, "error": "Export artifact has expired"}), 410

    if artifact.status != "ready":
        return jsonify({"success": False, "error": "Export artifact not ready"}), 409

    if not Path(artifact.storage_path).exists():
        artifact.status = "failed"
        db.session.commit()
        return jsonify({"success": False, "error": "Export artifact is unavailable"}), 410

    return send_file(
        artifact.storage_path,
        mimetype=artifact.content_type or "text/csv",
        as_attachment=True,
        download_name=artifact.filename,
    )


@jobs_bp.post("/exports/company/applications")
@role_required("company")
def trigger_company_applications_export():
    if not current_app.config.get("JOBS_COMPANY_EXPORT_ENABLED", False):
        return jsonify({"success": False, "error": "Company export feature is disabled"}), 403

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    company = _company_for_user(user_id)
    if not company:
        return jsonify({"success": False, "error": "Company profile not found"}), 404

    job, error_message, reused_existing = create_company_export_job(
        user_id,
        EXPORT_SCOPE_COMPANY_APPLICATIONS,
    )
    if error_message:
        return jsonify({"success": False, "error": error_message}), 400

    dispatch_result = {"status": job.status}
    if not reused_existing:
        dispatch_result = dispatch_export_job(job.job_id)

    latest_job = db.session.get(BackgroundJob, job.job_id)
    payload = {
        "job_id": job.job_id,
        "status": latest_job.status if latest_job else job.status,
        "requested_by_user_id": user_id,
        "dispatched": dispatch_result.get("status") in {"queued", "running", "completed"},
        "active_job_reused": bool(reused_existing),
    }
    status_code = 200 if payload["active_job_reused"] else 202
    return jsonify({"success": True, "data": payload}), status_code


@jobs_bp.post("/exports/company/placements")
@role_required("company")
def trigger_company_placements_export():
    if not current_app.config.get("JOBS_COMPANY_EXPORT_ENABLED", False):
        return jsonify({"success": False, "error": "Company export feature is disabled"}), 403
    if not current_app.config.get("JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY", False):
        return jsonify({"success": False, "error": "Placement history export is disabled"}), 403

    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    company = _company_for_user(user_id)
    if not company:
        return jsonify({"success": False, "error": "Company profile not found"}), 404

    job, error_message, reused_existing = create_company_export_job(
        user_id,
        EXPORT_SCOPE_COMPANY_PLACEMENTS,
    )
    if error_message:
        return jsonify({"success": False, "error": error_message}), 400

    dispatch_result = {"status": job.status}
    if not reused_existing:
        dispatch_result = dispatch_export_job(job.job_id)

    latest_job = db.session.get(BackgroundJob, job.job_id)
    payload = {
        "job_id": job.job_id,
        "status": latest_job.status if latest_job else job.status,
        "requested_by_user_id": user_id,
        "dispatched": dispatch_result.get("status") in {"queued", "running", "completed"},
        "active_job_reused": bool(reused_existing),
    }
    status_code = 200 if payload["active_job_reused"] else 202
    return jsonify({"success": True, "data": payload}), status_code


@jobs_bp.get("/exports/company/<string:job_id>")
@role_required("company")
def get_company_export_status(job_id):
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    job = _job_for_user(job_id, user_id)
    if not job or not _job_matches_owner(job, "company"):
        return jsonify({"success": False, "error": "Export job not found"}), 404

    artifact = _latest_export_artifact(job.job_id)
    if artifact:
        _expire_if_needed(artifact)

    payload = {
        "job": job.to_dict(),
        "artifact": artifact.to_dict() if artifact else None,
    }
    return jsonify({"success": True, "data": payload}), 200


@jobs_bp.get("/exports/company/<string:job_id>/download")
@role_required("company")
def download_company_export_artifact(job_id):
    user_id = _current_user_id()
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid token identity"}), 401

    job = _job_for_user(job_id, user_id)
    if not job or not _job_matches_owner(job, "company"):
        return jsonify({"success": False, "error": "Export job not found"}), 404

    artifact = _latest_export_artifact(job.job_id)
    if not artifact:
        return jsonify({"success": False, "error": "Export artifact not ready"}), 404

    if _expire_if_needed(artifact) or artifact.status == "expired":
        return jsonify({"success": False, "error": "Export artifact has expired"}), 410

    if artifact.status != "ready":
        return jsonify({"success": False, "error": "Export artifact not ready"}), 409

    if not Path(artifact.storage_path).exists():
        artifact.status = "failed"
        db.session.commit()
        return jsonify({"success": False, "error": "Export artifact is unavailable"}), 410

    return send_file(
        artifact.storage_path,
        mimetype=artifact.content_type or "text/csv",
        as_attachment=True,
        download_name=artifact.filename,
    )
