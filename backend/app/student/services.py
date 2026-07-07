"""Service layer for student dashboard, drive eligibility, and application operations."""

from datetime import datetime, timezone

from app.models import Application, PlacementOffer


def _coerce_utc(value):
    if not value:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalized_upper_set(values):
    if not isinstance(values, list):
        return set()
    return {
        str(item).strip().upper()
        for item in values
        if str(item).strip()
    }


def _normalized_int_set(values):
    if not isinstance(values, list):
        return set()

    normalized = set()
    for item in values:
        try:
            normalized.add(int(item))
        except (TypeError, ValueError):
            continue
    return normalized


def is_drive_open_for_student(drive):
    if not drive or drive.status != "approved":
        return False

    deadline = _coerce_utc(drive.application_deadline)
    if not deadline:
        return False

    return deadline >= datetime.now(timezone.utc)


def student_eligibility_for_drive(student, drive):
    reasons = []

    if not student:
        return False, ["Student profile not found"]

    if student.is_blacklisted:
        reasons.append("Student profile is restricted")

    if not student.profile_completed:
        reasons.append("Complete your profile first")

    student_branch = str(student.branch or "").strip().upper()
    student_year = student.year
    student_cgpa = student.cgpa

    allowed_branches = _normalized_upper_set(drive.eligible_branches)
    allowed_years = _normalized_int_set(drive.eligible_years)

    if allowed_branches and student_branch not in allowed_branches:
        reasons.append("Branch not eligible")

    if allowed_years and student_year not in allowed_years:
        reasons.append("Year not eligible")

    min_cgpa = float(drive.min_cgpa or 0)
    if student_cgpa is None or float(student_cgpa) < min_cgpa:
        reasons.append(f"Minimum CGPA is {min_cgpa:g}")

    return len(reasons) == 0, reasons


def get_student_dashboard_summary(student):
    application_query = Application.query.filter(
        Application.student_id == student.student_id
    )

    return {
        "applications_total": application_query.count(),
        "applied": application_query.filter(Application.status == "applied").count(),
        "shortlisted": application_query.filter(
            Application.status == "shortlisted"
        ).count(),
        "interviewed": application_query.filter(
            Application.status == "interviewed"
        ).count(),
        "selected": application_query.filter(Application.status == "selected").count(),
        "waitlisted": application_query.filter(
            Application.status == "waitlisted"
        ).count(),
        "rejected": application_query.filter(Application.status == "rejected").count(),
        "offers_released": PlacementOffer.query.filter(
            PlacementOffer.student_id == student.student_id,
            PlacementOffer.status == "offered",
        ).count(),
        "offers_accepted": PlacementOffer.query.filter(
            PlacementOffer.student_id == student.student_id,
            PlacementOffer.status == "accepted",
        ).count(),
        "offers_rejected": PlacementOffer.query.filter(
            PlacementOffer.student_id == student.student_id,
            PlacementOffer.status == "rejected",
        ).count(),
    }
