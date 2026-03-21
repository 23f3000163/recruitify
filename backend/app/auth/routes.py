"""Authentication routes using JWT."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.models import Admin, Company, Student, User, db

from .utils import role_required

auth_bp = Blueprint("auth", __name__)


def _json_error(message, status_code=400):
	"""Return a consistent JSON error payload."""
	return jsonify({"error": message}), status_code


def _require_json_fields(payload, required_fields):
	"""Validate required JSON fields and return missing field names."""
	missing = [
		field
		for field in required_fields
		if payload.get(field) is None
		or (isinstance(payload.get(field), str) and not payload.get(field).strip())
	]
	return missing

@auth_bp.post("/register/student")
def register_student():
	data = request.get_json(silent=True) or {}
	required = ["username", "email", "password"]
	missing = _require_json_fields(data, required)
	if missing:
		return _json_error(f"Missing required fields: {', '.join(missing)}", 400)

	email = data["email"].strip().lower()
	username = data["username"].strip()
	password = data["password"]

	duplicate_user = User.query.filter(
		(User.email == email) | (User.username == username)
	).first()
	if duplicate_user:
		if duplicate_user.email == email:
			return _json_error("Email is already registered", 409)
		return _json_error("Username is already taken", 409)

	user = User(username=username, email=email, role="student", is_active=True)
	user.set_password(password)

	try:
		db.session.add(user)
		db.session.flush()

		# Student requires several non-null profile fields in the current schema.
		student = Student(
			user_id=user.user_id,
			roll_number=f"STU-{user.user_id}",
			college_name="Not Provided",
			branch="OTHER",
			year=1,
			cgpa=0.0,
		)
		db.session.add(student)
		db.session.commit()
	except IntegrityError:
		db.session.rollback()
		return _json_error("Registration failed due to duplicate or invalid data", 409)
	except Exception:
		db.session.rollback()
		return _json_error("Unable to register student", 500)

	return jsonify({"message": "Student registered successfully"}), 201


@auth_bp.post("/register/company")
def register_company():
	data = request.get_json(silent=True) or {}
	required = [
		"username",
		"email",
		"password",
		"company_name",
		"hr_contact_name",
		"hr_contact_email",
		"hr_contact_phone",
	]
	missing = _require_json_fields(data, required)
	if missing:
		return _json_error(f"Missing required fields: {', '.join(missing)}", 400)

	email = data["email"].strip().lower()
	username = data["username"].strip()

	duplicate_user = User.query.filter(
		(User.email == email) | (User.username == username)
	).first()
	if duplicate_user:
		if duplicate_user.email == email:
			return _json_error("Email is already registered", 409)
		return _json_error("Username is already taken", 409)

	duplicate_company = Company.query.filter(
		(Company.company_name == data["company_name"].strip())
		| (Company.hr_contact_email == data["hr_contact_email"].strip().lower())
	).first()
	if duplicate_company:
		return _json_error("Company name or HR contact email already exists", 409)

	user = User(username=username, email=email, role="company", is_active=True)
	user.set_password(data["password"])

	try:
		db.session.add(user)
		db.session.flush()

		company = Company(
			user_id=user.user_id,
			company_name=data["company_name"].strip(),
			hr_contact_name=data["hr_contact_name"].strip(),
			hr_contact_email=data["hr_contact_email"].strip().lower(),
			hr_contact_phone=data["hr_contact_phone"].strip(),
			approval_status="pending",
		)
		db.session.add(company)
		db.session.commit()
	except IntegrityError:
		db.session.rollback()
		return _json_error("Registration failed due to duplicate or invalid data", 409)
	except Exception:
		db.session.rollback()
		return _json_error("Unable to register company", 500)

	return jsonify({"message": "Waiting for admin approval"}), 201


@auth_bp.post("/login")
def login():
	data = request.get_json(silent=True) or {}
	required = ["email", "password"]
	missing = _require_json_fields(data, required)
	if missing:
		return _json_error(f"Missing required fields: {', '.join(missing)}", 400)

	email = data["email"].strip().lower()
	password = data["password"]

	user = User.query.filter_by(email=email).first()

	if not user or not user.check_password(password):
		return _json_error("Invalid email or password", 401)

	if not user.is_active:
		return _json_error("User account is inactive", 403)

	if user.role == "company":
		company_profile = Company.query.filter_by(user_id=user.user_id).first()
		if not company_profile:
			return _json_error("Company profile not found", 403)
		if company_profile.approval_status != "approved":
			return _json_error("Company account is pending admin approval", 403)

	token = create_access_token(
        identity=str(user.user_id),   # MUST be string
        additional_claims={"role": user.role}
)

	user.last_login = datetime.now(timezone.utc)
	db.session.commit()

	return (
		jsonify(
			{
				"token": token,
				"role": user.role,
				"user_id": user.user_id,
			}
		),
		200,
	)


@auth_bp.get("/me")
@jwt_required()
def me():
	user_id = int(get_jwt_identity())
	if not user_id:
		return _json_error("Invalid token identity", 401)

	user = User.query.get(user_id)
	if not user:
		return _json_error("User not found", 404)

	payload = {
		"user_id": user.user_id,
		"username": user.username,
		"email": user.email,
		"role": user.role,
		"is_active": user.is_active,
	}
	return jsonify(payload), 200


@auth_bp.get("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
	admins_count = Admin.query.count()
	return jsonify({"message": "Welcome Admin", "total_admins": admins_count}), 200


@auth_bp.get("/student/dashboard")
@role_required("student")
def student_dashboard():
	identity = get_jwt_identity() or {}
	return jsonify({"message": "Welcome Student", "identity": identity}), 200


@auth_bp.get("/company/dashboard")
@role_required("company")
def company_dashboard():
	identity = get_jwt_identity() or {}
	return jsonify({"message": "Welcome Company", "identity": identity}), 200


__all__ = ["auth_bp"]
