from datetime import timedelta

from flask_jwt_extended import create_access_token

from app.models import User, db


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password("Password@123")
    db.session.add(user)
    db.session.flush()
    return user


def _auth_headers(user_id, role, expires_delta=None):
    token = create_access_token(
        identity=str(user_id),
        additional_claims={"role": role},
        expires_delta=expires_delta,
    )
    return {"Authorization": f"Bearer {token}"}


def test_company_endpoint_forbidden_for_student_role(app, client):
    with app.app_context():
        student_user = _make_user(
            "student.security.negative",
            "student.security.negative@example.com",
            "student",
        )
        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")

    response = client.get("/company/applications", headers=headers)

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Forbidden: insufficient permissions"


def test_expired_token_rejected_for_protected_endpoint(app, client):
    with app.app_context():
        company_user = _make_user(
            "company.security.expired",
            "company.security.expired@example.com",
            "company",
        )
        db.session.commit()

        expired_headers = _auth_headers(
            company_user.user_id,
            "company",
            expires_delta=timedelta(seconds=-1),
        )

    response = client.get("/company/applications", headers=expired_headers)

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Token has expired"


def test_jobs_company_export_forbidden_for_student_role(app, client):
    with app.app_context():
        student_user = _make_user(
            "student.jobs.security.negative",
            "student.jobs.security.negative@example.com",
            "student",
        )
        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")

    response = client.post("/jobs/exports/company/applications", headers=headers)

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Forbidden: insufficient permissions"


def test_expired_token_rejected_for_jobs_company_export(app, client):
    with app.app_context():
        company_user = _make_user(
            "company.jobs.security.expired",
            "company.jobs.security.expired@example.com",
            "company",
        )
        db.session.commit()

        expired_headers = _auth_headers(
            company_user.user_id,
            "company",
            expires_delta=timedelta(seconds=-1),
        )

    response = client.post("/jobs/exports/company/applications", headers=expired_headers)

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Token has expired"


def test_jobs_admin_export_forbidden_for_student_role(app, client):
    with app.app_context():
        student_user = _make_user(
            "student.jobs.admin.negative",
            "student.jobs.admin.negative@example.com",
            "student",
        )
        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")

    response = client.post("/jobs/exports/admin/companies", headers=headers)

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Forbidden: insufficient permissions"


def test_expired_token_rejected_for_jobs_admin_export(app, client):
    with app.app_context():
        admin_user = _make_user(
            "admin.jobs.security.expired",
            "admin.jobs.security.expired@example.com",
            "admin",
        )
        db.session.commit()

        expired_headers = _auth_headers(
            admin_user.user_id,
            "admin",
            expires_delta=timedelta(seconds=-1),
        )

    response = client.post("/jobs/exports/admin/companies", headers=expired_headers)

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Token has expired"
