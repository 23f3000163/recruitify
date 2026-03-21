"""Utility helpers for auth and authorization."""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required


def role_required(role):
    """
    Restrict endpoint access to a specific user role using JWT claims.

    This decorator:
    - Verifies JWT token
    - Extracts role from token claims
    - Compares with required role
    """

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            # ✅ Get full JWT payload (claims)
            claims = get_jwt()

            # ✅ Extract role from claims
            current_role = claims.get("role")

            # ❌ If role mismatch → block access
            if current_role != role:
                return jsonify({"error": "Forbidden: insufficient permissions"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["role_required"]