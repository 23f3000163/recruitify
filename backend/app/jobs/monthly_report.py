"""Monthly activity report generation and delivery workflow."""

from datetime import datetime, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import func

from app.jobs.channels import parse_channels, send_channel_notification
from app.models import (
    Application,
    BackgroundJob,
    Company,
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


def _month_start(now_utc):
    return now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(month_start, delta_months):
    month_index = (month_start.month - 1) + int(delta_months)
    year = month_start.year + (month_index // 12)
    month = (month_index % 12) + 1
    return month_start.replace(year=year, month=month)


def _normalize_report_audience(raw_audience):
    value = str(raw_audience or "").strip().lower()
    if value in {"admin", "company", "both"}:
        return value
    return "admin"


def _normalize_report_format(raw_format):
    value = str(raw_format or "").strip().lower()
    if value in {"html", "pdf"}:
        return value
    return "html"


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


def _save_report_html(report_html, month_key, suffix):
    output_root = current_app.config.get("JOBS_REPORT_OUTPUT_DIR")
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"monthly-activity-report-{month_key}-{suffix}.html"
    report_path = output_path / filename
    report_path.write_text(report_html, encoding="utf-8")

    return {
        "filename": filename,
        "path": str(report_path),
        "size_bytes": report_path.stat().st_size,
        "format": "html",
    }


def _save_report_pdf(month_label, metrics, month_key, suffix):
    output_root = current_app.config.get("JOBS_REPORT_OUTPUT_DIR")
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"monthly-activity-report-{month_key}-{suffix}.pdf"
    report_path = output_path / filename

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError as exc:
        raise RuntimeError("reportlab is required for PDF report generation") from exc

    generated_at = _utcnow().strftime("%d %b %Y %H:%M UTC")
    lines = [
        "Monthly Placement Activity Report",
        f"Month: {month_label}",
        f"Generated at: {generated_at}",
        "",
        f"Drives Conducted: {metrics['drives_conducted']}",
        f"Students Applied: {metrics['students_applied']}",
        f"Students Selected: {metrics['students_selected']}",
        f"Total Applications: {metrics['total_applications']}",
        f"Offers Released: {metrics['offers_released']}",
        f"Placements Confirmed: {metrics['placements_confirmed']}",
    ]

    report_canvas = canvas.Canvas(str(report_path), pagesize=A4)
    width, height = A4

    y = height - 52
    report_canvas.setFont("Helvetica-Bold", 16)
    report_canvas.drawString(40, y, lines[0])

    y -= 26
    report_canvas.setFont("Helvetica", 11)
    for line in lines[1:]:
        report_canvas.drawString(40, y, line)
        y -= 16

    report_canvas.save()

    return {
        "filename": filename,
        "path": str(report_path),
        "size_bytes": report_path.stat().st_size,
        "format": "pdf",
    }


def _save_report(month_label, month_key, suffix, report_format, metrics):
    if report_format == "pdf":
        return _save_report_pdf(month_label, metrics, month_key, suffix)

    report_html = _render_monthly_report_html(month_label, metrics)
    return _save_report_html(report_html, month_key, suffix)


def _monthly_metrics(period_start, period_end, company_id=None):
    drives_query = db.session.query(func.count(PlacementDrive.drive_id)).filter(
        PlacementDrive.created_at >= period_start,
        PlacementDrive.created_at < period_end,
    )
    if company_id is not None:
        drives_query = drives_query.filter(PlacementDrive.company_id == company_id)

    students_applied_query = (
        db.session.query(func.count(func.distinct(Application.student_id)))
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .filter(
            Application.application_date >= period_start,
            Application.application_date < period_end,
        )
    )
    if company_id is not None:
        students_applied_query = students_applied_query.filter(PlacementDrive.company_id == company_id)

    students_selected_query = (
        db.session.query(func.count(func.distinct(Application.student_id)))
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .filter(
            Application.updated_at >= period_start,
            Application.updated_at < period_end,
            Application.status == "selected",
        )
    )
    if company_id is not None:
        students_selected_query = students_selected_query.filter(PlacementDrive.company_id == company_id)

    total_applications_query = (
        db.session.query(func.count(Application.application_id))
        .join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
        .filter(
            Application.application_date >= period_start,
            Application.application_date < period_end,
        )
    )
    if company_id is not None:
        total_applications_query = total_applications_query.filter(PlacementDrive.company_id == company_id)

    offers_query = db.session.query(func.count(PlacementOffer.offer_id)).filter(
        PlacementOffer.created_at >= period_start,
        PlacementOffer.created_at < period_end,
    )
    if company_id is not None:
        offers_query = offers_query.filter(PlacementOffer.company_id == company_id)

    placements_query = db.session.query(func.count(Placement.placement_id)).filter(
        Placement.created_at >= period_start,
        Placement.created_at < period_end,
    )
    if company_id is not None:
        placements_query = placements_query.filter(Placement.company_id == company_id)

    return {
        "drives_conducted": drives_query.scalar() or 0,
        "students_applied": students_applied_query.scalar() or 0,
        "students_selected": students_selected_query.scalar() or 0,
        "total_applications": total_applications_query.scalar() or 0,
        "offers_released": offers_query.scalar() or 0,
        "placements_confirmed": placements_query.scalar() or 0,
    }


def build_monthly_metrics_series(months=6, company_id=None, now_utc=None):
    """Build monthly metric rows for the previous complete months.

    The returned list is ordered oldest to newest and excludes the current
    in-progress month so trend charts always compare complete periods.
    """

    try:
        month_count = int(months)
    except (TypeError, ValueError):
        month_count = 6

    month_count = max(1, min(month_count, 24))

    anchor = _month_start(now_utc or _utcnow())
    rows = []
    for offset in range(month_count, 0, -1):
        period_start = _add_months(anchor, -offset)
        period_end = _add_months(period_start, 1)
        metrics = _monthly_metrics(period_start, period_end, company_id=company_id)
        rows.append(
            {
                "month_key": _month_key(period_start),
                "month_label": _month_label(period_start),
                **metrics,
            }
        )

    return rows


def _admin_recipients():
    users = User.query.filter(User.role == "admin", User.is_active.is_(True)).all()
    return [
        {
            "user_id": user.user_id,
            "audience": "admin",
            "company_id": None,
            "company_name": None,
            "label": "Admin",
        }
        for user in users
    ]


def _company_recipients():
    rows = (
        db.session.query(User.user_id, Company.company_id, Company.company_name)
        .join(Company, Company.user_id == User.user_id)
        .filter(
            User.role == "company",
            User.is_active.is_(True),
            Company.approval_status == "approved",
            Company.is_blacklisted.is_(False),
        )
        .all()
    )

    return [
        {
            "user_id": row.user_id,
            "audience": "company",
            "company_id": row.company_id,
            "company_name": row.company_name,
            "label": row.company_name,
        }
        for row in rows
    ]


def _target_recipients(audience_key):
    recipients = []
    if audience_key in {"admin", "both"}:
        recipients.extend(_admin_recipients())
    if audience_key in {"company", "both"}:
        recipients.extend(_company_recipients())

    deduped = []
    seen_user_ids = set()
    for recipient in recipients:
        user_id = recipient["user_id"]
        if user_id in seen_user_ids:
            continue
        seen_user_ids.add(user_id)
        deduped.append(recipient)
    return deduped


def execute_monthly_activity_report(task_request_id=None, audience=None, report_format=None):
    """Generate, persist, and deliver monthly report to admins and/or companies."""
    now_utc = _utcnow()
    period_start, period_end = _month_window(now_utc)
    month_key = _month_key(period_start)
    month_label = _month_label(period_start)

    audience_key = _normalize_report_audience(
        audience or current_app.config.get("JOBS_MONTHLY_REPORT_AUDIENCE", "admin")
    )
    report_format_key = _normalize_report_format(
        report_format or current_app.config.get("JOBS_MONTHLY_REPORT_FORMAT", "html")
    )

    run_key = f"monthly-report:{month_key}:{audience_key}:{report_format_key}"

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
            payload={
                "task_request_id": task_request_id,
                "audience": audience_key,
                "format": report_format_key,
            },
            started_at=now_utc,
        )
        db.session.add(job)
    else:
        job.status = "running"
        job.started_at = now_utc
        job.finished_at = None
        job.error_message = None
        job.payload = {
            "task_request_id": task_request_id,
            "audience": audience_key,
            "format": report_format_key,
        }

    db.session.commit()

    channels = parse_channels(current_app.config.get("JOBS_REPORT_CHANNELS", "email"))
    if "in_app" not in channels:
        channels = ["in_app", *channels]
    webhook_url = current_app.config.get("JOBS_WEBHOOK_URL")
    recipients = _target_recipients(audience_key)

    delivery = {
        "sent": 0,
        "failed": 0,
        "channels": {channel: 0 for channel in channels},
        "recipient_count": len(recipients),
    }
    metrics_cache = {}
    report_cache = {}

    try:
        for recipient in recipients:
            company_id = recipient.get("company_id")
            metrics_key = f"company:{company_id}" if company_id is not None else "global"
            metrics = metrics_cache.get(metrics_key)
            if metrics is None:
                metrics = _monthly_metrics(period_start, period_end, company_id=company_id)
                metrics_cache[metrics_key] = metrics

            report_suffix = "admin" if company_id is None else f"company-{company_id}"
            report_key = f"{report_suffix}:both"
            report_bundle = report_cache.get(report_key)
            if report_bundle is None:
                # report_file = _save_report(
                #     month_label,
                #     month_key,
                #     report_suffix,
                #     report_format_key,
                #     metrics,
                # )
                # Generate BOTH formats
                report_html = _save_report(
                    month_label,
                    month_key,
                    report_suffix,
                    "html",
                    metrics,
                )

                report_pdf = _save_report(
                    month_label,
                    month_key,
                    report_suffix,
                    "pdf",
                     metrics,
                    )
            
                report_cache[report_key] = {
                    "html": report_html,
                    "pdf": report_pdf,
                }

                report_bundle = report_cache[report_key]

            if recipient["audience"] == "company":
                title = f"Monthly Placement Report - {month_label}"
                message = (
                    f"Monthly placement report for {recipient['company_name']} is ready. "
                    f"Applications: {metrics['total_applications']}, "
                    f"Selected: {metrics['students_selected']}."
                )
            else:
                title = f"Monthly Activity Report - {month_label}"
                message = (
                    "Monthly report is generated. "
                    f"Drives: {metrics['drives_conducted']}, "
                    f"Applied: {metrics['students_applied']}, "
                    f"Selected: {metrics['students_selected']}."
                )

            for channel in channels:
                email_attachments = (
                    [
                        report_bundle["html"]["path"],
                        report_bundle["pdf"]["path"],
                    ]
                    if channel == "email"
                    else None
                )
                delivery_result = send_channel_notification(
                    channel=channel,
                    recipient_id=recipient["user_id"],
                    title=title,
                    message=message,
                    resource_type="monthly_report",
                    resource_id=None,
                    webhook_url=webhook_url,
                    email_attachments=email_attachments,
                    webhook_payload={
                        "event": "monthly_activity_report",
                        "month": month_key,
                        "recipient_user_id": recipient["user_id"],
                        "recipient_audience": recipient["audience"],
                        "company_id": company_id,
                        "company_name": recipient.get("company_name"),
                        "report_files": [
                            report_bundle["html"]["filename"],
                            report_bundle["pdf"]["filename"],
                        ],
                        "report_format": "html+pdf",
                        "metrics": metrics,
                    },
                )

                if delivery_result.get("status") == "sent":
                    delivery["sent"] += 1
                    delivery["channels"][channel] += 1
                else:
                    delivery["failed"] += 1

        primary_metrics = metrics_cache.get("global")
        if primary_metrics is None and metrics_cache:
            primary_metrics = next(iter(metrics_cache.values()))

        job.status = "completed"
        job.finished_at = _utcnow()
        job.result_meta = {
            "month_key": month_key,
            "month_label": month_label,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "audience": audience_key,
            "report_format": report_format_key,
            "metrics": primary_metrics,
            "delivery": delivery,
            "report": list(report_cache.values())[0] if report_cache else None,
            "reports": list(report_cache.values()),
            "metrics_by_scope": metrics_cache,
        }
        db.session.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "month": month_key,
            "audience": audience_key,
            "report_format": report_format_key,
            "metrics": primary_metrics,
            "delivery": delivery,
            "report": list(report_cache.values())[0] if report_cache else None,
            "reports": list(report_cache.values()),
            "metrics_by_scope": metrics_cache,
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

from app.jobs.celery_app import celery

@celery.task(name="jobs.monthly_report.run")
def run_monthly_report_task():
    return execute_monthly_activity_report()