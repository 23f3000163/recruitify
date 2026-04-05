from datetime import datetime, timedelta, timezone

from app.jobs.reminders import execute_daily_deadline_reminders
from app.models import BackgroundJob, Company, Notification, PlacementDrive, Student, User, db


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
        cgpa=8.5,
        profile_completed=True,
        is_blacklisted=False,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Backend Engineer"):
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
        application_deadline=datetime.now(timezone.utc) + timedelta(days=1),
        interview_mode="online",
        status="approved",
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def test_daily_reminders_create_job_and_notifications(app):
    with app.app_context():
        app.config.update(
            JOBS_REMINDER_LOOKAHEAD_DAYS=2,
            JOBS_REMINDER_CHANNELS="email",
            JOBS_WEBHOOK_URL=None,
        )

        company_user = _make_user("company.reminder.1", "company.reminder.1@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Reminder Labs",
            "hr.reminder.1@example.com",
        )

        student_user = _make_user("student.reminder.1", "student.reminder.1@example.com", "student")
        _make_student_profile(student_user.user_id, "CS21R1001")

        drive = _make_drive(company.company_id, title="Reminder Engineer")
        db.session.commit()

        first_run = execute_daily_deadline_reminders(task_request_id="test-reminder-run")

        assert first_run["status"] == "completed"
        assert first_run["drives_considered"] == 1
        assert first_run["students_notified"] == 1
        assert first_run["sent"] == 1

        notifications = Notification.query.filter(
            Notification.recipient_id == student_user.user_id,
            Notification.notification_type == "email",
            Notification.related_resource_type == "deadline_reminder",
            Notification.related_resource_id == drive.drive_id,
        ).all()
        assert len(notifications) == 1

        run_key = f"daily-reminder:{datetime.now(timezone.utc).date().isoformat()}"
        tracked_job = BackgroundJob.query.filter_by(idempotency_key=run_key).first()
        assert tracked_job is not None
        assert tracked_job.status == "completed"

        second_run = execute_daily_deadline_reminders(task_request_id="test-reminder-run-repeat")
        assert second_run["skipped"] is True
        assert second_run["reason"] == "already-ran-today"
