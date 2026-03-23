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

    # =====================================================================
    # Register Blueprints
    # =====================================================================
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from app.student import student_bp
    app.register_blueprint(student_bp, url_prefix="/student")

    # =====================================================================
    # Health Check
    # =====================================================================
    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200

    return app


__all__ = ["create_app", "db"]