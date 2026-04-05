"""Foundational Celery tasks used for queue and scheduler smoke checks."""

from datetime import datetime, timezone

from flask import current_app

from app.models import User, db

from .celery_app import celery
from .channels import parse_channels, send_channel_notification
from .exports import execute_student_applications_export
from .monthly_report import execute_monthly_activity_report
from .reminders import execute_daily_deadline_reminders, execute_daily_interview_reminders


def _utc_iso_now():
    return datetime.now(timezone.utc).isoformat()


def _retry_policy():
    retry_limit = max(0, int(current_app.config.get("JOBS_RETRY_LIMIT", 3)))
    backoff_seconds = max(1, int(current_app.config.get("JOBS_RETRY_BACKOFF_SECONDS", 60)))
    return retry_limit, backoff_seconds


def _notify_job_failure(task_name, error_message, context=None):
    channels = parse_channels(
        current_app.config.get("JOBS_FAILURE_ALERT_CHANNELS")
        or current_app.config.get("JOBS_REPORT_CHANNELS", "email")
    )
    webhook_url = current_app.config.get("JOBS_WEBHOOK_URL")
    failure_payload = {
        "event": "background_job_failed",
        "task": task_name,
        "error": error_message,
        **(context or {}),
    }

    admins = User.query.filter(User.role == "admin", User.is_active.is_(True)).all()
    if not admins:
        return

    try:
        for admin in admins:
            for channel in channels:
                send_channel_notification(
                    channel=channel,
                    recipient_id=admin.user_id,
                    title=f"Background Job Failed: {task_name}",
                    message=(
                        f"{task_name} failed after retry attempts were exhausted. "
                        f"Error: {error_message}"
                    ),
                    resource_type="job_failure",
                    resource_id=None,
                    webhook_url=webhook_url,
                    webhook_payload={
                        **failure_payload,
                        "admin_user_id": admin.user_id,
                    },
                )
        db.session.commit()
    except Exception:
        db.session.rollback()


def _retry_or_alert(task_instance, task_name, result, context=None):
    if result.get("status") != "failed":
        return result

    retry_limit, backoff_seconds = _retry_policy()
    retries_so_far = int(getattr(task_instance.request, "retries", 0))
    error_message = str(result.get("error") or f"{task_name} failed")

    if retries_so_far < retry_limit:
        countdown = backoff_seconds * (2**retries_so_far)
        raise task_instance.retry(
            exc=RuntimeError(error_message),
            countdown=countdown,
            max_retries=retry_limit,
        )

    _notify_job_failure(
        task_name,
        error_message,
        context={
            "attempts": retries_so_far + 1,
            **(context or {}),
        },
    )
    return result


@celery.task(name="jobs.foundation.heartbeat")
def foundation_heartbeat():
    """Simple heartbeat task to confirm worker execution."""
    return {
        "task": "jobs.foundation.heartbeat",
        "executed_at": _utc_iso_now(),
    }


@celery.task(bind=True, name="jobs.daily_reminders.run")
def run_daily_reminders(self):
    """Execute deadline reminder dispatch for eligible students."""
    result = execute_daily_deadline_reminders(task_request_id=getattr(self.request, "id", None))
    return _retry_or_alert(
        self,
        "jobs.daily_reminders.run",
        result,
        context={
            "task_id": getattr(self.request, "id", None),
            "job_id": result.get("job_id"),
        },
    )


@celery.task(bind=True, name="jobs.interview_reminders.run")
def run_interview_reminders(self):
    """Execute interview reminder dispatch for upcoming scheduled interviews."""
    result = execute_daily_interview_reminders(task_request_id=getattr(self.request, "id", None))
    return _retry_or_alert(
        self,
        "jobs.interview_reminders.run",
        result,
        context={
            "task_id": getattr(self.request, "id", None),
            "job_id": result.get("job_id"),
        },
    )


@celery.task(bind=True, name="jobs.monthly_report.run")
def run_monthly_report(self, task_request_id=None, audience=None, report_format=None):
    """Generate monthly HTML activity report for admins."""
    request_id = task_request_id or getattr(self.request, "id", None)
    result = execute_monthly_activity_report(
        task_request_id=request_id,
        audience=audience,
        report_format=report_format,
    )
    return _retry_or_alert(
        self,
        "jobs.monthly_report.run",
        result,
        context={
            "task_id": getattr(self.request, "id", None),
            "request_id": request_id,
            "job_id": result.get("job_id"),
            "audience": audience,
            "report_format": report_format,
        },
    )


@celery.task(bind=True, name="jobs.export_applications_csv.run")
def run_export_applications_csv(self, job_id):
    """Generate student applications CSV export for a queued job."""
    result = execute_student_applications_export(job_id)
    return _retry_or_alert(
        self,
        "jobs.export_applications_csv.run",
        result,
        context={
            "task_id": getattr(self.request, "id", None),
            "job_id": job_id,
        },
    )
