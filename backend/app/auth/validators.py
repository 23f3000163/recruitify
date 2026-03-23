"""Reusable input validation helpers for auth routes."""

import re


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_email(email):
	"""Validate email presence and format."""
	email = (email or "").strip().lower()
	if not email:
		return "Email is required"
	if not EMAIL_REGEX.match(email):
		return "Invalid email format"
	return None


def validate_password(password):
	"""Validate password strength requirements."""
	if not password:
		return "Password is required"
	if len(password) < 6:
		return "Password must be at least 6 characters long"
	if not any(char.isalpha() for char in password):
		return "Password must contain at least one letter"
	if not any(char.isdigit() for char in password):
		return "Password must contain at least one number"
	return None


def validate_required_fields(data, fields):
	"""Return a formatted missing fields message, or None if valid."""
	missing = [
		field
		for field in fields
		if data.get(field) is None
		or (isinstance(data.get(field), str) and not data.get(field).strip())
	]
	if missing:
		return f"Missing required fields: {', '.join(missing)}"
	return None


__all__ = ["validate_email", "validate_password", "validate_required_fields"]