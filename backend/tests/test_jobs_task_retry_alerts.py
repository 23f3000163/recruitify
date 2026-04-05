from types import SimpleNamespace

import pytest

from app.jobs.tasks import _retry_or_alert
from app.models import Notification, User, db


class _RetryInvoked(Exception):
    def __init__(self, kwargs):
        super().__init__("retry invoked")
        self.kwargs = kwargs


class _RetryTask:
    def __init__(self, retries):
        self.request = SimpleNamespace(retries=retries)

    def retry(self, **kwargs):
        raise _RetryInvoked(kwargs)


class _NoRetryTask:
    def __init__(self, retries):
        self.request = SimpleNamespace(retries=retries)

    def retry(self, **kwargs):
        raise AssertionError("retry should not be called when retries are exhausted")


def _make_admin():
    admin = User(
        username="jobs.retry.admin",
        email="jobs.retry.admin@example.com",
        role="admin",
        is_active=True,
    )
    admin.set_password("Password@123")
    db.session.add(admin)
    db.session.flush()
    return admin


def test_retry_or_alert_retries_with_exponential_backoff(app):
    with app.app_context():
        app.config.update(
            JOBS_RETRY_LIMIT=3,
            JOBS_RETRY_BACKOFF_SECONDS=10,
        )

        task = _RetryTask(retries=1)
        result = {"status": "failed", "error": "boom"}

        with pytest.raises(_RetryInvoked) as exc_info:
            _retry_or_alert(task, "jobs.test.task", result)

        retry_payload = exc_info.value.kwargs
        assert retry_payload["countdown"] == 20
        assert retry_payload["max_retries"] == 3
        assert isinstance(retry_payload["exc"], RuntimeError)


def test_retry_or_alert_notifies_admin_when_retries_are_exhausted(app):
    with app.app_context():
        app.config.update(
            JOBS_RETRY_LIMIT=2,
            JOBS_RETRY_BACKOFF_SECONDS=5,
            JOBS_FAILURE_ALERT_CHANNELS="email",
            JOBS_WEBHOOK_URL=None,
        )
        admin = _make_admin()
        db.session.commit()

        task = _NoRetryTask(retries=2)
        result = _retry_or_alert(
            task,
            "jobs.monthly_report.run",
            {"status": "failed", "error": "monthly report failed"},
            context={"job_id": "job-123"},
        )

        assert result["status"] == "failed"

        alerts = Notification.query.filter(
            Notification.recipient_id == admin.user_id,
            Notification.notification_type == "email",
            Notification.related_resource_type == "job_failure",
        ).all()
        assert len(alerts) == 1
        assert "Background Job Failed" in alerts[0].title
        assert "monthly report failed" in alerts[0].message


def test_retry_or_alert_returns_success_without_notifications(app):
    with app.app_context():
        app.config.update(JOBS_FAILURE_ALERT_CHANNELS="email")
        _make_admin()
        db.session.commit()

        task = _NoRetryTask(retries=0)
        success_result = {"status": "completed", "job_id": "job-ok"}

        returned = _retry_or_alert(task, "jobs.export_applications_csv.run", success_result)
        assert returned == success_result
        assert Notification.query.count() == 0
