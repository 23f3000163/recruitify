from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import Application, Company, PlacementDrive, Student, User, db


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


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def _make_drive(company_id, title="Backend Engineer", status="approved"):
    drive = PlacementDrive(
        company_id=company_id,
        job_title=title,
        job_description="Core job responsibilities",
        required_skills="Python,SQL",
        experience_required="0-2 years",
        benefits="Health insurance, flexible hours",
        min_cgpa=6.0,
        eligible_branches=["CSE", "ECE"],
        eligible_years=[3, 4],
        salary_lpa=14.0,
        job_location="Remote",
        application_deadline=datetime.now(timezone.utc) + timedelta(days=10),
        interview_mode="online",
        status=status,
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def test_company_can_create_and_list_own_drives(app, client):
    with app.app_context():
        company_user = _make_user("company.phase3", "phase3.company@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Phase3 Labs",
            "hr.phase3@example.com",
        )

        other_company_user = _make_user("company.other", "other.company@example.com", "company")
        other_company = _make_company_profile(
            other_company_user.user_id,
            "Other Works",
            "hr.other@example.com",
        )
        _make_drive(other_company.company_id, title="External Drive", status="approved")
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        company_id = company.company_id

    payload = {
        "job_title": "Platform Engineer",
        "job_description": "Build backend systems",
        "required_skills": "Python,Flask,SQL",
        "experience_required": "1-3 years",
        "benefits": "Medical insurance, relocation support",
        "min_cgpa": 7.0,
        "eligible_branches": ["CSE", "ECE"],
        "eligible_years": [3, 4],
        "salary_lpa": 18,
        "job_location": "Bengaluru",
        "application_deadline": (datetime.now(timezone.utc) + timedelta(days=20)).isoformat(),
        "interview_mode": "online",
    }

    create_response = client.post("/company/drives", json=payload, headers=headers)

    assert create_response.status_code == 201
    create_data = create_response.get_json()["data"]
    assert create_data["job_title"] == "Platform Engineer"
    assert create_data["experience_required"] == "1-3 years"
    assert create_data["benefits"] == "Medical insurance, relocation support"
    assert create_data["status"] == "pending"

    list_response = client.get("/company/drives?status=pending", headers=headers)

    assert list_response.status_code == 200
    list_data = list_response.get_json()["data"]
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1
    assert list_data["items"][0]["job_title"] == "Platform Engineer"
    assert list_data["items"][0]["company_id"] == company_id


def test_company_can_close_owned_drive_and_receive_application_count(app, client):
    with app.app_context():
        company_user = _make_user("company.close", "company.close@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Closure Corp",
            "hr.close@example.com",
        )
        drive = _make_drive(company.company_id, title="SDE Intern", status="approved")

        student_user = _make_user("student.candidate", "student.candidate@example.com", "student")
        student = Student(
            user_id=student_user.user_id,
            roll_number="CS21B2001",
            branch="CSE",
            year=4,
            cgpa=8.4,
            profile_completed=True,
        )
        db.session.add(student)
        db.session.flush()

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        drive_id = drive.drive_id

    response = client.put(f"/company/drives/{drive_id}/close", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["status"] == "closed"
    assert payload["applications_count"] == 1


def test_company_drive_routes_forbid_non_company_role(app, client):
    with app.app_context():
        student_user = _make_user("student.viewer", "student.viewer+drives@example.com", "student")
        headers = _auth_headers(student_user.user_id, "student")

    response = client.get("/company/drives", headers=headers)

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False


def test_company_create_drive_rejects_invalid_branch(app, client):
    with app.app_context():
        company_user = _make_user("company.invalid", "company.invalid@example.com", "company")
        _make_company_profile(company_user.user_id, "Invalid Branch Inc", "hr.invalid@example.com")
        db.session.commit()
        headers = _auth_headers(company_user.user_id, "company")

    payload = {
        "job_title": "QA Engineer",
        "job_description": "Manual and automation testing",
        "required_skills": "Testing,Automation",
        "experience_required": "0-1 years",
        "benefits": "Health plan",
        "min_cgpa": 6.5,
        "eligible_branches": ["BIO"],
        "eligible_years": [4],
        "application_deadline": (datetime.now(timezone.utc) + timedelta(days=12)).isoformat(),
        "interview_mode": "online",
    }

    response = client.post("/company/drives", json=payload, headers=headers)

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "Unsupported branch" in payload["error"]


def test_company_create_drive_requires_experience_and_benefits(app, client):
    with app.app_context():
        company_user = _make_user("company.required", "company.required@example.com", "company")
        _make_company_profile(company_user.user_id, "Required Fields Inc", "hr.required@example.com")
        db.session.commit()
        headers = _auth_headers(company_user.user_id, "company")

    payload = {
        "job_title": "Cloud Engineer",
        "job_description": "Own cloud reliability",
        "required_skills": "AWS,Terraform",
        "min_cgpa": 7.2,
        "eligible_branches": ["CSE", "ECE"],
        "eligible_years": [4],
        "application_deadline": (datetime.now(timezone.utc) + timedelta(days=20)).isoformat(),
        "interview_mode": "online",
    }

    missing_experience_response = client.post("/company/drives", json=payload, headers=headers)
    assert missing_experience_response.status_code == 400
    assert missing_experience_response.get_json()["error"] == "experience_required is required"

    payload["experience_required"] = "1-2 years"

    missing_benefits_response = client.post("/company/drives", json=payload, headers=headers)
    assert missing_benefits_response.status_code == 400
    assert missing_benefits_response.get_json()["error"] == "benefits is required"