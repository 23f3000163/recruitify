from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import Application, Company, PlacementDrive, Student, User, db


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password("Password@123")
    db.session.add(user)
    db.session.flush()
    return user


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


def _make_student_profile(user_id, roll_number, skills=None, experience_summary=None):
    student = Student(
        user_id=user_id,
        roll_number=roll_number,
        branch="CSE",
        year=4,
        cgpa=8.4,
        profile_completed=True,
        skills=skills,
        experience_summary=experience_summary,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Backend Engineer", required_skills="Python,SQL", days=10):
    drive = PlacementDrive(
        company_id=company_id,
        job_title=title,
        job_description="Core job responsibilities",
        required_skills=required_skills,
        experience_required="0-2 years",
        benefits="Health insurance",
        min_cgpa=6.0,
        eligible_branches=["CSE", "ECE"],
        eligible_years=[3, 4],
        salary_lpa=14.0,
        job_location="Remote",
        application_deadline=datetime.now(timezone.utc) + timedelta(days=days),
        interview_mode="online",
        status="approved",
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_student_can_score_keywords_against_job(app, client):
    with app.app_context():
        company_user = _make_user(
            "company.screen.one",
            "company.screen.one@example.com",
            "company",
        )
        company = _make_company_profile(
            company_user.user_id,
            "Screening Corp One",
            "screen.one.hr@example.com",
            approval_status="approved",
        )
        drive = _make_drive(
            company.company_id,
            title="Platform Engineer",
            required_skills="Python,SQL,Flask",
        )

        student_user = _make_user(
            "student.screen.one",
            "student.screen.one@example.com",
            "student",
        )
        student = _make_student_profile(
            student_user.user_id,
            "CS21S1001",
            skills="Python,Flask",
            experience_summary="Built SQL APIs and dashboards",
        )
        student.resume_url = "https://cdn.example.com/resume/student-python-sql.pdf"

        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")
        drive_id = drive.drive_id
        student_id = student.student_id

    response = client.post(
        "/applications/screener",
        json={"job_id": drive_id},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True

    data = payload["data"]
    assert data["meta"]["role"] == "student"
    assert data["job"]["job_id"] == drive_id
    assert data["candidate"]["student_id"] == student_id
    assert data["candidate"]["application_id"] is None

    analysis = data["analysis"]
    assert analysis["score"] >= 66
    assert analysis["matched_count"] >= 2
    assert analysis["total_keywords"] == 3
    assert "python" in analysis["matched_keywords"]


def test_company_can_score_its_own_application(app, client):
    with app.app_context():
        company_user = _make_user(
            "company.screen.two",
            "company.screen.two@example.com",
            "company",
        )
        company = _make_company_profile(
            company_user.user_id,
            "Screening Corp Two",
            "screen.two.hr@example.com",
            approval_status="approved",
        )
        drive = _make_drive(
            company.company_id,
            title="Data Engineer",
            required_skills="Python,SQL",
        )

        student_user = _make_user(
            "student.screen.two",
            "student.screen.two@example.com",
            "student",
        )
        student = _make_student_profile(
            student_user.user_id,
            "CS21S1002",
            skills="Python",
            experience_summary="Worked on ETL pipelines",
        )

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        application_id = application.application_id

    response = client.post(
        "/applications/screener",
        json={"application_id": application_id},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["meta"]["role"] == "company"
    assert payload["data"]["candidate"]["application_id"] == application_id


def test_company_cannot_score_other_company_application(app, client):
    with app.app_context():
        owner_user = _make_user(
            "company.screen.owner",
            "company.screen.owner@example.com",
            "company",
        )
        owner_company = _make_company_profile(
            owner_user.user_id,
            "Owner Screening Corp",
            "screen.owner.hr@example.com",
            approval_status="approved",
        )
        drive = _make_drive(owner_company.company_id, title="SRE", required_skills="Linux,Python")

        outsider_user = _make_user(
            "company.screen.outsider",
            "company.screen.outsider@example.com",
            "company",
        )
        _make_company_profile(
            outsider_user.user_id,
            "Outsider Screening Corp",
            "screen.outsider.hr@example.com",
            approval_status="approved",
        )

        student_user = _make_user(
            "student.screen.three",
            "student.screen.three@example.com",
            "student",
        )
        student = _make_student_profile(
            student_user.user_id,
            "CS21S1003",
            skills="Linux",
            experience_summary="Infrastructure automation",
        )

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        outsider_headers = _auth_headers(outsider_user.user_id, "company")
        application_id = application.application_id

    response = client.post(
        "/applications/screener",
        json={"application_id": application_id},
        headers=outsider_headers,
    )

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Forbidden: cannot screen applications for this job"


def test_student_screener_requires_job_id(app, client):
    with app.app_context():
        student_user = _make_user(
            "student.screen.four",
            "student.screen.four@example.com",
            "student",
        )
        _make_student_profile(student_user.user_id, "CS21S1004", skills="Python")
        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")

    response = client.post("/applications/screener", json={}, headers=headers)

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "job_id must be an integer"