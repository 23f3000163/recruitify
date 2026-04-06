import json
from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import (
    Application,
    Company,
    Placement,
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


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def _make_company_profile(user_id, name, hr_email, approval_status="approved"):
    company = Company(
        user_id=user_id,
        company_name=name,
        industry="Software",
        hr_contact_name="Hiring Lead",
        hr_contact_email=hr_email,
        hr_contact_phone="9999999999",
        approval_status=approval_status,
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
        skills="Python,SQL,Flask",
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Backend Engineer", status="approved", days=10):
    drive = PlacementDrive(
        company_id=company_id,
        job_title=title,
        job_description="Core job responsibilities",
        required_skills="Python,SQL,Flask",
        experience_required="0-2 years",
        benefits="Health insurance",
        min_cgpa=6.0,
        eligible_branches=["CSE", "ECE"],
        eligible_years=[3, 4],
        salary_lpa=14.0,
        job_location="Remote",
        application_deadline=datetime.now(timezone.utc) + timedelta(days=days),
        interview_mode="online",
        status=status,
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def test_admin_analytics_overview_contract_and_months_filter(app, client):
    with app.app_context():
        admin_user = _make_user(
            "admin.analytics.one",
            "admin.analytics.one@example.com",
            "admin",
        )

        company_user = _make_user(
            "company.analytics.one",
            "company.analytics.one@example.com",
            "company",
        )
        company = _make_company_profile(
            company_user.user_id,
            "Analytics Owner Corp",
            "analytics.owner.hr@example.com",
            approval_status="approved",
        )

        student_user = _make_user(
            "student.analytics.one",
            "student.analytics.one@example.com",
            "student",
        )
        student = _make_student_profile(student_user.user_id, "CS21A1001")

        drive = _make_drive(company.company_id, title="Platform Engineer", status="approved")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="selected",
        )
        db.session.add(application)
        db.session.flush()

        offer = PlacementOffer(
            application_id=application.application_id,
            student_id=student.student_id,
            company_id=company.company_id,
            drive_id=drive.drive_id,
            salary=14.0,
            position="Platform Engineer",
            joining_date=(datetime.now(timezone.utc) + timedelta(days=20)).date(),
            status="accepted",
        )
        db.session.add(offer)
        db.session.flush()

        placement = Placement(
            student_id=student.student_id,
            company_id=company.company_id,
            drive_id=drive.drive_id,
            position="Platform Engineer",
            salary=14.0,
            joining_date=(datetime.now(timezone.utc) + timedelta(days=20)).date(),
        )
        db.session.add(placement)

        db.session.commit()

        headers = _auth_headers(admin_user.user_id, "admin")

    response = client.get("/admin/analytics/overview?months=3", headers=headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["success"] is True
    data = payload["data"]

    assert data["meta"]["months"] == 3
    assert len(data["placement_trends"]) == 3

    summary = data["summary"]
    assert summary["total_students"] == 1
    assert summary["total_companies"] == 1
    assert summary["total_jobs"] == 1
    assert summary["total_applications"] == 1
    assert summary["offers_released"] == 1
    assert summary["offers_accepted"] == 1
    assert summary["total_placements"] == 1

    funnel = data["application_funnel"]
    assert funnel["placed"] == 1
    assert funnel["total"] == 1

    skill_rows = data["job_demand_by_skills"]
    assert isinstance(skill_rows, list)
    for row in skill_rows:
        assert "skill" in row
        assert "demand_count" in row


def test_admin_analytics_overview_rejects_invalid_months_and_non_admin_role(app, client):
    with app.app_context():
        admin_user = _make_user(
            "admin.analytics.two",
            "admin.analytics.two@example.com",
            "admin",
        )
        student_user = _make_user(
            "student.analytics.two",
            "student.analytics.two@example.com",
            "student",
        )
        db.session.commit()

        admin_headers = _auth_headers(admin_user.user_id, "admin")
        student_headers = _auth_headers(student_user.user_id, "student")

    forbidden_response = client.get("/admin/analytics/overview", headers=student_headers)
    assert forbidden_response.status_code == 403
    assert forbidden_response.get_json()["error"] == "Forbidden: insufficient permissions"

    invalid_months_response = client.get(
        "/admin/analytics/overview?months=0",
        headers=admin_headers,
    )
    assert invalid_months_response.status_code == 400
    assert "months must be between 1 and 24" in invalid_months_response.get_json()["error"]


def test_public_landing_dashboard_contract_and_safety(app, client):
    with app.app_context():
        company_user_approved = _make_user(
            "company.public.approved",
            "company.public.approved@example.com",
            "company",
        )
        company_user_pending = _make_user(
            "company.public.pending",
            "company.public.pending@example.com",
            "company",
        )

        approved_company = _make_company_profile(
            company_user_approved.user_id,
            "Public Approved Corp",
            "public.approved.hr@example.com",
            approval_status="approved",
        )
        pending_company = _make_company_profile(
            company_user_pending.user_id,
            "Public Pending Corp",
            "public.pending.hr@example.com",
            approval_status="pending",
        )

        student_user = _make_user(
            "student.public.one",
            "student.public.one@example.com",
            "student",
        )
        _make_student_profile(student_user.user_id, "CS21A1002")

        _make_drive(approved_company.company_id, title="Approved Drive", status="approved")
        _make_drive(pending_company.company_id, title="Pending Drive", status="pending")

        db.session.commit()

    response = client.get("/admin/public/landing-dashboard?months=2")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["success"] is True

    data = payload["data"]
    assert data["meta"]["months"] == 2
    assert len(data["placement_trends"]) == 2
    assert data["highlights"]["total_students"] == 1
    assert data["highlights"]["approved_companies"] == 1
    assert data["highlights"]["approved_drives"] == 1

    serialized_data = json.dumps(data).lower()
    assert "hr_contact_email" not in serialized_data
    assert "resume_url" not in serialized_data
    assert "password_hash" not in serialized_data


def test_public_landing_dashboard_rejects_invalid_months(app, client):
    response = client.get("/admin/public/landing-dashboard?months=abc")

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "months must be an integer"