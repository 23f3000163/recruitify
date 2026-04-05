from uuid import uuid4

from app.models import BackgroundJob, ExportArtifact, User, db


def _new_user(role="student"):
    unique = uuid4().hex[:8]
    user = User(
        username=f"jobs_{role}_{unique}",
        email=f"jobs_{role}_{unique}@example.com",
        role=role,
        is_active=True,
    )
    user.set_password("Secret@123")
    db.session.add(user)
    db.session.flush()
    return user


def test_jobs_health_endpoint(client):
    response = client.get("/jobs/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True

    data = payload["data"]
    assert data["status"] in {"ok", "degraded"}
    assert "celery_initialized" in data
    assert "broker" in data
    assert "result_backend" in data
    assert "schedules" in data


def test_background_job_and_export_artifact_models(app):
    with app.app_context():
        requester = _new_user(role="student")

        job = BackgroundJob(
            job_type="export_csv",
            status="queued",
            requested_by_user_id=requester.user_id,
            idempotency_key=f"export-{uuid4().hex}",
            payload={"source": "student_history"},
        )
        db.session.add(job)
        db.session.flush()

        artifact = ExportArtifact(
            job_id=job.job_id,
            requested_by_user_id=requester.user_id,
            filename="applications.csv",
            storage_path="exports/applications.csv",
            status="pending",
        )
        db.session.add(artifact)
        db.session.commit()

        saved_job = db.session.get(BackgroundJob, job.job_id)
        assert saved_job is not None
        assert saved_job.job_id
        assert saved_job.export_artifacts.count() == 1

        saved_artifact = saved_job.export_artifacts.first()
        assert saved_artifact.filename == "applications.csv"
        assert saved_artifact.requested_by_user_id == requester.user_id

        job_payload = saved_job.to_dict()
        artifact_payload = saved_artifact.to_dict()
        assert job_payload["job_type"] == "export_csv"
        assert artifact_payload["status"] == "pending"
