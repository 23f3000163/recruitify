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
            claims = get_jwt()
            current_role = claims.get("role")
            if current_role != role:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Forbidden: insufficient permissions",
                        }
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["role_required"]