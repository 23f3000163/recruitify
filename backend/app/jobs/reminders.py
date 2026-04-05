"""Daily reminder job implementation for upcoming placement deadlines."""

from datetime import datetime, timedelta, timezone

from flask import current_app

from app.jobs.channels import parse_channels, send_channel_notification
from app.models import (
    Application,
    BackgroundJob,
    Company,
    Notification,
    PlacementDrive,
    Student,
    User,
    db,
)


def _utcnow():
    return datetime.now(timezone.utc)


def _daily_job_key(now_utc):
    return f"daily-reminder:{now_utc.date().isoformat()}"


def _eligible_students_for_drive(drive):
    query = (
        db.session.query(Student, User)
        .join(User, Student.user_id == User.user_id)
        .filter(
            Student.profile_completed.is_(True),
            Student.is_blacklisted.is_(False),
            User.is_active.is_(True),
        )
    )

    eligible_branches = [
        str(branch or "").strip().upper()
        for branch in (drive.eligible_branches or [])
        if str(branch or "").strip()
    ]
    if eligible_branches:
        query = query.filter(Student.branch.in_(eligible_branches))

    eligible_years = []
    for year in drive.eligible_years or []:
        try:
            eligible_years.append(int(year))
        except (TypeError, ValueError):
            continue
    if eligible_years:
        query = query.filter(Student.year.in_(eligible_years))

    if drive.min_cgpa is not None:
        query = query.filter(Student.cgpa >= float(drive.min_cgpa))

    applied_student_ids = {
        row[0]
        for row in db.session.query(Application.student_id)
        .filter(Application.drive_id == drive.drive_id)
        .all()
    }

    candidates = []
    for student, user in query.all():
        if student.student_id in applied_student_ids:
            continue
        candidates.append((student, user))

    return candidates


def _already_sent_today(recipient_id, drive_id, channel, day_start, day_end):
    reminder = (
        Notification.query.filter(
            Notification.recipient_id == recipient_id,
            Notification.notification_type == channel,
            Notification.related_resource_type == "deadline_reminder",
            Notification.related_resource_id == drive_id,
            Notification.sent_at >= day_start,
            Notification.sent_at < day_end,
        )
        .order_by(Notification.notification_id.desc())
        .first()
    )
    return reminder is not None


def _channel_breakdown(channels):
    return {channel: {"sent": 0, "failed": 0} for channel in channels}


def execute_daily_deadline_reminders(task_request_id=None):
    """Run the daily reminder flow and persist a BackgroundJob run record."""
    now_utc = _utcnow()
    run_key = _daily_job_key(now_utc)

    job = BackgroundJob.query.filter_by(idempotency_key=run_key).first()
    if job and job.status in {"running", "completed"}:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "skipped": True,
            "reason": "already-ran-today",
        }

    if not job:
        job = BackgroundJob(
            job_type="daily_reminder",
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

    lookahead_days = max(1, int(current_app.config.get("JOBS_REMINDER_LOOKAHEAD_DAYS", 3)))
    channels = parse_channels(current_app.config.get("JOBS_REMINDER_CHANNELS", "email"))
    webhook_url = current_app.config.get("JOBS_WEBHOOK_URL")

    window_end = now_utc + timedelta(days=lookahead_days)
    day_start = datetime.combine(now_utc.date(), datetime.min.time(), tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    drives = (
        db.session.query(PlacementDrive)
        .join(Company, PlacementDrive.company_id == Company.company_id)
        .filter(
            PlacementDrive.status == "approved",
            Company.approval_status == "approved",
            Company.is_blacklisted.is_(False),
            PlacementDrive.application_deadline >= now_utc,
            PlacementDrive.application_deadline <= window_end,
        )
        .order_by(PlacementDrive.application_deadline.asc())
        .all()
    )

    metrics = {
        "drives_considered": len(drives),
        "students_notified": 0,
        "sent": 0,
        "failed": 0,
        "skipped_duplicates": 0,
        "channel_breakdown": _channel_breakdown(channels),
    }
    recipients_notified = set()

    try:
        for drive in drives:
            drive_deadline_text = drive.application_deadline.strftime("%d %b %Y %H:%M UTC")
            title = f"Deadline Reminder: {drive.job_title}"

            eligible_students = _eligible_students_for_drive(drive)
            for student, user in eligible_students:
                message = (
                    f"Your application window for {drive.job_title} at "
                    f"{drive.company.company_name if drive.company else 'the company'} "
                    f"closes on {drive_deadline_text}."
                )

                student_received_message = False
                for channel in channels:
                    if channel in {"email", "sms"} and _already_sent_today(
                        user.user_id,
                        drive.drive_id,
                        channel,
                        day_start,
                        day_end,
                    ):
                        metrics["skipped_duplicates"] += 1
                        continue

                    result = send_channel_notification(
                        channel=channel,
                        recipient_id=user.user_id,
                        title=title,
                        message=message,
                        resource_type="deadline_reminder",
                        resource_id=drive.drive_id,
                        webhook_url=webhook_url,
                        webhook_payload={
                            "event": "daily_deadline_reminder",
                            "student_id": student.student_id,
                            "user_id": user.user_id,
                            "drive_id": drive.drive_id,
                            "drive_title": drive.job_title,
                            "deadline": drive.application_deadline.isoformat(),
                        },
                    )

                    if result.get("status") == "sent":
                        metrics["sent"] += 1
                        metrics["channel_breakdown"][channel]["sent"] += 1
                        student_received_message = True
                    else:
                        metrics["failed"] += 1
                        metrics["channel_breakdown"][channel]["failed"] += 1

                if student_received_message:
                    recipients_notified.add(user.user_id)

        metrics["students_notified"] = len(recipients_notified)

        job.status = "completed"
        job.finished_at = _utcnow()
        job.result_meta = metrics
        db.session.commit()

        return {
            "job_id": job.job_id,
            "status": job.status,
            **metrics,
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
