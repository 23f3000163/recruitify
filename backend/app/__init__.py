import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .extensions import limiter, migrate
from .models import db


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


def create_app(config_object=None):
    """Application factory for the Recruitify backend."""

    app = Flask(__name__, instance_relative_config=True)

    # Database Configuration
  
    default_sqlite_path = os.path.join(app.instance_path, "recruitify.db")

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{default_sqlite_path}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        #  JWT Configuration
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me"),
        JWT_ACCESS_TOKEN_EXPIRES=3600,  # 1 hour

        #  Background Jobs (Celery + Redis) configuration contracts
        CELERY_BROKER_URL=os.environ.get(
            "CELERY_BROKER_URL",
            os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
        ),
        CELERY_RESULT_BACKEND=os.environ.get(
            "CELERY_RESULT_BACKEND",
            os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
        ),
        CELERY_TIMEZONE=os.environ.get("CELERY_TIMEZONE", "Asia/Kolkata"),
        JOBS_DAILY_REMINDER_CRON=os.environ.get("JOBS_DAILY_REMINDER_CRON", "0 9 * * *"),
        JOBS_TEST_MODE=os.getenv("JOBS_TEST_MODE", "false").lower() == "true",
        JOBS_DISABLE_IDEMPOTENCY = os.getenv("JOBS_DISABLE_IDEMPOTENCY", "false").lower() == "true",
        JOBS_MONTHLY_REPORT_CRON=os.environ.get("JOBS_MONTHLY_REPORT_CRON", "0 9 1 * *"),
        JOBS_EXPORT_ARTIFACT_TTL_HOURS=_env_int("JOBS_EXPORT_ARTIFACT_TTL_HOURS", 24),
        JOBS_RETRY_LIMIT=_env_int("JOBS_RETRY_LIMIT", 3),
        JOBS_RETRY_BACKOFF_SECONDS=_env_int("JOBS_RETRY_BACKOFF_SECONDS", 60),
        JOBS_REMINDER_LOOKAHEAD_DAYS=_env_int("JOBS_REMINDER_LOOKAHEAD_DAYS", 3),
        JOBS_INTERVIEW_REMINDER_ENABLED=_env_bool("JOBS_INTERVIEW_REMINDER_ENABLED", False),
        JOBS_INTERVIEW_REMINDER_CRON=os.environ.get(
            "JOBS_INTERVIEW_REMINDER_CRON",
            "30 9 * * *",
        ),
        JOBS_INTERVIEW_REMINDER_WINDOW_HOURS=_env_int(
            "JOBS_INTERVIEW_REMINDER_WINDOW_HOURS",
            24,
        ),
        JOBS_REMINDER_CHANNELS=os.environ.get(
            "JOBS_REMINDER_CHANNELS",
            "email",
        ),
        JOBS_INTERVIEW_REMINDER_CHANNELS=os.environ.get(
            "JOBS_INTERVIEW_REMINDER_CHANNELS",
            os.environ.get("JOBS_REMINDER_CHANNELS", "email"),
        ),
        JOBS_WEBHOOK_URL=os.environ.get("JOBS_WEBHOOK_URL"),
        JOBS_REPORT_CHANNELS=os.environ.get("JOBS_REPORT_CHANNELS", "email"),
        JOBS_MONTHLY_REPORT_AUDIENCE=os.environ.get("JOBS_MONTHLY_REPORT_AUDIENCE", "admin"),
        JOBS_MONTHLY_REPORT_FORMAT=os.environ.get("JOBS_MONTHLY_REPORT_FORMAT", "html"),
        JOBS_EXPORT_ALERT_CHANNELS=os.environ.get("JOBS_EXPORT_ALERT_CHANNELS", "in_app,email"),
        JOBS_COMPANY_EXPORT_ENABLED=_env_bool("JOBS_COMPANY_EXPORT_ENABLED", False),
        JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY=_env_bool(
            "JOBS_EXPORT_ALLOW_PLACEMENT_HISTORY",
            False,
        ),
        JOBS_FAILURE_ALERT_CHANNELS=os.environ.get(
            "JOBS_FAILURE_ALERT_CHANNELS",
            os.environ.get("JOBS_REPORT_CHANNELS", "email"),
        ),
        JOBS_REPORT_OUTPUT_DIR=os.environ.get(
            "JOBS_REPORT_OUTPUT_DIR",
            os.path.join(app.instance_path, "reports"),
        ),
        JOBS_EXPORT_OUTPUT_DIR=os.environ.get(
            "JOBS_EXPORT_OUTPUT_DIR",
            os.path.join(app.instance_path, "exports"),
        ),
        JOBS_EAGER_EXECUTION=_env_bool("JOBS_EAGER_EXECUTION", False),

        #  SMTP mail delivery (used by background job email notifications)
        MAIL_FROM_ADDRESS=os.environ.get("MAIL_FROM_ADDRESS", "noreply@recruitify.local"),
        MAIL_SMTP_HOST=os.environ.get("MAIL_SMTP_HOST"),
        MAIL_SMTP_PORT=_env_int("MAIL_SMTP_PORT", 587),
        MAIL_SMTP_USERNAME=os.environ.get("MAIL_SMTP_USERNAME"),
        MAIL_SMTP_PASSWORD=os.environ.get("MAIL_SMTP_PASSWORD"),
        MAIL_SMTP_USE_TLS=_env_bool("MAIL_SMTP_USE_TLS", True),
        MAIL_SMTP_USE_SSL=_env_bool("MAIL_SMTP_USE_SSL", False),
        MAIL_TIMEOUT_SECONDS=_env_int("MAIL_TIMEOUT_SECONDS", 10),
        MAIL_SIMULATE_WHEN_UNCONFIGURED=_env_bool("MAIL_SIMULATE_WHEN_UNCONFIGURED", False),

        #  Analytics API defaults
        ANALYTICS_LOOKBACK_MONTHS=_env_int("ANALYTICS_LOOKBACK_MONTHS", 6),

        #  API Response Cache (Redis) configuration contracts
        CACHE_ENABLED=_env_bool("CACHE_ENABLED", True),
        CACHE_KEY_PREFIX=os.environ.get("CACHE_KEY_PREFIX", "recruitify"),
        CACHE_REDIS_URL=os.environ.get(
            "CACHE_REDIS_URL",
            os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/2"),
        ),
        CACHE_REDIS_CONNECT_TIMEOUT_SECONDS=_env_float(
            "CACHE_REDIS_CONNECT_TIMEOUT_SECONDS",
            0.5,
        ),
        CACHE_REDIS_SOCKET_TIMEOUT_SECONDS=_env_float(
            "CACHE_REDIS_SOCKET_TIMEOUT_SECONDS",
            0.5,
        ),
        CACHE_DEFAULT_TTL_SECONDS=_env_int("CACHE_DEFAULT_TTL_SECONDS", 120),
        CACHE_JOBS_LIST_TTL_SECONDS=_env_int("CACHE_JOBS_LIST_TTL_SECONDS", 120),
        CACHE_COMPANY_SEARCH_TTL_SECONDS=_env_int("CACHE_COMPANY_SEARCH_TTL_SECONDS", 90),
        CACHE_STUDENT_SEARCH_TTL_SECONDS=_env_int("CACHE_STUDENT_SEARCH_TTL_SECONDS", 90),
    )

    # Optional external config override
    if config_object is not None:
        if isinstance(config_object, dict):
            app.config.update(config_object)
        else:
            app.config.from_object(config_object)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize Extensions

    db.init_app(app)
    # Bind Flask-Migrate to this app and the db instance.
    # render_as_batch=True is required for SQLite ALTER TABLE support (batch mode
    # recreates the table instead of issuing unsupported ALTER statements).
    # PostgreSQL ignores this flag; it has no effect on production behaviour.
    migrate.init_app(app, db, render_as_batch=True)
    limiter.init_app(app)

    allowed_origins = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173"
    ).split(",")

    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True
    )

    jwt = JWTManager(app)

    from .cache import init_cache

    init_cache(app)

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return jsonify({"success": False, "error": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return jsonify({"success": False, "error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return jsonify({"success": False, "error": "Missing authorization token"}), 401

    
    # Register Models (important for SQLAlchemy)
    # All model classes must be imported before any database operation so that
    # SQLAlchemy's metadata is fully populated. Flask-Migrate also depends on
    # this import to discover every table during migration generation.
    from . import models  # noqa: F401

    
    # Register Blueprints
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from app.student import student_bp
    app.register_blueprint(student_bp, url_prefix="/student")

    from app.company import company_bp
    app.register_blueprint(company_bp, url_prefix="/company")

    from app.applications import applications_bp
    app.register_blueprint(applications_bp)

    from app.jobs import jobs_bp
    app.register_blueprint(jobs_bp)

    from app.notifications import notifications_bp
    app.register_blueprint(notifications_bp)

    try:
        from app.jobs.celery_app import init_celery

        init_celery(app)
    except ModuleNotFoundError as exc:
        missing = str(getattr(exc, "name", ""))
        if missing in {"celery", "redis"}:
            app.logger.warning(
                "Background job extensions unavailable because '%s' is not installed.",
                missing,
            )
        else:
            raise

   
    # Health Check
   
    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    return app


__all__ = ["create_app", "db"]  