"""Monthly admin activity report generation and delivery workflow."""

from datetime import datetime, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import func

from app.jobs.channels import parse_channels, send_channel_notification
from app.models import (
    Application,
    BackgroundJob,
    Placement,
    PlacementDrive,
    PlacementOffer,
    User,
    db,
)


def _utcnow():
    return datetime.now(timezone.utc)


def _month_window(now_utc):
    current_month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if current_month_start.month == 1:
        previous_month_start = current_month_start.replace(
            year=current_month_start.year - 1,
            month=12,
        )
    else:
        previous_month_start = current_month_start.replace(month=current_month_start.month - 1)
    return previous_month_start, current_month_start


def _month_label(month_start):
    return month_start.strftime("%B %Y")


def _month_key(month_start):
    return month_start.strftime("%Y-%m")


def _render_monthly_report_html(month_label, metrics):
    generated_at = _utcnow().strftime("%d %b %Y %H:%M UTC")

    return f"""<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>Recruitify Monthly Activity Report - {month_label}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 24px; color: #111827; }}
      h1 {{ margin: 0 0 8px; font-size: 24px; }}
      p.meta {{ margin: 0 0 20px; color: #6b7280; }}
      table {{ border-collapse: collapse; width: 100%; max-width: 700px; }}
      th, td {{ border: 1px solid #d1d5db; padding: 10px 12px; text-align: left; }}
      th {{ background: #f3f4f6; font-weight: 700; }}
      td.value {{ font-weight: 700; }}
    </style>
  </head>
  <body>
    <h1>Monthly Placement Activity Report</h1>
    <p class=\"meta\">Month: {month_label} | Generated at: {generated_at}</p>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Drives Conducted</td><td class=\"value\">{metrics["drives_conducted"]}</td></tr>
        <tr><td>Students Applied</td><td class=\"value\">{metrics["students_applied"]}</td></tr>
        <tr><td>Students Selected</td><td class=\"value\">{metrics["students_selected"]}</td></tr>
        <tr><td>Total Applications</td><td class=\"value\">{metrics["total_applications"]}</td></tr>
        <tr><td>Offers Released</td><td class=\"value\">{metrics["offers_released"]}</td></tr>
        <tr><td>Placements Confirmed</td><td class=\"value\">{metrics["placements_confirmed"]}</td></tr>
      </tbody>
    </table>
  </body>
</html>
"""


def _save_report(report_html, month_key):
    output_root = current_app.config.get("JOBS_REPORT_OUTPUT_DIR")
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"monthly-activity-report-{month_key}.html"
    report_path = output_path / filename
    report_path.write_text(report_html, encoding="utf-8")

    return {
        "filename": filename,
        "path": str(report_path),
        "size_bytes": report_path.stat().st_size,
    }


def _monthly_metrics(period_start, period_end):
    return {
        "drives_conducted": (
            db.session.query(func.count(PlacementDrive.drive_id))
            .filter(
                PlacementDrive.created_at >= period_start,
                PlacementDrive.created_at < period_end,
            )
            .scalar()
            or 0
        ),
        "students_applied": (
            db.session.query(func.count(func.distinct(Application.student_id)))
            .filter(
                Application.application_date >= period_start,
                Application.application_date < period_end,
            )
            .scalar()
            or 0
        ),
        "students_selected": (
            db.session.query(func.count(func.distinct(Application.student_id)))
            .filter(
                Application.updated_at >= period_start,
                Application.updated_at < period_end,
                Application.status == "selected",
            )
            .scalar()
            or 0
        ),
        "total_applications": (
            db.session.query(func.count(Application.application_id))
            .filter(
                Application.application_date >= period_start,
                Application.application_date < period_end,
            )
            .scalar()
            or 0
        ),
        "offers_released": (
            db.session.query(func.count(PlacementOffer.offer_id))
            .filter(
                PlacementOffer.created_at >= period_start,
                PlacementOffer.created_at < period_end,
            )
            .scalar()
            or 0
        ),
        "placements_confirmed": (
            db.session.query(func.count(Placement.placement_id))
            .filter(
                Placement.created_at >= period_start,
                Placement.created_at < period_end,
            )
            .scalar()
            or 0
        ),
    }


def execute_monthly_activity_report(task_request_id=None):
    """Generate, persist, and deliver monthly admin report."""
    now_utc = _utcnow()
    period_start, period_end = _month_window(now_utc)
    month_key = _month_key(period_start)
    month_label = _month_label(period_start)
    run_key = f"monthly-report:{month_key}"

    job = BackgroundJob.query.filter_by(idempotency_key=run_key).first()
    if job and job.status in {"running", "completed"}:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "skipped": True,
            "reason": "already-ran-this-month",
        }

    if not job:
        job = BackgroundJob(
            job_type="monthly_report",
            status="running",
            idempotency_key=run_key,
            payload={"task_request_id": task_request_id},
            started_at=now_utc,
        )
        db.session.add(job)
    else:
        job.status = "running"
        job.started_at = now_utc
        job.finished_at = None
        job.error_message = None
        job.payload = {"task_request_id": task_request_id}

    db.session.commit()

    channels = parse_channels(current_app.config.get("JOBS_REPORT_CHANNELS", "email"))
    webhook_url = current_app.config.get("JOBS_WEBHOOK_URL")

    metrics = _monthly_metrics(period_start, period_end)
    report_html = _render_monthly_report_html(month_label, metrics)
    report_file = _save_report(report_html, month_key)

    admins = User.query.filter(User.role == "admin", User.is_active.is_(True)).all()
    delivery = {"sent": 0, "failed": 0, "channels": {channel: 0 for channel in channels}}

    try:
        for admin in admins:
            for channel in channels:
                delivery_result = send_channel_notification(
                    channel=channel,
                    recipient_id=admin.user_id,
                    title=f"Monthly Activity Report - {month_label}",
                    message=(
                        "Monthly report is generated. "
                        f"Drives: {metrics['drives_conducted']}, "
                        f"Applied: {metrics['students_applied']}, "
                        f"Selected: {metrics['students_selected']}."
                    ),
                    resource_type="monthly_report",
                    resource_id=None,
                    webhook_url=webhook_url,
                    webhook_payload={
                        "event": "monthly_activity_report",
                        "month": month_key,
                        "admin_user_id": admin.user_id,
                        "report_file": report_file["filename"],
                        "metrics": metrics,
                    },
                )

                if delivery_result.get("status") == "sent":
                    delivery["sent"] += 1
                    delivery["channels"][channel] += 1
                else:
                    delivery["failed"] += 1

        job.status = "completed"
        job.finished_at = _utcnow()
        job.result_meta = {
            "month_key": month_key,
            "month_label": month_label,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "metrics": metrics,
            "delivery": delivery,
            "report": report_file,
        }
        db.session.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "month": month_key,
            "metrics": metrics,
            "delivery": delivery,
            "report": report_file,
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
