import os


def _env_int(name, default_value):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default_value
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default_value


def _env_bool(name, default_value=False):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return bool(default_value)

    normalized = str(raw_value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return bool(default_value)


def _env_float(name, default_value):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default_value

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default_value


_instance_path = os.path.join(os.path.dirname(__file__), "instance")


class BaseConfig:
    # os.environ.get() — not os.environ[] — so that importing this module before
    # the environment is loaded does not crash.  validate_config() enforces that
    # these values are actually present after configuration has been selected.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS: list[str] = os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5173"
    ).split(",")


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    TESTING: bool = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(_instance_path, 'recruitify.db')}"
    )
    CELERY_BROKER_URL = os.environ.get(
        "CELERY_BROKER_URL",
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
    )
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND",
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
    )
    CELERY_TIMEZONE = os.environ.get("CELERY_TIMEZONE", "Asia/Kolkata")
    JOBS_DAILY_REMINDER_CRON = os.environ.get("JOBS_DAILY_REMINDER_CRON", "0 9 * * *")
    JOBS_TEST_MODE = os.getenv("JOBS_TEST_MODE", "false").lower() == "true"
    JOBS_DISABLE_IDEMPOTENCY = os.getenv("JOBS_DISABLE_IDEMPOTENCY", "false").lower() == "true"
    JOBS_MONTHLY_REPORT_CRON = os.environ.get("JOBS_MONTHLY_REPORT_CRON", "0 9 1 * *")
    JOBS_EXPORT_ARTIFACT_TTL_HOURS = _env_int("JOBS_EXPORT_ARTIFACT_TTL_HOURS", 24)
    JOBS_RETRY_LIMIT = _env_int("JOBS_RETRY_LIMIT", 3)
    JOBS_RETRY_BACKOFF_SECONDS = _env_int("JOBS_RETRY_BACKOFF_SECONDS", 60)
    JOBS_REMINDER_LOOKAHEAD_DAYS = _env_int("JOBS_REMINDER_LOOKAHEAD_DAYS", 3)
    JOBS_INTERVIEW_REMINDER_ENABLED = _env_bool("JOBS_INTERVIEW_REMINDER_ENABLED", False)
    JOBS_INTERVIEW_REMINDER_CRON = os.environ.get(
        "JOBS_INTERVIEW_REMINDER_CRON",
        "30 9 * * *",
    )
    JOBS_INTERVIEW_REMINDER_WINDOW_HOURS = _env_int(
        "JOBS_INTERVIEW_REMINDER_WINDOW_HOURS",
        24,
    )
    JOBS_REMINDER_CHANNELS = os.environ.get(
        "JOBS_REMINDER_CHANNELS",
        "email",
    )
    JOBS_INTERVIEW_REMINDER_CHANNELS = os.environ.get(
        "JOBS_INTERVIEW_REMINDER_CHANNELS",
        os.environ.get("JOBS_REMINDER_CHANNELS", "email"),
    )
    JOBS_WEBHOOK_URL = os.environ.get("JOBS_WEBHOOK_URL")
    JOBS_REPORT_CHANNELS = os.environ.get("JOBS_REPORT_CHANNELS", "email")
    JOBS_MONTHLY_REPORT_AUDIENCE = os.environ.get("JOBS_MONTHLY_REPORT_AUDIENCE", "admin")
    JOBS_MONTHLY_REPORT_FORMAT = os.environ.get("JOBS_MONTHLY_REPORT_FORMAT", "html")
    JOBS_EXPORT_ALERT_CHANNELS = os.environ.get("JOBS_EXPORT_ALERT_CHANNELS", "in_app,email")
    JOBS_COMPANY_EXPORT_ENABLED = _env_bool("JOBS_COMPANY_EXPORT_ENABLED", False)
    JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY = _env_bool(
        "JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY",
        False,
    )
    JOBS_FAILURE_ALERT_CHANNELS = os.environ.get(
        "JOBS_FAILURE_ALERT_CHANNELS",
        os.environ.get("JOBS_REPORT_CHANNELS", "email"),
    )
    JOBS_REPORT_OUTPUT_DIR = os.environ.get(
        "JOBS_REPORT_OUTPUT_DIR",
        os.path.join(_instance_path, "reports"),
    )
    JOBS_EXPORT_OUTPUT_DIR = os.environ.get(
        "JOBS_EXPORT_OUTPUT_DIR",
        os.path.join(_instance_path, "exports"),
    )
    JOBS_EAGER_EXECUTION = _env_bool("JOBS_EAGER_EXECUTION", False)
    MAIL_FROM_ADDRESS = os.environ.get("MAIL_FROM_ADDRESS", "noreply@recruitify.local")
    MAIL_SMTP_HOST = os.environ.get("MAIL_SMTP_HOST")
    MAIL_SMTP_PORT = _env_int("MAIL_SMTP_PORT", 587)
    MAIL_SMTP_USERNAME = os.environ.get("MAIL_SMTP_USERNAME")
    MAIL_SMTP_PASSWORD = os.environ.get("MAIL_SMTP_PASSWORD")
    MAIL_SMTP_USE_TLS = _env_bool("MAIL_SMTP_USE_TLS", True)
    MAIL_SMTP_USE_SSL = _env_bool("MAIL_SMTP_USE_SSL", False)
    MAIL_TIMEOUT_SECONDS = _env_int("MAIL_TIMEOUT_SECONDS", 10)
    MAIL_SIMULATE_WHEN_UNCONFIGURED = _env_bool("MAIL_SIMULATE_WHEN_UNCONFIGURED", False)
    ANALYTICS_LOOKBACK_MONTHS = _env_int("ANALYTICS_LOOKBACK_MONTHS", 6)
    CACHE_ENABLED = False
    CACHE_KEY_PREFIX = os.environ.get("CACHE_KEY_PREFIX", "recruitify")
    CACHE_REDIS_URL = os.environ.get(
        "CACHE_REDIS_URL",
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/2"),
    )
    CACHE_REDIS_CONNECT_TIMEOUT_SECONDS = _env_float(
        "CACHE_REDIS_CONNECT_TIMEOUT_SECONDS",
        0.5,
    )
    CACHE_REDIS_SOCKET_TIMEOUT_SECONDS = _env_float(
        "CACHE_REDIS_SOCKET_TIMEOUT_SECONDS",
        0.5,
    )
    CACHE_DEFAULT_TTL_SECONDS = _env_int("CACHE_DEFAULT_TTL_SECONDS", 120)
    CACHE_JOBS_LIST_TTL_SECONDS = _env_int("CACHE_JOBS_LIST_TTL_SECONDS", 120)
    CACHE_COMPANY_SEARCH_TTL_SECONDS = _env_int("CACHE_COMPANY_SEARCH_TTL_SECONDS", 90)
    CACHE_STUDENT_SEARCH_TTL_SECONDS = _env_int("CACHE_STUDENT_SEARCH_TTL_SECONDS", 90)


class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False
    # os.environ.get() so that importing this module during development (where
    # DATABASE_URL is absent) does not crash.  validate_config() enforces this
    # value is present when FLASK_ENV=production.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    CELERY_BROKER_URL = os.environ.get(
        "CELERY_BROKER_URL",
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
    )
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND",
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
    )
    CELERY_TIMEZONE = os.environ.get("CELERY_TIMEZONE", "Asia/Kolkata")
    JOBS_DAILY_REMINDER_CRON = os.environ.get("JOBS_DAILY_REMINDER_CRON", "0 9 * * *")
    JOBS_TEST_MODE = False
    JOBS_DISABLE_IDEMPOTENCY = os.getenv("JOBS_DISABLE_IDEMPOTENCY", "false").lower() == "true"
    JOBS_MONTHLY_REPORT_CRON = os.environ.get("JOBS_MONTHLY_REPORT_CRON", "0 9 1 * *")
    JOBS_EXPORT_ARTIFACT_TTL_HOURS = _env_int("JOBS_EXPORT_ARTIFACT_TTL_HOURS", 24)
    JOBS_RETRY_LIMIT = _env_int("JOBS_RETRY_LIMIT", 3)
    JOBS_RETRY_BACKOFF_SECONDS = _env_int("JOBS_RETRY_BACKOFF_SECONDS", 60)
    JOBS_REMINDER_LOOKAHEAD_DAYS = _env_int("JOBS_REMINDER_LOOKAHEAD_DAYS", 3)
    JOBS_INTERVIEW_REMINDER_ENABLED = _env_bool("JOBS_INTERVIEW_REMINDER_ENABLED", False)
    JOBS_INTERVIEW_REMINDER_CRON = os.environ.get(
        "JOBS_INTERVIEW_REMINDER_CRON",
        "30 9 * * *",
    )
    JOBS_INTERVIEW_REMINDER_WINDOW_HOURS = _env_int(
        "JOBS_INTERVIEW_REMINDER_WINDOW_HOURS",
        24,
    )
    JOBS_REMINDER_CHANNELS = os.environ.get(
        "JOBS_REMINDER_CHANNELS",
        "email",
    )
    JOBS_INTERVIEW_REMINDER_CHANNELS = os.environ.get(
        "JOBS_INTERVIEW_REMINDER_CHANNELS",
        os.environ.get("JOBS_REMINDER_CHANNELS", "email"),
    )
    JOBS_WEBHOOK_URL = os.environ.get("JOBS_WEBHOOK_URL")
    JOBS_REPORT_CHANNELS = os.environ.get("JOBS_REPORT_CHANNELS", "email")
    JOBS_MONTHLY_REPORT_AUDIENCE = os.environ.get("JOBS_MONTHLY_REPORT_AUDIENCE", "admin")
    JOBS_MONTHLY_REPORT_FORMAT = os.environ.get("JOBS_MONTHLY_REPORT_FORMAT", "html")
    JOBS_EXPORT_ALERT_CHANNELS = os.environ.get("JOBS_EXPORT_ALERT_CHANNELS", "in_app,email")
    JOBS_COMPANY_EXPORT_ENABLED = _env_bool("JOBS_COMPANY_EXPORT_ENABLED", False)
    JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY = _env_bool(
        "JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY",
        False,
    )
    JOBS_FAILURE_ALERT_CHANNELS = os.environ.get(
        "JOBS_FAILURE_ALERT_CHANNELS",
        os.environ.get("JOBS_REPORT_CHANNELS", "email"),
    )
    JOBS_REPORT_OUTPUT_DIR = os.environ.get(
        "JOBS_REPORT_OUTPUT_DIR",
        os.path.join(_instance_path, "reports"),
    )
    JOBS_EXPORT_OUTPUT_DIR = os.environ.get(
        "JOBS_EXPORT_OUTPUT_DIR",
        os.path.join(_instance_path, "exports"),
    )
    JOBS_EAGER_EXECUTION = _env_bool("JOBS_EAGER_EXECUTION", False)
    MAIL_FROM_ADDRESS = os.environ.get("MAIL_FROM_ADDRESS", "noreply@recruitify.local")
    MAIL_SMTP_HOST = os.environ.get("MAIL_SMTP_HOST")
    MAIL_SMTP_PORT = _env_int("MAIL_SMTP_PORT", 587)
    MAIL_SMTP_USERNAME = os.environ.get("MAIL_SMTP_USERNAME")
    MAIL_SMTP_PASSWORD = os.environ.get("MAIL_SMTP_PASSWORD")
    MAIL_SMTP_USE_TLS = _env_bool("MAIL_SMTP_USE_TLS", True)
    MAIL_SMTP_USE_SSL = _env_bool("MAIL_SMTP_USE_SSL", False)
    MAIL_TIMEOUT_SECONDS = _env_int("MAIL_TIMEOUT_SECONDS", 10)
    MAIL_SIMULATE_WHEN_UNCONFIGURED = False
    ANALYTICS_LOOKBACK_MONTHS = _env_int("ANALYTICS_LOOKBACK_MONTHS", 6)
    CACHE_ENABLED = True
    CACHE_KEY_PREFIX = os.environ.get("CACHE_KEY_PREFIX", "recruitify")
    CACHE_REDIS_URL = os.environ.get(
        "CACHE_REDIS_URL",
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/2"),
    )
    CACHE_REDIS_CONNECT_TIMEOUT_SECONDS = _env_float(
        "CACHE_REDIS_CONNECT_TIMEOUT_SECONDS",
        0.5,
    )
    CACHE_REDIS_SOCKET_TIMEOUT_SECONDS = _env_float(
        "CACHE_REDIS_SOCKET_TIMEOUT_SECONDS",
        0.5,
    )
    CACHE_DEFAULT_TTL_SECONDS = _env_int("CACHE_DEFAULT_TTL_SECONDS", 120)
    CACHE_JOBS_LIST_TTL_SECONDS = _env_int("CACHE_JOBS_LIST_TTL_SECONDS", 120)
    CACHE_COMPANY_SEARCH_TTL_SECONDS = _env_int("CACHE_COMPANY_SEARCH_TTL_SECONDS", 90)
    CACHE_STUDENT_SEARCH_TTL_SECONDS = _env_int("CACHE_STUDENT_SEARCH_TTL_SECONDS", 90)


def validate_config(app) -> None:
    """Enforce required configuration after the active class has been applied.

    Called from create_app() immediately after app.config.from_object() so that
    validation is environment-specific and happens post-selection — never during
    module import.

    Development — requires:  SECRET_KEY, JWT_SECRET_KEY
    Production  — requires:  SECRET_KEY, JWT_SECRET_KEY, DATABASE_URL

    Raises RuntimeError with a complete list of every missing variable instead
    of allowing a raw KeyError to surface from an unrelated call site.
    """
    # 1. Determine environment strictly from Flask's active configuration (source of truth)
    # Production implies we are not running in debug or testing modes.
    is_production = not app.config.get("DEBUG", False) and not app.config.get("TESTING", False)

    missing = []

    # 2. Check standard security keys required in all environments
    if not app.config.get("SECRET_KEY"):
        missing.append("SECRET_KEY")
    if not app.config.get("JWT_SECRET_KEY"):
        missing.append("JWT_SECRET_KEY")

    # 3. In production, enforce that a real database URL was provided,
    # preventing silent fallbacks to ephemeral SQLite databases.
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if is_production and (not db_uri or db_uri.startswith("sqlite://")):
        missing.append("DATABASE_URL")

    if missing:
        env_label = "production" if is_production else "development"
        raise RuntimeError(
            f"[Recruitify] Missing or invalid configuration for {env_label} environment: "
            f"{', '.join(missing)}. "
            "Ensure these variables are present in backend/.env (or injected by the "
            "platform) before starting the application."
        )
