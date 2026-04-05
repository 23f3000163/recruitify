from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import Company, Notification, User, db


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password("Password@123")
    db.session.add(user)
    db.session.flush()
    return user


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_admin_notifications_list_and_mark_routes(app, client):
    with app.app_context():
        admin_user = _make_user("admin.notify", "admin.notify@example.com", "admin")
        other_admin_user = _make_user("admin.other", "admin.other@example.com", "admin")
        company_user = _make_user("co.sender", "co.sender@example.com", "company")

        db.session.add_all(
            [
                Notification(
                    recipient_id=admin_user.user_id,
                    sender_id=company_user.user_id,
                    notification_type="in_app",
                    title="New Company Registration",
                    message="Acme Labs is awaiting review.",
                    delivery_status="sent",
                    is_read=False,
                    created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
                ),
                Notification(
                    recipient_id=admin_user.user_id,
                    sender_id=company_user.user_id,
                    notification_type="in_app",
                    title="New Drive Submitted",
                    message="Drive submission requires approval.",
                    delivery_status="sent",
                    is_read=False,
                    created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                ),
                Notification(
                    recipient_id=admin_user.user_id,
                    sender_id=company_user.user_id,
                    notification_type="in_app",
                    title="Reviewed Notification",
                    message="Already seen.",
                    delivery_status="sent",
                    is_read=True,
                    read_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                ),
                Notification(
                    recipient_id=admin_user.user_id,
                    sender_id=company_user.user_id,
                    notification_type="email",
                    title="Email Notification",
                    message="Should not appear in in-app list.",
                    delivery_status="sent",
                    is_read=False,
                ),
                Notification(
                    recipient_id=other_admin_user.user_id,
                    sender_id=company_user.user_id,
                    notification_type="in_app",
                    title="Other Admin Notification",
                    message="Isolated recipient",
                    delivery_status="sent",
                    is_read=False,
                ),
            ]
        )
        db.session.commit()

        headers = _auth_headers(admin_user.user_id, "admin")

    list_response = client.get("/admin/notifications?page=1&limit=10&is_read=all", headers=headers)

    assert list_response.status_code == 200
    list_payload = list_response.get_json()["data"]
    assert list_payload["total"] == 3
    assert list_payload["unread_count"] == 2
    assert len(list_payload["items"]) == 3

    unread_item = next((item for item in list_payload["items"] if not item["is_read"]), None)
    assert unread_item is not None
    notification_id = unread_item["notification_id"]

    mark_one_response = client.put(
        f"/admin/notifications/{notification_id}/read",
        headers=headers,
    )
    assert mark_one_response.status_code == 200
    mark_one_payload = mark_one_response.get_json()["data"]
    assert mark_one_payload["notification"]["is_read"] is True
    assert mark_one_payload["unread_count"] == 1

    mark_all_response = client.put("/admin/notifications/read-all", headers=headers)
    assert mark_all_response.status_code == 200
    mark_all_payload = mark_all_response.get_json()["data"]
    assert mark_all_payload["updated_count"] == 1
    assert mark_all_payload["unread_count"] == 0

    unread_response = client.get("/admin/notifications?is_read=false", headers=headers)
    assert unread_response.status_code == 200
    assert unread_response.get_json()["data"]["total"] == 0

    invalid_filter_response = client.get("/admin/notifications?is_read=maybe", headers=headers)
    assert invalid_filter_response.status_code == 400
    assert (
        invalid_filter_response.get_json()["error"]
        == "is_read must be one of all, true, or false"
    )


def test_admin_notifications_created_on_company_registration_and_drive_submission(app, client):
    with app.app_context():
        admin_user = _make_user("admin.flow", "admin.flow@example.com", "admin")
        db.session.commit()
        admin_user_id = admin_user.user_id

    register_payload = {
        "username": "company.flow",
        "email": "company.flow@example.com",
        "password": "Password@123",
        "company_name": "Flow Dynamics",
        "industry": "Software",
        "hr_contact_name": "Flow HR",
        "hr_contact_email": "flow.hr@example.com",
        "hr_contact_phone": "9999911111",
    }

    register_response = client.post("/auth/register/company", json=register_payload)
    assert register_response.status_code == 201

    with app.app_context():
        company = Company.query.filter_by(company_name="Flow Dynamics").first()
        assert company is not None

        registration_notification = Notification.query.filter_by(
            recipient_id=admin_user_id,
            title="New Company Registration",
            related_resource_type="company",
            related_resource_id=company.company_id,
        ).first()
        assert registration_notification is not None
        assert registration_notification.notification_type == "in_app"
        assert registration_notification.sender_id == company.user_id

        company.approval_status = "approved"
        db.session.commit()

        company_user_id = company.user_id

    company_headers = _auth_headers(company_user_id, "company")
    drive_payload = {
        "job_title": "Platform Engineer",
        "job_description": "Build scalable backend services",
        "required_skills": "Python,Flask,SQL",
        "experience_required": "1-3 years",
        "benefits": "Health insurance and L&D budget",
        "min_cgpa": 7.0,
        "eligible_branches": ["CSE", "ECE"],
        "eligible_years": [3, 4],
        "salary_lpa": 16,
        "job_location": "Bengaluru",
        "application_deadline": (
            datetime.now(timezone.utc) + timedelta(days=20)
        ).isoformat(),
        "interview_mode": "online",
    }

    drive_response = client.post("/company/drives", json=drive_payload, headers=company_headers)
    assert drive_response.status_code == 201
    drive_id = drive_response.get_json()["data"]["id"]

    with app.app_context():
        drive_notification = Notification.query.filter_by(
            recipient_id=admin_user_id,
            title="New Drive Submitted",
            related_resource_type="drive",
            related_resource_id=drive_id,
        ).first()
        assert drive_notification is not None
        assert drive_notification.notification_type == "in_app"
        assert drive_notification.sender_id == company_user_id


def test_admin_notifications_route_forbidden_for_non_admin_role(app, client):
    with app.app_context():
        student_user = _make_user("stu.notify", "stu.notify@example.com", "student")
        db.session.commit()
        headers = _auth_headers(student_user.user_id, "student")

    response = client.get("/admin/notifications", headers=headers)

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
