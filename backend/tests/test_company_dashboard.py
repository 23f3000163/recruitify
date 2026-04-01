from datetime import date, datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import (
    Application,
    Company,
    Interview,
    PlacementDrive,
    PlacementOffer,
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


def _make_student_profile(user_id, roll_number):
    student = Student(
        user_id=user_id,
        roll_number=roll_number,
        branch="CSE",
        year=4,
        cgpa=8.1,
        profile_completed=True,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def _make_drive(company_id, title, status, deadline):
    drive = PlacementDrive(
        company_id=company_id,
        job_title=title,
        job_description="Core job responsibilities",
        required_skills="Python,SQL",
        min_cgpa=6.0,
        eligible_branches=["CSE", "ECE"],
        eligible_years=[3, 4],
        salary_lpa=12.0,
        job_location="Remote",
        application_deadline=deadline,
        interview_mode="online",
        status=status,
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def test_company_dashboard_bootstrap_returns_summary_pipeline_and_recent_rows(app, client):
    now = datetime.now(timezone.utc)

    with app.app_context():
        company_user = _make_user("company.one", "company.one@example.com", "company")
        company = Company(
            user_id=company_user.user_id,
            company_name="Aurora Labs",
            industry="Software",
            hr_contact_name="Ari HR",
            hr_contact_email="ari.hr@aurora.example.com",
            hr_contact_phone="9999999999",
            approval_status="approved",
        )
        db.session.add(company)
        db.session.flush()

        student_user_1 = _make_user("student.alpha", "student.alpha@example.com", "student")
        student_user_2 = _make_user("student.beta", "student.beta@example.com", "student")
        student_user_3 = _make_user("student.gamma", "student.gamma@example.com", "student")
        student_user_4 = _make_user("student.delta", "student.delta@example.com", "student")

        student_1 = _make_student_profile(student_user_1.user_id, "CS21B1001")
        student_2 = _make_student_profile(student_user_2.user_id, "CS21B1002")
        student_3 = _make_student_profile(student_user_3.user_id, "CS21B1003")
        student_4 = _make_student_profile(student_user_4.user_id, "CS21B1004")

        drive_pending = _make_drive(
            company.company_id,
            "Graduate Engineer",
            "pending",
            now + timedelta(days=10),
        )
        drive_approved = _make_drive(
            company.company_id,
            "Platform Intern",
            "approved",
            now + timedelta(days=15),
        )
        drive_closed = _make_drive(
            company.company_id,
            "QA Analyst",
            "closed",
            now + timedelta(days=5),
        )

        application_1 = Application(
            student_id=student_1.student_id,
            drive_id=drive_pending.drive_id,
            status="applied",
            updated_at=now - timedelta(hours=3),
        )
        application_2 = Application(
            student_id=student_2.student_id,
            drive_id=drive_approved.drive_id,
            status="shortlisted",
            updated_at=now - timedelta(hours=2),
        )
        application_3 = Application(
            student_id=student_3.student_id,
            drive_id=drive_approved.drive_id,
            status="interviewed",
            updated_at=now - timedelta(minutes=45),
        )
        application_4 = Application(
            student_id=student_4.student_id,
            drive_id=drive_closed.drive_id,
            status="selected",
            updated_at=now - timedelta(minutes=10),
        )
        db.session.add_all([application_1, application_2, application_3, application_4])
        db.session.flush()

        interview = Interview(
            application_id=application_3.application_id,
            company_id=company.company_id,
            drive_id=drive_approved.drive_id,
            interview_date=now + timedelta(days=2),
            interview_mode="online",
            interviewer_name="Panel One",
            result="pending",
        )
        db.session.add(interview)

        offer = PlacementOffer(
            application_id=application_4.application_id,
            student_id=student_4.student_id,
            company_id=company.company_id,
            drive_id=drive_closed.drive_id,
            salary=1400000,
            position="QA Analyst",
            joining_date=date.today() + timedelta(days=30),
            status="offered",
        )
        db.session.add(offer)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")

    response = client.get("/auth/company/dashboard", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["message"] == "Company dashboard loaded successfully"

    data = payload["data"]
    assert data["user"]["company_name"] == "Aurora Labs"

    summary = data["summary"]
    assert summary == {
        "active_drives": 2,
        "applications_received": 4,
        "interviews_scheduled": 1,
        "offers_released": 1,
    }

    pipeline = {item["id"]: item["count"] for item in data["pipeline"]}
    assert pipeline == {
        "pending": 1,
        "screening": 2,
        "interviews": 1,
        "offers": 1,
    }

    recent = data["recent_applicants"]
    assert len(recent) == 4
    assert recent[0]["status"] == "selected"
    assert recent[0]["student_name"] == "student.delta"
    assert recent[1]["status"] == "interviewed"


def test_company_dashboard_bootstrap_returns_empty_collections_for_new_company(app, client):
    with app.app_context():
        company_user = _make_user("company.empty", "company.empty@example.com", "company")
        company = Company(
            user_id=company_user.user_id,
            company_name="Empty Corp",
            industry="Consulting",
            hr_contact_name="Evan HR",
            hr_contact_email="hr.empty@example.com",
            hr_contact_phone="8888888888",
            approval_status="approved",
        )
        db.session.add(company)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")

    response = client.get("/auth/company/dashboard", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["summary"] == {
        "active_drives": 0,
        "applications_received": 0,
        "interviews_scheduled": 0,
        "offers_released": 0,
    }
    assert payload["recent_applicants"] == []
    assert all(stage["count"] == 0 for stage in payload["pipeline"])


def test_company_dashboard_forbidden_for_non_company_user(app, client):
    with app.app_context():
        student_user = _make_user("student.viewer", "student.viewer@example.com", "student")
        headers = _auth_headers(student_user.user_id, "student")

    response = client.get("/auth/company/dashboard", headers=headers)

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False