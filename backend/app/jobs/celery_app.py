"""Celery application bootstrap for Recruitify background jobs."""

from celery import Celery, Task
from celery.schedules import crontab

celery = Celery("recruitify_jobs")


def _cron_to_schedule(raw_cron, fallback):
    """Convert five-part cron expression to Celery crontab schedule."""
    cron_expr = (raw_cron or fallback or "").strip()
    parts = cron_expr.split()
    if len(parts) != 5:
        parts = fallback.split()
    minute, hour, day_of_month, month_of_year, day_of_week = parts
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )


def init_celery(app):
    """Attach Flask app context and runtime config to the shared Celery app."""

    class FlaskContextTask(Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    daily_cron = app.config.get("JOBS_DAILY_REMINDER_CRON", "0 9 * * *")
    monthly_cron = app.config.get("JOBS_MONTHLY_REPORT_CRON", "0 9 1 * *")

    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND"),
        timezone=app.config.get("CELERY_TIMEZONE", "Asia/Kolkata"),
        enable_utc=True,
        task_track_started=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        imports=("app.jobs.tasks",),
        broker_connection_retry_on_startup=True,
        beat_schedule={
            "daily-reminder-placeholder": {
                "task": "jobs.daily_reminders.run",
                "schedule": _cron_to_schedule(daily_cron, "0 9 * * *"),
            },
            "monthly-report-placeholder": {
                "task": "jobs.monthly_report.run",
                "schedule": _cron_to_schedule(monthly_cron, "0 9 1 * *"),
            },
        },
    )

    celery.Task = FlaskContextTask
    app.extensions["celery"] = celery
    return celery
