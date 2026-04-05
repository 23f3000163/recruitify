from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask_jwt_extended import create_access_token

from app.jobs.monthly_report import execute_monthly_activity_report
from app.models import (
    Application,
    Company,
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
        cgpa=8.4,
        profile_completed=True,
        is_blacklisted=False,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Monthly Report Engineer"):
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
        application_deadline=datetime.now(timezone.utc) + timedelta(days=7),
        interview_mode="online",
        status="approved",
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def _previous_month_anchor(now_utc):
    current_month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if current_month_start.month == 1:
        previous_month_start = current_month_start.replace(
            year=current_month_start.year - 1,
            month=12,
        )
    else:
        previous_month_start = current_month_start.replace(month=current_month_start.month - 1)
    return previous_month_start + timedelta(days=5)


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_monthly_report_creates_html_and_admin_notifications(app, tmp_path):
    with app.app_context():
        app.config.update(
            JOBS_REPORT_CHANNELS="email",
            JOBS_REPORT_OUTPUT_DIR=str(tmp_path / "reports"),
            JOBS_WEBHOOK_URL=None,
        )

        admin_user = _make_user("admin.monthly.1", "admin.monthly.1@example.com", "admin")

        company_user = _make_user("company.monthly.1", "company.monthly.1@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Monthly Labs",
            "hr.monthly.1@example.com",
        )

        student_user = _make_user("student.monthly.1", "student.monthly.1@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21M1001")

        drive = _make_drive(company.company_id)
        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="selected",
        )
        db.session.add(application)

        monthly_anchor = _previous_month_anchor(datetime.now(timezone.utc))
        drive.created_at = monthly_anchor
        drive.updated_at = monthly_anchor
        application.application_date = monthly_anchor + timedelta(days=1)
        application.updated_at = monthly_anchor + timedelta(days=2)

        db.session.commit()

        first_run = execute_monthly_activity_report(task_request_id="monthly-test-run")
        assert first_run["status"] == "completed"
        assert first_run["metrics"]["drives_conducted"] >= 1
        assert first_run["metrics"]["students_applied"] >= 1
        assert first_run["metrics"]["students_selected"] >= 1

        report_path = Path(first_run["report"]["path"])
        assert report_path.exists()
        assert report_path.suffix == ".html"

        sent_to_admin = Notification.query.filter(
            Notification.recipient_id == admin_user.user_id,
            Notification.notification_type == "email",
            Notification.related_resource_type == "monthly_report",
        ).count()
        assert sent_to_admin == 1

        second_run = execute_monthly_activity_report(task_request_id="monthly-test-repeat")
        assert second_run["skipped"] is True
        assert second_run["reason"] == "already-ran-this-month"


def test_admin_can_trigger_monthly_report_endpoint(app, client, tmp_path):
    with app.app_context():
        app.config.update(
            JOBS_EAGER_EXECUTION=True,
            JOBS_REPORT_CHANNELS="email",
            JOBS_REPORT_OUTPUT_DIR=str(tmp_path / "reports-endpoint"),
            JOBS_WEBHOOK_URL=None,
        )

        admin_user = _make_user("admin.monthly.2", "admin.monthly.2@example.com", "admin")
        db.session.commit()
        headers = _auth_headers(admin_user.user_id, "admin")

    response = client.post("/jobs/reports/monthly/run", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["status"] in {"completed", "running", "queued", "failed"}


def test_company_can_trigger_pdf_monthly_report_endpoint(app, client, tmp_path):
    with app.app_context():
        app.config.update(
            JOBS_EAGER_EXECUTION=True,
            JOBS_REPORT_CHANNELS="email",
            JOBS_REPORT_OUTPUT_DIR=str(tmp_path / "reports-company-pdf"),
            JOBS_MONTHLY_REPORT_FORMAT="pdf",
            JOBS_MONTHLY_REPORT_AUDIENCE="company",
            JOBS_WEBHOOK_URL=None,
        )

        company_user = _make_user("company.monthly.3", "company.monthly.3@example.com", "company")
        _make_company_profile(
            company_user.user_id,
            "Monthly Company Labs",
            "hr.monthly.3@example.com",
        )
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")

    response = client.post("/jobs/reports/monthly/company/run?format=pdf", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["status"] == "completed"
    assert payload["audience"] == "company"
    assert payload["report_format"] == "pdf"

    report_path = Path(payload["report"]["path"])
    assert report_path.exists()
    assert report_path.suffix == ".pdf"

    with app.app_context():
        sent_to_company = Notification.query.filter(
            Notification.recipient_id == company_user.user_id,
            Notification.notification_type == "email",
            Notification.related_resource_type == "monthly_report",
        ).count()
        assert sent_to_company == 1
