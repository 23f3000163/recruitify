"""Shared status normalization and transition rules for placement applications."""

ATS_STATUSES = {
    "applied",
    "shortlisted",
    "interview",
    "offered",
    "rejected",
    "placed",
}

STATUS_ALIASES = {
    "interviewed": "interview",
    "selected": "offered",
    "waitlisted": "shortlisted",
}

ATS_TO_LEGACY_STATUS = {
    "applied": "applied",
    "shortlisted": "shortlisted",
    "interview": "interviewed",
    "offered": "selected",
    "rejected": "rejected",
    "placed": "selected",
}

ATS_TRANSITIONS = {
    "applied": {"shortlisted", "rejected"},
    "shortlisted": {"interview", "rejected"},
    "interview": {"offered", "rejected"},
    "offered": {"placed", "rejected"},
    "rejected": set(),
    "placed": set(),
}


def normalize_status_input(raw_status):
    normalized = str(raw_status or "").strip().lower()
    normalized = STATUS_ALIASES.get(normalized, normalized)
    if normalized not in ATS_STATUSES:
        return None
    return normalized


def status_label(status):
    labels = {
        "applied": "Applied",
        "shortlisted": "Shortlisted",
        "interview": "Interview",
        "offered": "Offered",
        "rejected": "Rejected",
        "placed": "Placed",
    }
    normalized = str(status or "").strip().lower()
    return labels.get(normalized, normalized.capitalize() if normalized else "Updated")


def application_ats_status(application):
    legacy_status = str(getattr(application, "status", "") or "").strip().lower()

    if legacy_status == "selected":
        offer = getattr(application, "placement_offer", None)
        if offer:
            offer_status = str(getattr(offer, "status", "") or "").strip().lower()
            if offer_status == "accepted":
                return "placed"
            if offer_status == "rejected":
                return "rejected"
        return "offered"

    if legacy_status == "interviewed":
        return "interview"

    if legacy_status == "waitlisted":
        return "shortlisted"

    if legacy_status in {"applied", "shortlisted", "rejected"}:
        return legacy_status

    return "applied"
