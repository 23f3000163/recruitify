from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.models import (
    Application,
    Company,
    ExportArtifact,
    Placement,
    PlacementDrive,
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
        cgpa=8.6,
        profile_completed=True,
        is_blacklisted=False,
    )
    db.session.add(student)
    db.session.flush()
    return student


def _make_drive(company_id, title="Export Engineer"):
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
        application_deadline=datetime.now(timezone.utc) + timedelta(days=7),
        interview_mode="online",
        status="approved",
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def test_student_export_trigger_status_and_download(app, client, tmp_path):
    with app.app_context():
        app.config.update(
            JOBS_EAGER_EXECUTION=True,
            JOBS_EXPORT_OUTPUT_DIR=str(tmp_path / "exports"),
            JOBS_EXPORT_ARTIFACT_TTL_HOURS=24,
        )

        company_user = _make_user("company.export.1", "company.export.1@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Export Labs",
            "hr.export.1@example.com",
        )

        student_user = _make_user("student.export.1", "student.export.1@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21E1001")

        outsider_user = _make_user("student.export.2", "student.export.2@example.com", "student")
        _make_student_profile(outsider_user.user_id, "CS21E1002")

        drive = _make_drive(company.company_id)
        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        student_headers = _auth_headers(student_user.user_id, "student")
        outsider_headers = _auth_headers(outsider_user.user_id, "student")

    trigger_response = client.post("/jobs/exports/applications", headers=student_headers)
    assert trigger_response.status_code in {200, 202}

    trigger_payload = trigger_response.get_json()["data"]
    job_id = trigger_payload["job_id"]

    status_response = client.get(f"/jobs/exports/{job_id}", headers=student_headers)
    assert status_response.status_code == 200

    status_payload = status_response.get_json()["data"]
    assert status_payload["job"]["status"] == "completed"
    assert status_payload["artifact"] is not None

    download_response = client.get(
        f"/jobs/exports/{job_id}/download",
        headers=student_headers,
    )
    assert download_response.status_code == 200

    csv_content = download_response.data.decode("utf-8")
    assert "Student ID,Company Name,Drive Title,Application Status,Applied Date,Updated Date" in csv_content
    assert "Export Labs" in csv_content

    unauthorized_download = client.get(
        f"/jobs/exports/{job_id}/download",
        headers=outsider_headers,
    )
    assert unauthorized_download.status_code == 404


def test_expired_export_artifact_returns_410(app, client, tmp_path):
    with app.app_context():
        app.config.update(
            JOBS_EAGER_EXECUTION=True,
            JOBS_EXPORT_OUTPUT_DIR=str(tmp_path / "exports-expired"),
            JOBS_EXPORT_ARTIFACT_TTL_HOURS=24,
        )

        company_user = _make_user("company.export.3", "company.export.3@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Export Expiry Labs",
            "hr.export.3@example.com",
        )

        student_user = _make_user("student.export.3", "student.export.3@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21E1003")

        drive = _make_drive(company.company_id)
        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="applied",
        )
        db.session.add(application)
        db.session.commit()

        headers = _auth_headers(student_user.user_id, "student")

    trigger_response = client.post("/jobs/exports/applications", headers=headers)
    job_id = trigger_response.get_json()["data"]["job_id"]

    with app.app_context():
        artifact = (
            ExportArtifact.query.filter(ExportArtifact.job_id == job_id)
            .order_by(ExportArtifact.artifact_id.desc())
            .first()
        )
        assert artifact is not None
        artifact.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.session.commit()

    expired_response = client.get(f"/jobs/exports/{job_id}/download", headers=headers)
    assert expired_response.status_code == 410
    assert expired_response.get_json()["error"] == "Export artifact has expired"


def test_company_exports_applications_and_placements(app, client, tmp_path):
    with app.app_context():
        app.config.update(
            JOBS_EAGER_EXECUTION=True,
            JOBS_EXPORT_OUTPUT_DIR=str(tmp_path / "exports-company"),
            JOBS_EXPORT_ARTIFACT_TTL_HOURS=24,
            JOBS_COMPANY_EXPORT_ENABLED=True,
            JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY=True,
        )

        company_user = _make_user("company.export.5", "company.export.5@example.com", "company")
        company = _make_company_profile(
            company_user.user_id,
            "Company Export Labs",
            "hr.export.5@example.com",
        )

        student_user = _make_user("student.export.5", "student.export.5@example.com", "student")
        student = _make_student_profile(student_user.user_id, "CS21E1005")

        drive = _make_drive(company.company_id, title="Company Export Engineer")
        application = Application(
            student_id=student.student_id,
            drive_id=drive.drive_id,
            status="selected",
        )
        db.session.add(application)
        db.session.flush()

        placement = Placement(
            student_id=student.student_id,
            company_id=company.company_id,
            drive_id=drive.drive_id,
            position="Software Engineer",
            salary=17.5,
            joining_date=datetime.now(timezone.utc).date(),
        )
        db.session.add(placement)
        db.session.commit()

        company_headers = _auth_headers(company_user.user_id, "company")
        student_headers = _auth_headers(student_user.user_id, "student")

    applications_trigger = client.post("/jobs/exports/company/applications", headers=company_headers)
    assert applications_trigger.status_code in {200, 202}

    applications_job_id = applications_trigger.get_json()["data"]["job_id"]
    applications_status = client.get(
        f"/jobs/exports/company/{applications_job_id}",
        headers=company_headers,
    )
    assert applications_status.status_code == 200
    assert applications_status.get_json()["data"]["job"]["status"] == "completed"

    applications_download = client.get(
        f"/jobs/exports/company/{applications_job_id}/download",
        headers=company_headers,
    )
    assert applications_download.status_code == 200
    applications_csv = applications_download.data.decode("utf-8")
    assert "Student ID,Student Name,Student Email,Drive Title,Application Status,Applied Date,Updated Date" in applications_csv
    assert "student.export.5" in applications_csv

    placements_trigger = client.post("/jobs/exports/company/placements", headers=company_headers)
    assert placements_trigger.status_code in {200, 202}

    placements_job_id = placements_trigger.get_json()["data"]["job_id"]
    placements_download = client.get(
        f"/jobs/exports/company/{placements_job_id}/download",
        headers=company_headers,
    )
    assert placements_download.status_code == 200
    placements_csv = placements_download.data.decode("utf-8")
    assert "Student ID,Student Name,Student Email,Drive Title,Position,Salary,Joining Date,Placement Date" in placements_csv
    assert "Software Engineer" in placements_csv

    forbidden_student_access = client.post("/jobs/exports/company/applications", headers=student_headers)
    assert forbidden_student_access.status_code == 403
