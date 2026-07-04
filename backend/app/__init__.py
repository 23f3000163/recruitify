import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import DevelopmentConfig, ProductionConfig, validate_config

from .extensions import limiter, migrate
from .models import db


def create_app(config_object=None):
    """Application factory for the Recruitify backend."""

    app = Flask(__name__, instance_relative_config=True)

    _flask_env = os.environ.get("FLASK_ENV", "development")
    _config_class = (
        ProductionConfig if _flask_env == "production"
        else DevelopmentConfig
    )
    app.config.from_object(_config_class)

    # Optional external config override
    if config_object is not None:
        if isinstance(config_object, dict):
            app.config.update(config_object)
        else:
            app.config.from_object(config_object)

    # Validate configuration AFTER it has been fully applied and BEFORE any
    # extension is initialized.  Raises RuntimeError with a clear message for
    # every missing required variable.
    validate_config(app)

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

    allowed_origins = app.config.get(
        "CORS_ORIGINS",
        ["http://localhost:5173"]
    )

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
