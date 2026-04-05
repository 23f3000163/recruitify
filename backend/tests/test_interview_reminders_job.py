from datetime import datetime, timedelta, timezone

from app.jobs.reminders import execute_daily_interview_reminders
from app.models import (
    Application,
    BackgroundJob,
    Company,
    Interview,
    Notification,
    PlacementDrive,
    Student,
    User,
    db,
)


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password("Password@123")
    db.session.add(user)
    db.session.flush()
    return user


def _make_company_profile(user_id, name, hr_email):
    company = Company(
        user_id=user_id,
        company_name=name,
        industry="Software",
        hr_contact_name="Hiring Lead",
        hr_contact_email=hr_email,
        hr_contact_phone="9999999999",
        approval_status="approved",
    )
    db.session.add(company)
    db.session.flush()
    return company


def _make_student_profile(user_id, roll_number):
    student = Student(
        user_id=user_id,
        roll_number=roll_number,
        branch="CSE",
        year=4,
        cgpa=8.7,
        profile_completed=True,
        is_blacklisted=False,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Interview Reminder Engineer"):
    drive = PlacementDrive(
        company_id=company_id,
        job_title=title,
        job_description="Core job responsibilities",
        required_skills="Python,SQL",
        experience_required="0-2 years",
        benefits="Health insurance",
        min_cgpa=6.0,
        eligible_branches=["CSE", "ECE"],
        eligible_years=[3, 4],
        salary_lpa=14.0,
        job_location="Remote",
        application_deadline=datetime.now(timezone.utc) + timedelta(days=5),
        interview_mode="online",
        status="approved",
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def test_interview_reminders_create_notification_and_job(app):
    with app.app_context():
        app.config.update(
            JOBS_INTERVIEW_REMINDER_ENABLED=True,
            JOBS_INTERVIEW_REMINDER_WINDOW_HOURS=24,
            JOBS_INTERVIEW_REMINDER_CHANNELS="email",
            JOBS_WEBHOOK_URL=None,
        )

        company_user = _make_user(
            "company.interview.reminder.1",
            "company.interview.reminder.1@example.com",
            "company",
        )
        company = _make_company_profile(
            company_user.user_id,
            "Interview Reminder Labs",
            "hr.interview.reminder.1@example.com",
        )

        student_user = _make_user(
            "student.interview.reminder.1",
            "student.interview.reminder.1@example.com",
            "student",
        )
        student = _make_student_profile(student_user.user_id, "CS21IR1001")

        drive = _make_drive(company.company_id)
        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="shortlisted",
        )
        db.session.add(application)
        db.session.flush()

        interview = Interview(
            application_id=application.application_id,
            company_id=company.company_id,
            drive_id=drive.drive_id,
            interview_date=datetime.now(timezone.utc) + timedelta(hours=3),
            interview_mode="online",
            interview_link="https://example.com/interview-room",
            result="pending",
        )
        db.session.add(interview)
        db.session.commit()

        first_run = execute_daily_interview_reminders(task_request_id="test-interview-reminder-run")

        assert first_run["status"] == "completed"
        assert first_run["interviews_considered"] == 1
        assert first_run["students_notified"] == 1
        assert first_run["sent"] == 1

        notifications = Notification.query.filter(
            Notification.recipient_id == student_user.user_id,
            Notification.notification_type == "email",
            Notification.related_resource_type == "interview_reminder",
            Notification.related_resource_id == interview.interview_id,
        ).all()
        assert len(notifications) == 1

        run_key = f"interview-reminder:{datetime.now(timezone.utc).date().isoformat()}"
        tracked_job = BackgroundJob.query.filter_by(idempotency_key=run_key).first()
        assert tracked_job is not None
        assert tracked_job.status == "completed"

        second_run = execute_daily_interview_reminders(task_request_id="test-interview-reminder-run-repeat")
        assert second_run["skipped"] is True
        assert second_run["reason"] == "already-ran-today"


def test_interview_reminders_skip_when_disabled(app):
    with app.app_context():
        app.config.update(
            JOBS_INTERVIEW_REMINDER_ENABLED=False,
            JOBS_INTERVIEW_REMINDER_WINDOW_HOURS=24,
            JOBS_INTERVIEW_REMINDER_CHANNELS="email",
        )

        result = execute_daily_interview_reminders(task_request_id="disabled-interview-reminder")
        assert result["status"] == "skipped"
        assert result["reason"] == "interview-reminders-disabled"
