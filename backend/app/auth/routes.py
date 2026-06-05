"""Authentication routes using JWT."""

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.extensions import limiter
from app.cache import (
	CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH,
	CACHE_NAMESPACE_ADMIN_STUDENT_SEARCH,
	invalidate_api_cache_namespaces,
)
from app.models import (
	Application,
	Company,
	Interview,
	Notification,
	PlacementDrive,
	PlacementOffer,
	Student,
	User,
	db,
)

from .utils import role_required
from .validators import validate_email, validate_password, validate_required_fields

auth_bp = Blueprint("auth", __name__)


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


def _current_user_id():
	"""Extract the authenticated user id from JWT identity."""
	identity = get_jwt_identity()
	raw_user_id = identity.get("user_id") if isinstance(identity, dict) else identity
	try:
		return int(raw_user_id)
	except (TypeError, ValueError):
		return None


def _create_admin_notifications(title, message, sender_id=None, resource_type=None, resource_id=None):
	admin_users = User.query.filter(
		User.role == "admin",
		User.is_active.is_(True),
	).all()

	for admin_user in admin_users:
		db.session.add(
			Notification(
				recipient_id=admin_user.user_id,
				sender_id=sender_id,
				notification_type="in_app",
				title=(title or "Update").strip()[:200],
				message=(message or "").strip() or "You have a new update.",
				related_resource_type=(resource_type or "system").strip()[:100],
				related_resource_id=resource_id,
				delivery_status="sent",
			)
		)

def _invalidate_admin_cache(*namespaces):
	cache = current_app.extensions.get("redis_cache")
	invalidate_api_cache_namespaces(cache, *namespaces)

@auth_bp.post("/register/student")
@limiter.limit("5 per hour")
def register_student():
	data = _normalized_json_payload()
	required = ["username", "email", "password"]
	missing_message = validate_required_fields(data, required)
	if missing_message:
		return _json_error(missing_message, 400)

	email_error = validate_email(data.get("email", ""))
	if email_error:
		return _json_error(email_error, 400)

	password_error = validate_password(data.get("password", ""))
	if password_error:
		return _json_error(password_error, 400)

	email = data["email"].lower()
	username = data["username"]
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

		student = Student(user_id=user.user_id)
		db.session.add(student)
		db.session.commit()
	except IntegrityError:
		db.session.rollback()
		return _json_error("Registration failed due to duplicate or invalid data", 409)
	except Exception:
		db.session.rollback()
		return _json_error("Unable to register student", 500)

	_invalidate_admin_cache(CACHE_NAMESPACE_ADMIN_STUDENT_SEARCH)

	return (
		jsonify(
			{
				"success": True,
				"data": {
					"message": "Student registered successfully",
					"user_id": user.user_id,
					"role": user.role,
					"profile_completed": False,
				},
			}
		),
		201,
	)


@auth_bp.post("/register/company")
@limiter.limit("3 per hour")
def register_company():
	data = _normalized_json_payload()
	required = [
		"username",
		"email",
		"password",
		"company_name",
		"industry",
		"hr_contact_name",
		"hr_contact_email",
		"hr_contact_phone",
	]
	missing_message = validate_required_fields(data, required)
	if missing_message:
		return _json_error(missing_message, 400)

	email_error = validate_email(data.get("email", ""))
	if email_error:
		return _json_error(email_error, 400)

	hr_email_error = validate_email(data.get("hr_contact_email", ""))
	if hr_email_error:
		return _json_error("Invalid HR contact email format", 400)

	password_error = validate_password(data.get("password", ""))
	if password_error:
		return _json_error(password_error, 400)

	email = data["email"].lower()
	username = data["username"]

	duplicate_user = User.query.filter(
		(User.email == email) | (User.username == username)
	).first()
	if duplicate_user:
		if duplicate_user.email == email:
			return _json_error("Email is already registered", 409)
		return _json_error("Username is already taken", 409)

	duplicate_company = Company.query.filter(
		(Company.company_name == data["company_name"])
		| (Company.hr_contact_email == data["hr_contact_email"].lower())
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
			company_name=data["company_name"],
			industry=data["industry"],
			hr_contact_name=data["hr_contact_name"],
			hr_contact_email=data["hr_contact_email"].lower(),
			hr_contact_phone=data["hr_contact_phone"],
			approval_status="pending",
		)
		db.session.add(company)
		db.session.flush()

		_create_admin_notifications(
			"New Company Registration",
			f"{company.company_name} registered and is awaiting approval.",
			sender_id=user.user_id,
			resource_type="company",
			resource_id=company.company_id,
		)
		db.session.commit()
	except IntegrityError:
		db.session.rollback()
		return _json_error("Registration failed due to duplicate or invalid data", 409)
	except Exception:
		db.session.rollback()
		return _json_error("Unable to register company", 500)

	_invalidate_admin_cache(CACHE_NAMESPACE_ADMIN_COMPANY_SEARCH)

	return (
		jsonify(
			{
				"message": "Waiting for admin approval",
				"data": {"user_id": user.user_id, "role": user.role},
			}
		),
		201,
	)


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
	data = _normalized_json_payload()
	required = ["email", "password"]
	missing_message = validate_required_fields(data, required)
	if missing_message:
		return _json_error(missing_message, 400)

	email_error = validate_email(data.get("email", ""))
	if email_error:
		return _json_error(email_error, 400)

	password_error = validate_password(data.get("password", ""))
	if password_error:
		return _json_error(password_error, 400)

	email = data["email"].lower()
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
				"message": "Login successful",
				"data": {
					"token": token,
					"role": user.role,
					"user_id": user.user_id,
				},
			}
		),
		200,
	)


@auth_bp.get("/me")
@jwt_required()
def me():
	identity = get_jwt_identity()
	try:
		user_id = int(identity)
	except (TypeError, ValueError):
		return _json_error("Invalid token identity", 401)

	if not user_id:
		return _json_error("Invalid token identity", 401)

	user = db.session.get(User, user_id)
	if not user:
		return _json_error("User not found", 404)

	payload = {
		"user_id": user.user_id,
		"username": user.username,
		"email": user.email,
		"role": user.role,
		"is_active": user.is_active,
	}
	return jsonify({"message": "User profile fetched successfully", "data": payload}), 200


@auth_bp.get("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
	identity = get_jwt_identity()
	user = identity if isinstance(identity, dict) else {"user_id": identity}
	return jsonify({"message": "Welcome Admin", "data": {"user": user}}), 200


@auth_bp.get("/student/dashboard")
@role_required("student")
def student_dashboard():
	identity = get_jwt_identity()
	user_id = identity if not isinstance(identity, dict) else identity.get("user_id")
	student = Student.query.filter_by(user_id=user_id).first()
	if not student:
		return _json_error("Student profile not found", 404)
	if not student.profile_completed:
		return _json_error("Complete your profile first", 403)

	user = identity if isinstance(identity, dict) else {"user_id": identity}
	return jsonify({"success": True, "data": {"message": "Welcome Student", "user": user}}), 200


@auth_bp.get("/company/dashboard")
@role_required("company")
def company_dashboard():
	user_id = _current_user_id()
	if not user_id:
		return _json_error("Invalid token identity", 401)

	user = db.session.get(User, user_id)
	if not user:
		return _json_error("User not found", 404)

	company = Company.query.filter_by(user_id=user_id).first()
	if not company:
		return _json_error("Company profile not found", 404)

	active_drives = PlacementDrive.query.filter(
		PlacementDrive.company_id == company.company_id,
		PlacementDrive.status.in_(("pending", "approved")),
	).count()

	applications_base = db.session.query(Application).join(
		PlacementDrive, Application.drive_id == PlacementDrive.drive_id
	).filter(PlacementDrive.company_id == company.company_id)

	applications_received = applications_base.count()
	screening_count = applications_base.filter(
		Application.status.in_(("applied", "shortlisted", "waitlisted"))
	).count()
	interviews_scheduled = Interview.query.filter_by(company_id=company.company_id).count()
	offers_released = PlacementOffer.query.filter_by(
		company_id=company.company_id,
		status="offered",
	).count()
	offers_accepted = PlacementOffer.query.filter_by(
		company_id=company.company_id,
		status="accepted",
	).count()
	offers_rejected = PlacementOffer.query.filter_by(
		company_id=company.company_id,
		status="rejected",
	).count()
	pending_drives = PlacementDrive.query.filter_by(
		company_id=company.company_id, status="pending"
	).count()
	unread_notifications = Notification.query.filter(
		Notification.recipient_id == user_id,
		Notification.notification_type == "in_app",
		Notification.is_read.is_(False),
	).count()

	pipeline = [
		{"id": "pending", "label": "Pending Approval", "count": pending_drives},
		{"id": "screening", "label": "Application Screening", "count": screening_count},
		{
			"id": "interviews",
			"label": "Interviews",
			"count": interviews_scheduled,
		},
		{"id": "offers", "label": "Offers", "count": offers_released},
	]

	recent_rows = (
		db.session.query(Application, Student, User, PlacementDrive)
		.join(PlacementDrive, Application.drive_id == PlacementDrive.drive_id)
		.join(Student, Application.student_id == Student.student_id)
		.join(User, Student.user_id == User.user_id)
		.filter(PlacementDrive.company_id == company.company_id)
		.order_by(Application.updated_at.desc(), Application.application_id.desc())
		.limit(8)
		.all()
	)

	recent_applicants = [
		{
			"application_id": application.application_id,
			"student_name": student_user.username,
			"job_title": drive.job_title,
			"status": application.status,
			"updated_at": application.updated_at.isoformat()
			if application.updated_at
			else None,
		}
		for application, _student, student_user, drive in recent_rows
	]

	return (
		jsonify(
			{
				"message": "Company dashboard loaded successfully",
				"data": {
					"user": {
						"user_id": user.user_id,
						"username": user.username,
						"email": user.email,
						"company_id": company.company_id,
						"company_name": company.company_name,
					},
					"summary": {
						"active_drives": active_drives,
						"applications_received": applications_received,
						"interviews_scheduled": interviews_scheduled,
						"offers_released": offers_released,
						"offers_accepted": offers_accepted,
						"offers_rejected": offers_rejected,
						"unread_notifications": unread_notifications,
					},
					"pipeline": pipeline,
					"recent_applicants": recent_applicants,
				},
			}
		),
		200,
	)


__all__ = ["auth_bp"]
