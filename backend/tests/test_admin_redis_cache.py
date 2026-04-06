from fnmatch import fnmatch

import pytest
from flask_jwt_extended import create_access_token

from app.admin import routes as admin_routes
from app.cache import RedisApiCache
from app.models import User, db


class FakeRedis:
    def __init__(self):
        self._store = {}
        self.now = 0
        self.get_calls = 0
        self.setex_calls = 0
        self.delete_calls = 0

    def get(self, key):
        self.get_calls += 1
        self._purge_expired()
        item = self._store.get(key)
        if not item:
            return None
        return item["value"]

    def setex(self, key, ttl_seconds, value):
        self.setex_calls += 1
        ttl = max(int(ttl_seconds), 1)
        self._store[key] = {
            "value": value,
            "expires_at": self.now + ttl,
        }
        return True

    def scan(self, cursor=0, match=None, count=200):  # noqa: ARG002
        self._purge_expired()
        keys = list(self._store.keys())
        if match:
            keys = [key for key in keys if fnmatch(key, match)]
        return 0, keys

    def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self._store:
                removed += 1
                self._store.pop(key, None)
        self.delete_calls += removed
        return removed

    def advance(self, seconds):
        self.now += int(seconds)
        self._purge_expired()

    def _purge_expired(self):
        expired_keys = [
            key
            for key, value in self._store.items()
            if value["expires_at"] <= self.now
        ]
        for key in expired_keys:
            self._store.pop(key, None)


class FailingRedis:
    def get(self, key):  # noqa: ARG002
        raise RuntimeError("Redis unavailable")

    def setex(self, key, ttl_seconds, value):  # noqa: ARG002
        raise RuntimeError("Redis unavailable")

    def scan(self, cursor=0, match=None, count=200):  # noqa: ARG002
        raise RuntimeError("Redis unavailable")

    def delete(self, *keys):
        raise RuntimeError("Redis unavailable")


def _make_user(username, email, role):
    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password("Password@123")
    db.session.add(user)
    db.session.flush()
    return user


def _auth_headers(user_id, role):
    token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(app):
    with app.app_context():
        admin_user = _make_user("admin.cache", "admin.cache@example.com", "admin")
        db.session.commit()
        return _auth_headers(admin_user.user_id, "admin")


def _install_cache(app, cache_instance):
    with app.app_context():
        app.extensions["redis_cache"] = cache_instance


def _service_payload(call_number):
    return {
        "success": True,
        "data": {
            "items": [{"id": call_number}],
            "total": 1,
            "page": 1,
            "pages": 1,
            "limit": 10,
        },
    }, 200


@pytest.mark.parametrize(
    ("endpoint", "service_name"),
    [
        ("/admin/jobs", "list_jobs"),
        ("/admin/search/companies?q=acme", "search_companies"),
        ("/admin/search/students?q=john", "search_students"),
    ],
)
def test_admin_cache_miss_then_set_and_hit(app, client, monkeypatch, endpoint, service_name):
    fake_redis = FakeRedis()
    cache = RedisApiCache(client=fake_redis, enabled=True, key_prefix="test")
    _install_cache(app, cache)
    headers = _admin_headers(app)

    calls = {"count": 0}

    def _stubbed_service(*args, **kwargs):  # noqa: ARG001
        calls["count"] += 1
        return _service_payload(calls["count"])

    monkeypatch.setattr(admin_routes.services, service_name, _stubbed_service)

    first_response = client.get(endpoint, headers=headers)
    assert first_response.status_code == 200
    first_payload = first_response.get_json()
    assert first_payload["data"]["items"][0]["id"] == 1

    second_response = client.get(endpoint, headers=headers)
    assert second_response.status_code == 200
    second_payload = second_response.get_json()
    assert second_payload["data"]["items"][0]["id"] == 1

    assert calls["count"] == 1
    assert fake_redis.setex_calls == 1
    assert len(fake_redis._store) == 1


def test_admin_cache_expiry_refreshes_company_search(app, client, monkeypatch):
    fake_redis = FakeRedis()
    cache = RedisApiCache(client=fake_redis, enabled=True, key_prefix="test")
    _install_cache(app, cache)
    headers = _admin_headers(app)

    with app.app_context():
        app.config["CACHE_COMPANY_SEARCH_TTL_SECONDS"] = 1

    calls = {"count": 0}

    def _stubbed_company_search(*args, **kwargs):  # noqa: ARG001
        calls["count"] += 1
        return _service_payload(calls["count"])

    monkeypatch.setattr(admin_routes.services, "search_companies", _stubbed_company_search)

    first_response = client.get("/admin/search/companies?q=acme", headers=headers)
    assert first_response.status_code == 200
    assert first_response.get_json()["data"]["items"][0]["id"] == 1

    fake_redis.advance(2)

    second_response = client.get("/admin/search/companies?q=acme", headers=headers)
    assert second_response.status_code == 200
    assert second_response.get_json()["data"]["items"][0]["id"] == 2
    assert calls["count"] == 2


def test_admin_cache_invalidation_refreshes_jobs_after_write(app, client, monkeypatch):
    fake_redis = FakeRedis()
    cache = RedisApiCache(client=fake_redis, enabled=True, key_prefix="test")
    _install_cache(app, cache)
    headers = _admin_headers(app)

    list_calls = {"count": 0}

    def _stubbed_list_jobs(*args, **kwargs):  # noqa: ARG001
        list_calls["count"] += 1
        return _service_payload(list_calls["count"])

    def _stubbed_approve_job(job_id, actor_user_id):  # noqa: ARG001
        return {"success": True, "data": {"id": job_id, "status": "approved"}}, 200

    monkeypatch.setattr(admin_routes.services, "list_jobs", _stubbed_list_jobs)
    monkeypatch.setattr(admin_routes.services, "approve_job", _stubbed_approve_job)

    warm_response = client.get("/admin/jobs", headers=headers)
    assert warm_response.status_code == 200
    assert warm_response.get_json()["data"]["items"][0]["id"] == 1
    assert len(fake_redis._store) == 1

    approve_response = client.put("/admin/job/99/approve", headers=headers)
    assert approve_response.status_code == 200
    assert fake_redis.delete_calls >= 1
    assert len(fake_redis._store) == 0

    refreshed_response = client.get("/admin/jobs", headers=headers)
    assert refreshed_response.status_code == 200
    assert refreshed_response.get_json()["data"]["items"][0]["id"] == 2
    assert list_calls["count"] == 2


def test_admin_cache_gracefully_falls_back_when_redis_unavailable(app, client, monkeypatch):
    cache = RedisApiCache(client=FailingRedis(), enabled=True, key_prefix="test")
    _install_cache(app, cache)
    headers = _admin_headers(app)

    calls = {"count": 0}

    def _stubbed_student_search(*args, **kwargs):  # noqa: ARG001
        calls["count"] += 1
        return _service_payload(calls["count"])

    monkeypatch.setattr(admin_routes.services, "search_students", _stubbed_student_search)

    first_response = client.get("/admin/search/students?q=john", headers=headers)
    assert first_response.status_code == 200
    assert first_response.get_json()["data"]["items"][0]["id"] == 1

    second_response = client.get("/admin/search/students?q=john", headers=headers)
    assert second_response.status_code == 200
    assert second_response.get_json()["data"]["items"][0]["id"] == 2

    assert cache.is_available is False
    assert calls["count"] == 2