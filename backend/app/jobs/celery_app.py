"""Celery application bootstrap for Recruitify background jobs."""
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present
from celery import Celery, Task
from celery.schedules import crontab

celery = Celery("recruitify_jobs")

celery.conf.update(
    imports=(
        "app.jobs.tasks",
        "app.jobs.monthly_report",
        "app.jobs.reminders",
    )
)

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
    interview_cron = app.config.get("JOBS_INTERVIEW_REMINDER_CRON", "30 9 * * *")
    monthly_cron = app.config.get("JOBS_MONTHLY_REPORT_CRON", "0 9 1 * *")

    celery.conf.update(
        broker_url=os.getenv("CELERY_BROKER_URL"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND"),
        timezone=app.config.get("CELERY_TIMEZONE", "Asia/Kolkata"),
        enable_utc=True,
        task_track_started=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        broker_connection_retry_on_startup=True,
        beat_schedule={
            # DAILY MODE (default): keep enabled in normal/production runs.
            "daily-reminder-placeholder": {
                "task": "jobs.daily_reminders.run",
                "schedule": _cron_to_schedule(daily_cron, "0 9 * * *"),
            },
           
            # DEMO MODE (USE FOR VIVA ONLY) runs every 2 minutes.
            # "demo-daily-reminder-2min": {
            #     "task": "jobs.daily_reminders.run",
            #     "schedule": 120.0,
            # },
            
            "interview-reminder-placeholder": {
                "task": "jobs.interview_reminders.run",
                "schedule": _cron_to_schedule(interview_cron, "30 9 * * *"),
            },
            "monthly-report-placeholder": {
                "task": "jobs.monthly_report.run",
                "schedule": _cron_to_schedule(monthly_cron, "0 9 1 * *"),
            },

            # DEMO MODE (USE FOR VIVA ONLY) runs every 2 minutes.
            # "demo-monthly-report-2min": {
            #     "task": "jobs.monthly_report.run",
            #     "schedule": 120.0,
            # },
        },
    )

    celery.Task = FlaskContextTask
    app.extensions["celery"] = celery
    return celery

