"""Redis-backed API cache helpers with graceful fallback."""

import json
from urllib.parse import urlparse


CACHE_NAMESPACE_ADMIN_JOBS = "admin:jobs"
CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH = "admin:search:companies"
CACHE_NAMESPACE_ADMIN_STUDENT_SEARCH = "admin:search:students"


class RedisApiCache:
    """Small JSON cache wrapper that fails open when Redis is unavailable."""

    def __init__(
        self,
        client=None,
        *,
        enabled=True,
        key_prefix="recruitify",
        logger=None,
    ):
        self._client = client
        self._enabled = bool(enabled)
        self._key_prefix = (key_prefix or "recruitify").strip() or "recruitify"
        self._logger = logger
        self._disabled_due_to_error = False

    @property
    def is_available(self):
        return self._enabled and self._client is not None and not self._disabled_due_to_error

    def bind_client(self, client):
        self._client = client
        self._disabled_due_to_error = False

    def make_key(self, namespace, suffix):
        clean_namespace = (namespace or "api").strip() or "api"
        clean_suffix = (suffix or "default").strip() or "default"
        return f"{self._key_prefix}:{clean_namespace}:{clean_suffix}"

    def get_json(self, key):
        if not self.is_available:
            return None

        try:
            raw_value = self._client.get(key)
            if raw_value is None:
                return None
            return json.loads(raw_value)
        except Exception as exc:  # pragma: no cover - defensive fallback
            self._mark_unavailable(exc)
            return None

    def set_json(self, key, payload, ttl_seconds):
        if not self.is_available:
            return False

        try:
            normalized_ttl = max(int(ttl_seconds), 1)
            self._client.setex(key, normalized_ttl, json.dumps(payload))
            return True
        except Exception as exc:  # pragma: no cover - defensive fallback
            self._mark_unavailable(exc)
            return False

    def delete_by_pattern(self, pattern, batch_size=200):
        if not self.is_available:
            return 0

        deleted = 0
        cursor = 0

        try:
            while True:
                cursor, keys = self._client.scan(cursor=cursor, match=pattern, count=batch_size)
                if keys:
                    deleted += self._client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as exc:  # pragma: no cover - defensive fallback
            self._mark_unavailable(exc)

        return int(deleted)

    def _mark_unavailable(self, exc):
        if self._disabled_due_to_error:
            return

        self._disabled_due_to_error = True
        if self._logger:
            self._logger.warning(
                "Redis cache became unavailable, continuing without cache: %s",
                exc,
            )


def _sanitize_redis_url(raw_url):
    if not raw_url:
        return None

    parsed = urlparse(raw_url)
    host = parsed.hostname or "localhost"
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or ""
    return f"{parsed.scheme}://{host}{port}{path}"


def invalidate_api_cache_namespaces(cache, *namespaces):
    """Delete all keys for the given namespaces and return deleted key count."""
    if not cache or not getattr(cache, "is_available", False):
        return 0

    deleted = 0
    for namespace in namespaces:
        if not namespace:
            continue
        pattern = cache.make_key(namespace, "*")
        deleted += cache.delete_by_pattern(pattern)

    return int(deleted)


def init_cache(app):
    """Initialize Redis cache extension in fail-open mode."""
    cache = RedisApiCache(
        enabled=app.config.get("CACHE_ENABLED", True),
        key_prefix=app.config.get("CACHE_KEY_PREFIX", "recruitify"),
        logger=app.logger,
    )
    app.extensions["redis_cache"] = cache

    if not cache._enabled:
        app.logger.info("API cache disabled by configuration.")
        return cache

    redis_url = app.config.get("CACHE_REDIS_URL")
    if not redis_url:
        app.logger.warning("CACHE_REDIS_URL is empty; API cache disabled.")
        return cache

    try:
        import redis
    except ModuleNotFoundError:
        app.logger.warning("redis package not installed; API cache disabled.")
        return cache

    try:
        client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=app.config.get("CACHE_REDIS_CONNECT_TIMEOUT_SECONDS", 1),
            socket_timeout=app.config.get("CACHE_REDIS_SOCKET_TIMEOUT_SECONDS", 1),
        )
        cache.bind_client(client)
        app.logger.info("API cache configured with Redis at %s", _sanitize_redis_url(redis_url))
    except Exception as exc:  # pragma: no cover - defensive fallback
        app.logger.warning(
            "Redis client init failed; continuing without API cache: %s",
            exc,
        )

    return cache


__all__ = [
    "CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH",
    "CACHE_NAMESPACE_ADMIN_JOBS",
    "CACHE_NAMESPACE_ADMIN_STUDENT_SEARCH",
    "RedisApiCache",
    "init_cache",
    "invalidate_api_cache_namespaces",
]