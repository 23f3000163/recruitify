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
        cgpa=8.2,
        profile_completed=True,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Backend Engineer", status="approved"):
    drive = PlacementDrive(
        company_id=company_id,
        job_title=title,
        job_description="Core job responsibilities",
        required_skills="Python,SQL",
        experience_required="0-2 years",
        benefits="Learning stipend, insurance",
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


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_company_can_list_and_update_application_status(app, client):
    with app.app_context():
        company_user = _make_user("company.phase4", "phase4.company@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Phase4 Labs",
            "hr.phase4@example.com",
        )
        drive = _make_drive(company.company_id, title="Platform Engineer", status="approved")

        student_user = _make_user("student.phase4", "student.phase4@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9001")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        application_id = application.application_id

    list_response = client.get("/company/applications", headers=headers)
    assert list_response.status_code == 200

    list_payload = list_response.get_json()["data"]
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["student_name"] == "student.phase4"
    assert list_payload["items"][0]["status"] == "applied"

    update_response = client.put(
        f"/company/applications/{application_id}/status",
        json={
            "status": "shortlisted",
            "notes": "Profile aligns with role requirements.",
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["data"]["status"] == "shortlisted"
    assert (
        update_response.get_json()["data"]["notes"]
        == "Profile aligns with role requirements."
    )

    filtered_response = client.get("/company/applications?status=shortlisted", headers=headers)
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.get_json()["data"]
    assert filtered_payload["total"] == 1
    assert filtered_payload["items"][0]["application_id"] == application_id


def test_company_rejection_requires_reason_and_saves_feedback(app, client):
    with app.app_context():
        company_user = _make_user(
            "company.feedback",
            "company.feedback@example.com",
            "company",
        )
        company = _make_company_profile(
            company_user.user_id,
            "Feedback Labs",
            "hr.feedback@example.com",
        )
        drive = _make_drive(company.company_id, title="Data Analyst", status="approved")

        student_user = _make_user("student.feedback", "student.feedback@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9101")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        application_id = application.application_id

    missing_reason_response = client.put(
        f"/company/applications/{application_id}/status",
        json={"status": "rejected", "notes": "Interview rubric mismatch."},
        headers=headers,
    )
    assert missing_reason_response.status_code == 400
    assert (
        missing_reason_response.get_json()["error"]
        == "rejection_reason is required when status is rejected"
    )

    reject_response = client.put(
        f"/company/applications/{application_id}/status",
        json={
            "status": "rejected",
            "rejection_reason": "Did not meet technical cutoff.",
            "notes": "Interview rubric mismatch.",
        },
        headers=headers,
    )
    assert reject_response.status_code == 200
    reject_payload = reject_response.get_json()["data"]
    assert reject_payload["status"] == "rejected"
    assert reject_payload["rejection_reason"] == "Did not meet technical cutoff."
    assert reject_payload["notes"] == "Interview rubric mismatch."

    with app.app_context():
        refreshed = db.session.get(Application, application_id)
        assert refreshed is not None
        assert refreshed.status == "rejected"
        assert refreshed.rejection_reason == "Did not meet technical cutoff."
        assert refreshed.notes == "Interview rubric mismatch."


def test_company_status_transition_rules_are_enforced(app, client):
    with app.app_context():
        company_user = _make_user(
            "company.transition.guard",
            "company.transition.guard@example.com",
            "company",
        )
        company = _make_company_profile(
            company_user.user_id,
            "Transition Guard Labs",
            "hr.transition.guard@example.com",
        )
        drive = _make_drive(company.company_id, title="Cloud Engineer", status="approved")

        student_user = _make_user(
            "student.transition.guard",
            "student.transition.guard@example.com",
            "student",
        )
        student = _make_student_profile(student_user.user_id, "CS21B9199")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        application_id = application.application_id

    invalid_transition_response = client.put(
        f"/company/applications/{application_id}/status",
        json={"status": "selected"},
        headers=headers,
    )

    assert invalid_transition_response.status_code == 400
    assert (
        invalid_transition_response.get_json()["error"]
        == "Invalid status transition: applied -> offered"
    )


def test_company_can_schedule_interview_and_update_result(app, client):
    with app.app_context():
        company_user = _make_user("company.interview", "company.interview@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Interview Corp",
            "hr.interview@example.com",
        )
        drive = _make_drive(company.company_id, title="Data Engineer", status="approved")

        student_user = _make_user("student.interview", "student.interview@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9002")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="shortlisted",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        application_id = application.application_id

    schedule_payload = {
        "application_id": application_id,
        "interview_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "interview_mode": "online",
        "interviewer_name": "Panel A",
    }

    schedule_response = client.post("/company/interviews", json=schedule_payload, headers=headers)
    assert schedule_response.status_code == 201

    interview_data = schedule_response.get_json()["data"]
    assert interview_data["application_id"] == application_id
    assert interview_data["result"] == "pending"
    interview_id = interview_data["interview_id"]

    update_response = client.put(
        f"/company/interviews/{interview_id}/result",
        json={"result": "pass", "feedback": "Strong communication"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["data"]["result"] == "pass"

    with app.app_context():
        interview = db.session.get(Interview, interview_id)
        application = db.session.get(Application, application_id)
        assert interview is not None
        assert application is not None
        assert application.status == "selected"


def test_company_can_release_offer_and_list_offers(app, client):
    with app.app_context():
        company_user = _make_user("company.offer", "company.offer@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Offer Corp",
            "hr.offer@example.com",
        )
        drive = _make_drive(company.company_id, title="SRE", status="approved")

        student_user = _make_user("student.offer", "student.offer@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9003")

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="interviewed",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(company_user.user_id, "company")
        application_id = application.application_id

    create_payload = {
        "application_id": application_id,
        "salary": 1450000,
        "position": "Site Reliability Engineer",
        "joining_date": (date.today() + timedelta(days=45)).isoformat(),
    }

    create_response = client.post("/company/offers", json=create_payload, headers=headers)
    assert create_response.status_code == 201

    create_data = create_response.get_json()["data"]
    assert create_data["status"] == "offered"
    assert create_data["application_id"] == application_id

    list_response = client.get("/company/offers?status=offered", headers=headers)
    assert list_response.status_code == 200
    list_data = list_response.get_json()["data"]
    assert list_data["total"] == 1
    assert list_data["items"][0]["position"] == "Site Reliability Engineer"

    duplicate_response = client.post("/company/offers", json=create_payload, headers=headers)
    assert duplicate_response.status_code == 400

    with app.app_context():
        offer_count = db.session.query(PlacementOffer).count()
        application = db.session.get(Application, application_id)
        assert offer_count == 1
        assert application.status == "selected"
