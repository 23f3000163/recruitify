from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import Application, Company, Notification, PlacementDrive, Student, User, db


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
        cgpa=8.3,
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
        benefits="Health insurance and flexible hours",
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


def test_student_can_view_application_timeline_and_notifications(app, client):
    with app.app_context():
        company_user = _make_user("company.step3", "company.step3@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Step3 Labs",
            "hr.step3@example.com",
        )
        drive = _make_drive(company.company_id, title="Platform Engineer", status="approved")

        student_user = _make_user("student.step3", "student.step3@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9201")

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

    update_response = client.put(
        f"/company/applications/{application_id}/status",
        json={
            "status": "shortlisted",
            "notes": "Excellent project portfolio.",
        },
        headers=company_headers,
    )
    assert update_response.status_code == 200

    applications_response = client.get(
        "/student/applications?status=shortlisted",
        headers=student_headers,
    )
    assert applications_response.status_code == 200

    applications_payload = applications_response.get_json()["data"]
    assert applications_payload["total"] == 1

    row = applications_payload["items"][0]
    assert row["status"] == "shortlisted"
    assert row["status_label"] == "Shortlisted"
    assert row["notes"] == "Excellent project portfolio."
    assert row["drive"]["title"] == "Platform Engineer"
    assert row["company"]["name"] == "Step3 Labs"
    assert any(event["label"] == "Shortlisted" for event in row["timeline"])

    notifications_response = client.get("/student/notifications", headers=student_headers)
    assert notifications_response.status_code == 200

    notifications_payload = notifications_response.get_json()["data"]
    assert notifications_payload["total"] == 1
    assert notifications_payload["unread_count"] == 1
    assert notifications_payload["items"][0]["title"] == "Application Update"

    dashboard_response = client.get("/student/dashboard", headers=student_headers)
    assert dashboard_response.status_code == 200

    dashboard_payload = dashboard_response.get_json()["data"]
    assert dashboard_payload["summary"]["applications_total"] == 1
    assert dashboard_payload["summary"]["shortlisted"] == 1
    assert dashboard_payload["unread_notifications"] == 1


def test_student_can_mark_notification_as_read(app, client):
    with app.app_context():
        student_user = _make_user("student.notify", "student.notify@example.com", "student")
        _make_student_profile(student_user.user_id, "CS21B9202")

        notification = Notification(
            recipient_id=student_user.user_id,
            notification_type="in_app",
            title="Interview Scheduled",
            message="Your interview is scheduled for tomorrow.",
            related_resource_type="interview",
            related_resource_id=101,
            delivery_status="sent",
            is_read=False,
        )
        db.session.add(notification)
        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")
        notification_id = notification.notification_id

    response = client.put(
        f"/student/notifications/{notification_id}/read",
        headers=headers,
    )
    assert response.status_code == 200

    payload = response.get_json()["data"]
    assert payload["notification"]["notification_id"] == notification_id
    assert payload["notification"]["is_read"] is True
    assert payload["unread_count"] == 0

    with app.app_context():
        refreshed = db.session.get(Notification, notification_id)
        assert refreshed is not None
        assert refreshed.is_read is True
        assert refreshed.read_at is not None
