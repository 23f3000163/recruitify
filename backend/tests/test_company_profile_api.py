from flask_jwt_extended import create_access_token

from app.models import Company, User, db


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password("Password@123")
    db.session.add(user)
    db.session.flush()
    return user


def _make_company_profile(user_id, company_name, hr_email, **overrides):
    profile = Company(
        user_id=user_id,
        company_name=company_name,
        industry=overrides.get("industry", "Software"),
        location=overrides.get("location", "Pune"),
        website=overrides.get("website", "https://example.com"),
        hr_contact_name=overrides.get("hr_contact_name", "Hiring Lead"),
        hr_contact_email=hr_email,
        hr_contact_phone=overrides.get("hr_contact_phone", "9999999999"),
        company_description=overrides.get("company_description", "Initial description"),
        approval_status=overrides.get("approval_status", "approved"),
    )
    db.session.add(profile)
    db.session.flush()
    return profile


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_company_profile_get_and_patch_flow(app, client):
    with app.app_context():
        company_user = _make_user("company.profile", "company.profile@example.com", "company")
        _make_company_profile(
            company_user.user_id,
            "Profile Labs",
            "hr.profile@example.com",
            location="Pune",
        )
        db.session.commit()
        headers = _auth_headers(company_user.user_id, "company")

    get_response = client.get("/company/profile", headers=headers)
    assert get_response.status_code == 200

    get_payload = get_response.get_json()["data"]
    assert get_payload["company_name"] == "Profile Labs"
    assert get_payload["hr_contact_email"] == "hr.profile@example.com"
    assert get_payload["location"] == "Pune"

    update_response = client.patch(
        "/company/profile",
        json={
            "company_name": "Profile Labs India",
            "industry": "Fintech",
            "website": "https://profilelabs.example",
            "hr_contact_name": "Ari Recruiter",
            "hr_contact_email": "ari.profile@example.com",
            "location": "Bengaluru",
            "company_description": "Updated company profile details",
        },
        headers=headers,
    )
    assert update_response.status_code == 200

    update_payload = update_response.get_json()["data"]
    assert update_payload["company_name"] == "Profile Labs India"
    assert update_payload["industry"] == "Fintech"
    assert update_payload["website"] == "https://profilelabs.example"
    assert update_payload["hr_contact_name"] == "Ari Recruiter"
    assert update_payload["hr_contact_email"] == "ari.profile@example.com"
    assert update_payload["location"] == "Bengaluru"
    assert update_payload["company_description"] == "Updated company profile details"

    with app.app_context():
        persisted = Company.query.filter_by(user_id=company_user.user_id).first()
        assert persisted is not None
        assert persisted.company_name == "Profile Labs India"
        assert persisted.hr_contact_email == "ari.profile@example.com"
        assert persisted.location == "Bengaluru"


def test_company_profile_patch_validates_email_and_uniques(app, client):
    with app.app_context():
        first_user = _make_user("company.first", "company.first@example.com", "company")
        second_user = _make_user("company.second", "company.second@example.com", "company")

        _make_company_profile(first_user.user_id, "First Labs", "first.hr@example.com")
        _make_company_profile(second_user.user_id, "Second Labs", "second.hr@example.com")

        db.session.commit()
        headers = _auth_headers(first_user.user_id, "company")

    duplicate_name_response = client.patch(
        "/company/profile",
        json={"company_name": "Second Labs"},
        headers=headers,
    )
    assert duplicate_name_response.status_code == 409
    assert duplicate_name_response.get_json()["error"] == "Company name already exists"

    invalid_email_response = client.patch(
        "/company/profile",
        json={"hr_contact_email": "not-an-email"},
        headers=headers,
    )
    assert invalid_email_response.status_code == 400
    assert invalid_email_response.get_json()["error"] == "Invalid HR contact email format"

    duplicate_email_response = client.patch(
        "/company/profile",
        json={"hr_contact_email": "second.hr@example.com"},
        headers=headers,
    )
    assert duplicate_email_response.status_code == 409
    assert duplicate_email_response.get_json()["error"] == "HR contact email already exists"


def test_company_profile_forbidden_for_non_company_role(app, client):
    with app.app_context():
        student_user = _make_user("student.viewer", "student.viewer@example.com", "student")
        db.session.commit()
        headers = _auth_headers(student_user.user_id, "student")

    get_response = client.get("/company/profile", headers=headers)
    assert get_response.status_code == 403

    patch_response = client.patch(
        "/company/profile",
        json={"company_name": "Should Not Work"},
        headers=headers,
    )
    assert patch_response.status_code == 403
