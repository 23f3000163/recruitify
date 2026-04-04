import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .models import db


def create_app(config_object=None):
    """Application factory for the Recruitify backend."""

    app = Flask(__name__, instance_relative_config=True)

    # =====================================================================
    # Database Configuration
    # =====================================================================
    default_sqlite_path = os.path.join(app.instance_path, "recruitify.db")

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{default_sqlite_path}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        # 🔐 JWT Configuration
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me"),
        JWT_ACCESS_TOKEN_EXPIRES=3600,  # 1 hour
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
        except Exception as exc:
            app.logger.warning("Schema update check failed: %s", exc)

    # =====================================================================
    # Initialize Extensions
    # =====================================================================
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return jsonify({"success": False, "error": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return jsonify({"success": False, "error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return jsonify({"success": False, "error": "Missing authorization token"}), 401

    # =====================================================================
    # Register Models (important for SQLAlchemy)
    # =====================================================================
    from . import models  # noqa: F401

    with app.app_context():
        _ensure_schema_updates()

    # =====================================================================
    # Register Blueprints
    # =====================================================================
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

    # =====================================================================
    # Health Check
    # =====================================================================
    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    return app


__all__ = ["create_app", "db"]