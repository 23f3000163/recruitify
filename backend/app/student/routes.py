"""Student profile routes."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.auth.utils import role_required
from app.auth.validators import validate_required_fields
from app.models import Student, db

student_bp = Blueprint("student", __name__)

# ✅ Allowed ENUM values (MUST match your DB)
VALID_BRANCHES = {"CSE", "ECE", "MECH", "OTHER"}

# ✅ Mapping user input → enum
BRANCH_MAP = {
    "cse": "CSE",
    "computer science": "CSE",
    "ece": "ECE",
    "electronics": "ECE",
    "mech": "MECH",
    "mechanical": "MECH",
    "other": "OTHER",
}


def _json_error(message, status_code=400):
    """Return a consistent JSON error payload."""
    return jsonify({"success": False, "error": message}), status_code


def _normalized_json_payload():
    """Return request JSON with surrounding whitespace trimmed from string values."""
    data = request.get_json(silent=True) or {}
    return {
        key: value.strip() if isinstance(value, str) else value
        for key, value in data.items()
    }


def _validate_student_profile_payload(data):
    """Validate required student profile fields and value ranges."""
    required_fields = ["college_name", "branch", "year", "cgpa", "roll_number"]
    missing_message = validate_required_fields(data, required_fields)
    if missing_message:
        return missing_message, None, None

    try:
        year = int(data.get("year"))
    except (TypeError, ValueError):
        return "Year must be a valid integer", None, None
    if year <= 0:
        return "Year must be greater than 0", None, None

    try:
        cgpa = float(data.get("cgpa"))
    except (TypeError, ValueError):
        return "CGPA must be a valid number", None, None
    if cgpa < 0 or cgpa > 10:
        return "CGPA must be between 0 and 10", None, None

    return None, year, cgpa


@student_bp.put("/profile")
@role_required("student")
def update_student_profile():
    """Complete or update student profile after initial registration."""
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return _json_error("Invalid token identity", 401)

    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return _json_error("Student profile not found", 404)

    data = _normalized_json_payload()
    validation_error, year, cgpa = _validate_student_profile_payload(data)
    if validation_error:
        return _json_error(validation_error, 400)

    student.college_name = data["college_name"]
    student.branch = data["branch"]
    student.year = year
    student.cgpa = cgpa
    student.roll_number = data["roll_number"]
    student.profile_completed = True

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to update student profile", 500)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "message": "Student profile updated successfully",
                    "student": student.to_dict(),
                },
            }
        ),
        200,
    )


__all__ = ["student_bp"]
