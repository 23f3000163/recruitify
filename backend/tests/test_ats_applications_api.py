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


def _make_student_profile(user_id, roll_number):
    student = Student(
        user_id=user_id,
        roll_number=roll_number,
        branch="CSE",
        year=4,
        cgpa=8.4,
        profile_completed=True,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Backend Engineer", status="approved", days=10):
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
        application_deadline=datetime.now(timezone.utc) + timedelta(days=days),
        interview_mode="online",
        status=status,
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_student_apply_persists_and_duplicate_is_rejected(app, client):
    with app.app_context():
        company_user = _make_user("company.ats.1", "company.ats.1@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "ATS Apply Corp",
            "hr.ats.apply@example.com",
            approval_status="approved",
        )
        drive = _make_drive(company.company_id, title="Platform Engineer", status="approved")

        student_user = _make_user("student.ats.1", "student.ats.1@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9801")

        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")
        drive_id = drive.drive_id
        student_id = student.student_id

    first_response = client.post(
        "/applications",
        json={"job_id": drive_id},
        headers=headers,
    )
    assert first_response.status_code == 201

    created_payload = first_response.get_json()["data"]
    assert created_payload["student_id"] == student_id
    assert created_payload["job_id"] == drive_id
    assert created_payload["status"] == "applied"

    duplicate_response = client.post(
        "/applications",
        json={"job_id": drive_id},
        headers=headers,
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.get_json()["error"] == "Student has already applied for this job"

    with app.app_context():
        count = Application.query.filter_by(student_id=student_id, drive_id=drive_id).count()
        assert count == 1


def test_company_status_update_persists_and_student_sees_latest_status(app, client):
    with app.app_context():
        company_user = _make_user("company.ats.2", "company.ats.2@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "ATS Pipeline Corp",
            "hr.ats.pipeline@example.com",
            approval_status="approved",
        )
        drive = _make_drive(company.company_id, title="Data Engineer", status="approved")

        student_user = _make_user("student.ats.2", "student.ats.2@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9802")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        company_headers = _auth_headers(company_user.user_id, "company")
        student_headers = _auth_headers(student_user.user_id, "student")
        application_id = application.application_id

    update_response = client.patch(
        f"/applications/{application_id}",
        json={"status": "shortlisted", "notes": "Strong profile alignment."},
        headers=company_headers,
    )
    assert update_response.status_code == 200
    update_payload = update_response.get_json()["data"]
    assert update_payload["status"] == "shortlisted"
    assert update_payload["notes"] == "Strong profile alignment."

    with app.app_context():
        refreshed = db.session.get(Application, application_id)
        assert refreshed is not None
        assert refreshed.status == "shortlisted"
        assert refreshed.notes == "Strong profile alignment."

    student_list_response = client.get(
        "/applications/student?status=shortlisted",
        headers=student_headers,
    )
    assert student_list_response.status_code == 200

    student_list_payload = student_list_response.get_json()["data"]
    assert student_list_payload["total"] == 1
    assert student_list_payload["items"][0]["application_id"] == application_id
    assert student_list_payload["items"][0]["status"] == "shortlisted"


def test_invalid_transition_is_rejected_by_backend(app, client):
    with app.app_context():
        company_user = _make_user("company.ats.3", "company.ats.3@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "ATS Transition Corp",
            "hr.ats.transition@example.com",
            approval_status="approved",
        )
        drive = _make_drive(company.company_id, title="Security Engineer", status="approved")

        student_user = _make_user("student.ats.3", "student.ats.3@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9803")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        company_headers = _auth_headers(company_user.user_id, "company")
        application_id = application.application_id

    invalid_transition_response = client.patch(
        f"/applications/{application_id}",
        json={"status": "offered"},
        headers=company_headers,
    )
    assert invalid_transition_response.status_code == 400
    assert "Invalid status transition" in invalid_transition_response.get_json()["error"]


def test_unauthorized_access_is_blocked(app, client):
    with app.app_context():
        owner_user = _make_user("company.ats.4", "company.ats.4@example.com", "company")
        owner_company = _make_company_profile(
            owner_user.user_id,
            "Owner ATS Corp",
            "hr.owner.ats@example.com",
            approval_status="approved",
        )
        drive = _make_drive(owner_company.company_id, title="SRE", status="approved")

        student_user = _make_user("student.ats.4", "student.ats.4@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9804")

        outsider_user = _make_user("company.ats.5", "company.ats.5@example.com", "company")
        _make_company_profile(
            outsider_user.user_id,
            "Outsider ATS Corp",
            "hr.outsider.ats@example.com",
            approval_status="approved",
        )

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        student_headers = _auth_headers(student_user.user_id, "student")
        outsider_headers = _auth_headers(outsider_user.user_id, "company")
        drive_id = drive.drive_id
        application_id = application.application_id

    job_view_forbidden = client.get(f"/applications/job/{drive_id}", headers=student_headers)
    assert job_view_forbidden.status_code == 403

    update_forbidden = client.patch(
        f"/applications/{application_id}",
        json={"status": "shortlisted"},
        headers=outsider_headers,
    )
    assert update_forbidden.status_code == 403


def test_only_approved_company_can_create_drive(app, client):
    with app.app_context():
        pending_user = _make_user("company.ats.6", "company.ats.6@example.com", "company")
        _make_company_profile(
            pending_user.user_id,
            "Pending ATS Corp",
            "hr.pending.ats@example.com",
            approval_status="pending",
        )
        db.session.commit()

        headers = _auth_headers(pending_user.user_id, "company")

    payload = {
        "job_title": "Cloud Engineer",
        "job_description": "Own cloud reliability",
        "required_skills": "AWS,Python",
        "experience_required": "1-2 years",
        "benefits": "Health insurance",
        "min_cgpa": 7.0,
        "eligible_branches": ["CSE", "ECE"],
        "eligible_years": [4],
        "salary_lpa": 18,
        "job_location": "Bengaluru",
        "application_deadline": (
            datetime.now(timezone.utc) + timedelta(days=20)
        ).isoformat(),
        "interview_mode": "online",
    }

    response = client.post("/company/drives", json=payload, headers=headers)

    assert response.status_code == 403
    assert response.get_json()["error"] == "Only approved companies can create jobs"
