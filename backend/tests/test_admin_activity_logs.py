from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import ActivityLog, Application, Company, PlacementDrive, Student, User, db


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password("Password@123")
    db.session.add(user)
    db.session.flush()
    return user


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_approve_company_creates_persistent_activity_log(app, client):
    with app.app_context():
        admin_user = _make_user("admin.one", "admin.one@example.com", "admin")
        company_user = _make_user("co.one", "co.one@example.com", "company")
        company = Company(
            user_id=company_user.user_id,
            company_name="Acme Labs",
            industry="Software",
            hr_contact_name="Ava HR",
            hr_contact_email="hr.acme@example.com",
            hr_contact_phone="9999999999",
            approval_status="pending",
        )
        db.session.add(company)
        db.session.commit()

        admin_user_id = admin_user.user_id
        admin_username = admin_user.username
        company_id = company.company_id
        headers = _auth_headers(admin_user_id, "admin")

    response = client.put(f"/admin/company/{company_id}/approve", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True

    with app.app_context():
        db_company = db.session.get(Company, company_id)
        assert db_company.approval_status == "approved"

        logs = ActivityLog.query.order_by(ActivityLog.log_id.desc()).all()
        assert len(logs) == 1
        latest = logs[0]
        assert latest.user_id == admin_user_id
        assert latest.action == "Company Approved"
        assert latest.target == "Acme Labs"
        assert latest.status == "success"

    logs_response = client.get("/admin/activity-logs?limit=10", headers=headers)
    assert logs_response.status_code == 200
    logs_payload = logs_response.get_json()
    assert logs_payload["success"] is True
    assert logs_payload["data"]["total"] == 1
    assert len(logs_payload["data"]["items"]) == 1
    assert logs_payload["data"]["items"][0]["action"] == "Company Approved"
    assert logs_payload["data"]["items"][0]["actor"] == admin_username


def test_admin_application_status_update_endpoint_is_not_available(app, client):
    with app.app_context():
        admin_user = _make_user("admin.two", "admin.two@example.com", "admin")
        company_user = _make_user("co.two", "co.two@example.com", "company")
        student_user = _make_user("stu.two", "stu.two@example.com", "student")

        company = Company(
            user_id=company_user.user_id,
            company_name="Beta Systems",
            industry="Product",
            hr_contact_name="Ben HR",
            hr_contact_email="hr.beta@example.com",
            hr_contact_phone="8888888888",
            approval_status="approved",
        )
        db.session.add(company)
        db.session.flush()

        student = Student(
            user_id=student_user.user_id,
            roll_number="CS21B1001",
            branch="CSE",
            year=4,
            cgpa=8.4,
        )
        db.session.add(student)
        db.session.flush()

        drive = PlacementDrive(
            company_id=company.company_id,
            job_title="SDE Intern",
            job_description="Build features",
            required_skills="Python,SQL",
            experience_required="0-1 years",
            benefits="Insurance and mentoring",
            min_cgpa=6.5,
            eligible_branches=["CSE", "ECE"],
            eligible_years=[3, 4],
            salary_lpa=12.0,
            job_location="Remote",
            application_deadline=datetime.now(timezone.utc) + timedelta(days=30),
            interview_mode="online",
            status="approved",
        )
        db.session.add(drive)
        db.session.flush()

        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        admin_user_id = admin_user.user_id
        headers = _auth_headers(admin_user_id, "admin")
        application_id = application.application_id

    status_response = client.put(
        f"/admin/application/{application_id}/status",
        json={"status": "shortlisted"},
        headers=headers,
    )
    assert status_response.status_code == 404

    with app.app_context():
        refreshed = db.session.get(Application, application_id)
        assert refreshed is not None
        assert refreshed.status == "applied"
        assert ActivityLog.query.filter_by(action="Application Updated").count() == 0


def test_activity_logs_exclude_legacy_application_updated_rows(app, client):
    with app.app_context():
        admin_user = _make_user("admin.legacy", "admin.legacy@example.com", "admin")
        db.session.add_all(
            [
                ActivityLog(
                    user_id=admin_user.user_id,
                    action="Application Updated",
                    target="#55 -> shortlisted",
                    status="success",
                ),
                ActivityLog(
                    user_id=admin_user.user_id,
                    action="Company Approved",
                    target="Gamma Corp",
                    status="success",
                ),
            ]
        )
        db.session.commit()

        headers = _auth_headers(admin_user.user_id, "admin")

    response = client.get("/admin/activity-logs?limit=20", headers=headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 1
    assert len(payload["data"]["items"]) == 1
    assert payload["data"]["items"][0]["action"] == "Company Approved"
    assert payload["data"]["items"][0]["target"] == "Gamma Corp"


def test_activity_logs_limit_validation(app, client):
    with app.app_context():
        admin_user = _make_user("admin.three", "admin.three@example.com", "admin")
        headers = _auth_headers(admin_user.user_id, "admin")

    bad_response = client.get("/admin/activity-logs?limit=abc", headers=headers)
    assert bad_response.status_code == 400
    assert bad_response.get_json()["error"] == "limit must be an integer"

    zero_response = client.get("/admin/activity-logs?limit=0", headers=headers)
    assert zero_response.status_code == 400
    assert zero_response.get_json()["error"] == "limit must be greater than 0"


def test_activity_logs_forbidden_for_non_admin_role(app, client):
    with app.app_context():
        student_user = _make_user("stu.three", "stu.three@example.com", "student")
        headers = _auth_headers(student_user.user_id, "student")

    response = client.get("/admin/activity-logs", headers=headers)
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
