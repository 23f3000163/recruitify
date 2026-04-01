from datetime import date, datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import (
    Application,
    Company,
    Notification,
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
        cgpa=8.5,
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
        benefits="Health insurance and bonus",
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


def test_company_notifications_workflow_including_student_offer_response(app, client):
    with app.app_context():
        company_user = _make_user("company.notify", "company.notify@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Notify Corp",
            "hr.notify@example.com",
        )

        # Existing notifications for list/filter behavior
        db.session.add_all(
            [
                Notification(
                    recipient_id=company_user.user_id,
                    notification_type="in_app",
                    title="Pipeline Reminder",
                    message="Review pending applications.",
                    delivery_status="sent",
                    is_read=False,
                ),
                Notification(
                    recipient_id=company_user.user_id,
                    notification_type="in_app",
                    title="Interview Update",
                    message="Interview panel updated.",
                    delivery_status="sent",
                    is_read=False,
                ),
                Notification(
                    recipient_id=company_user.user_id,
                    notification_type="in_app",
                    title="Old Notification",
                    message="Already reviewed.",
                    delivery_status="sent",
                    is_read=True,
                ),
            ]
        )

        student_user = _make_user("student.notify", "student.notify@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21B9301")

        drive = _make_drive(company.company_id, title="SRE Engineer", status="approved")
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
            salary=1700000,
            position="Site Reliability Engineer",
            joining_date=date.today() + timedelta(days=30),
            status="offered",
        )
        db.session.add(offer)
        db.session.commit()

        company_headers = _auth_headers(company_user.user_id, "company")
        student_headers = _auth_headers(student_user.user_id, "student")
        offer_id = offer.offer_id

    # Student response should create company in-app notification
    offer_response = client.put(
        f"/student/offers/{offer_id}/respond",
        json={"status": "accepted"},
        headers=student_headers,
    )
    assert offer_response.status_code == 200

    list_response = client.get("/company/notifications?is_read=false", headers=company_headers)
    assert list_response.status_code == 200

    list_payload = list_response.get_json()["data"]
    assert list_payload["total"] == 3
    assert list_payload["unread_count"] == 3
    assert any(item["title"] == "Offer Response Received" for item in list_payload["items"])

    first_notification_id = list_payload["items"][0]["notification_id"]
    mark_one_response = client.put(
        f"/company/notifications/{first_notification_id}/read",
        headers=company_headers,
    )
    assert mark_one_response.status_code == 200
    assert mark_one_response.get_json()["data"]["unread_count"] == 2

    mark_all_response = client.put("/company/notifications/read-all", headers=company_headers)
    assert mark_all_response.status_code == 200
    assert mark_all_response.get_json()["data"]["unread_count"] == 0

    unread_response = client.get("/company/notifications?is_read=false", headers=company_headers)
    assert unread_response.status_code == 200
    assert unread_response.get_json()["data"]["total"] == 0


def test_company_notifications_validate_read_filter(app, client):
    with app.app_context():
        company_user = _make_user("company.filter", "company.filter@example.com", "company")
        _make_company_profile(
            company_user.user_id,
            "Filter Corp",
            "hr.filter@example.com",
        )
        db.session.commit()
        headers = _auth_headers(company_user.user_id, "company")

    response = client.get("/company/notifications?is_read=maybe", headers=headers)

    assert response.status_code == 400
    assert response.get_json()["error"] == "is_read must be one of all, true, or false"
