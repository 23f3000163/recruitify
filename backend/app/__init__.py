import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .extensions import limiter
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

    def _ensure_schema_updates():
        """Apply lightweight non-destructive schema updates for local SQLite."""
        database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if not database_uri.startswith("sqlite"):
            return

        try:
            with db.engine.begin() as conn:
                table_exists = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='company'"
                ).fetchone()
                if not table_exists:
                    return

                columns = {
                    row[1]
                    for row in conn.exec_driver_sql("PRAGMA table_info(company)").fetchall()
                }
                if "industry" not in columns:
                    conn.exec_driver_sql("ALTER TABLE company ADD COLUMN industry VARCHAR(120)")
                if "location" not in columns:
                    conn.exec_driver_sql("ALTER TABLE company ADD COLUMN location VARCHAR(160)")

                student_table_exists = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='student'"
                ).fetchone()
                if student_table_exists:
                    student_columns = {
                        row[1]
                        for row in conn.exec_driver_sql("PRAGMA table_info(student)").fetchall()
                    }
                    if "skills" not in student_columns:
                        conn.exec_driver_sql("ALTER TABLE student ADD COLUMN skills TEXT")
                    if "experience_summary" not in student_columns:
                        conn.exec_driver_sql(
                            "ALTER TABLE student ADD COLUMN experience_summary TEXT"
                        )

                drive_table_exists = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='placement_drive'"
                ).fetchone()
                if drive_table_exists:
                    drive_columns = {
                        row[1]
                        for row in conn.exec_driver_sql(
                            "PRAGMA table_info(placement_drive)"
                        ).fetchall()
                    }
                    if "experience_required" not in drive_columns:
                        conn.exec_driver_sql(
                            "ALTER TABLE placement_drive ADD COLUMN experience_required VARCHAR(120)"
                        )
                    if "benefits" not in drive_columns:
                        conn.exec_driver_sql(
                            "ALTER TABLE placement_drive ADD COLUMN benefits TEXT"
                        )

                activity_table_exists = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log'"
                ).fetchone()
                if activity_table_exists:
                    activity_columns = {
                        row[1]
                        for row in conn.exec_driver_sql("PRAGMA table_info(activity_log)").fetchall()
                    }
                    if "target" not in activity_columns:
                        conn.exec_driver_sql(
                            "ALTER TABLE activity_log ADD COLUMN target VARCHAR(255)"
                        )
                    if "status" not in activity_columns:
                        conn.exec_driver_sql(
                            "ALTER TABLE activity_log ADD COLUMN status VARCHAR(20) DEFAULT 'info'"
                        )
                    conn.exec_driver_sql(
                        "UPDATE activity_log SET status='info' WHERE status IS NULL OR TRIM(status) = ''"
                    )

                notification_table_exists = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='notification'"
                ).fetchone()
                if notification_table_exists:
                    conn.exec_driver_sql(
                        "CREATE INDEX IF NOT EXISTS ix_notification_recipient_type_read_created "
                        "ON notification (recipient_id, notification_type, is_read, created_at)"
                    )
                    conn.exec_driver_sql(
                        "CREATE INDEX IF NOT EXISTS ix_notification_recipient_resource "
                        "ON notification (recipient_id, notification_type, related_resource_type, related_resource_id)"
                    )

            from .models import BackgroundJob, ExportArtifact, Notification

            db.metadata.create_all(
                bind=db.engine,
                tables=[
                    BackgroundJob.__table__,
                    ExportArtifact.__table__,
                    Notification.__table__,
                ],
                checkfirst=True,
            )
        except Exception as exc:
            app.logger.warning("Schema update check failed: %s", exc)

    
    # Initialize Extensions

    db.init_app(app)
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
    
    from . import models  # noqa: F401

    with app.app_context():
        _ensure_schema_updates()

    
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