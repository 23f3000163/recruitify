"""Shared notification APIs used across roles."""

from datetime import datetime, timedelta, timezone
from math import ceil

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from app.auth.utils import get_current_user_id
from app.models import Notification, User, db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

ALLOWED_READ_FILTERS = {"all", "true", "false"}
ALLOWED_NOTIFICATION_TYPES = {"in_app", "email", "sms"}
MAX_LIMIT = 100


def _json_error(message, status_code=400):
    return jsonify({"success": False, "error": message}), status_code


def _json_ok(data, status_code=200):
    return jsonify({"success": True, "data": data}), status_code


def _current_role():
    claims = get_jwt()
    return str(claims.get("role") or "").strip().lower()


def _parse_pagination():
    page_raw = request.args.get("page", "1")
    limit_raw = request.args.get("limit", "20")

    try:
        page = int(page_raw)
        limit = int(limit_raw)
    except (TypeError, ValueError):
        return None, None, _json_error("page and limit must be integers", 400)

    if page < 1:
        return None, None, _json_error("page must be greater than 0", 400)
    if limit < 1:
        return None, None, _json_error("limit must be greater than 0", 400)

    return page, min(limit, MAX_LIMIT), None


def _query_for_user(user_id, notification_type="in_app"):
    return Notification.query.filter(
        Notification.recipient_id == user_id,
        Notification.notification_type == notification_type,
    )


def _dedupe_match(
    recipient_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id,
    dedupe_minutes,
):
    if dedupe_minutes <= 0:
        return None

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=dedupe_minutes)

    return (
        Notification.query.filter(
            Notification.recipient_id == recipient_id,
            Notification.notification_type == notification_type,
            Notification.title == title,
            Notification.message == message,
            Notification.related_resource_type == resource_type,
            Notification.related_resource_id == resource_id,
            Notification.created_at >= cutoff,
        )
        .order_by(Notification.notification_id.desc())
        .first()
    )


@notifications_bp.get("")
@jwt_required()
def list_notifications():
    user_id = get_current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    page, limit, pagination_error = _parse_pagination()
    if pagination_error:
        return pagination_error

    read_filter = (request.args.get("is_read") or "all").strip().lower()
    if read_filter not in ALLOWED_READ_FILTERS:
        return _json_error("is_read must be one of all, true, or false", 400)

    notification_type = (request.args.get("type") or "in_app").strip().lower()
    if notification_type not in ALLOWED_NOTIFICATION_TYPES:
        return _json_error("type must be one of in_app, email, or sms", 400)

    query = _query_for_user(user_id, notification_type=notification_type)

    if read_filter == "true":
        query = query.filter(Notification.is_read.is_(True))
    elif read_filter == "false":
        query = query.filter(Notification.is_read.is_(False))

    ordered_query = query.order_by(
        Notification.created_at.desc(),
        Notification.notification_id.desc(),
    )

    total = ordered_query.count()
    pages = ceil(total / limit) if total else 0
    rows = ordered_query.offset((page - 1) * limit).limit(limit).all()

    unread_count = _query_for_user(user_id, notification_type=notification_type).filter(
        Notification.is_read.is_(False)
    ).count()

    return _json_ok(
        {
            "items": [row.to_dict() for row in rows],
            "total": total,
            "page": page,
            "pages": pages,
            "limit": limit,
            "unread_count": unread_count,
            "type": notification_type,
        }
    )


@notifications_bp.post("/mark-read")
@jwt_required()
def mark_notification_read():
    user_id = get_current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    payload = request.get_json(silent=True) or {}
    mark_all = str(payload.get("mark_all") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }

    if mark_all:
        unread_rows = _query_for_user(user_id).filter(
            Notification.is_read.is_(False)
        ).all()

        if not unread_rows:
            return _json_ok({"updated_count": 0, "unread_count": 0})

        read_time = datetime.now(timezone.utc)
        for row in unread_rows:
            row.is_read = True
            row.read_at = read_time

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return _json_error("Unable to update notifications", 500)

        return _json_ok(
            {
                "updated_count": len(unread_rows),
                "unread_count": 0,
            }
        )

    raw_notification_id = payload.get("notification_id")
    try:
        notification_id = int(raw_notification_id)
    except (TypeError, ValueError):
        return _json_error("notification_id must be an integer", 400)

    notification = _query_for_user(user_id).filter(
        Notification.notification_id == notification_id
    ).first()
    if not notification:
        return _json_error("Notification not found", 404)

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to update notification", 500)

    unread_count = _query_for_user(user_id).filter(
        Notification.is_read.is_(False)
    ).count()

    return _json_ok(
        {
            "notification": notification.to_dict(),
            "unread_count": unread_count,
        }
    )


@notifications_bp.post("/create")
@jwt_required()
def create_notification():
    user_id = get_current_user_id()
    if user_id is None:
        return _json_error("Invalid token identity", 401)

    if _current_role() != "admin":
        return _json_error("Forbidden: insufficient permissions", 403)

    payload = request.get_json(silent=True) or {}

    raw_recipient_id = payload.get("user_id", payload.get("recipient_id"))
    try:
        recipient_id = int(raw_recipient_id)
    except (TypeError, ValueError):
        return _json_error("user_id is required and must be an integer", 400)

    recipient = db.session.get(User, recipient_id)
    if not recipient:
        return _json_error("Recipient user not found", 404)

    notification_type = str(payload.get("type") or "in_app").strip().lower()
    if notification_type not in ALLOWED_NOTIFICATION_TYPES:
        return _json_error("type must be one of in_app, email, or sms", 400)

    title = str(payload.get("title") or "Notification").strip()[:200]
    message = str(payload.get("message") or "").strip()
    if not message:
        return _json_error("message is required", 400)

    resource_type = str(payload.get("resource_type") or "system").strip()[:100]
    resource_type = resource_type or "system"

    raw_resource_id = payload.get("resource_id")
    resource_id = None
    if raw_resource_id not in (None, ""):
        try:
            resource_id = int(raw_resource_id)
        except (TypeError, ValueError):
            return _json_error("resource_id must be an integer", 400)

    raw_sender_id = payload.get("sender_id", user_id)
    sender_id = None
    if raw_sender_id not in (None, ""):
        try:
            sender_id = int(raw_sender_id)
        except (TypeError, ValueError):
            return _json_error("sender_id must be an integer", 400)

    try:
        dedupe_minutes = int(payload.get("dedupe_minutes", 5))
    except (TypeError, ValueError):
        dedupe_minutes = 5
    dedupe_minutes = max(0, dedupe_minutes)

    duplicate = _dedupe_match(
        recipient_id,
        notification_type,
        title,
        message,
        resource_type,
        resource_id,
        dedupe_minutes,
    )
    if duplicate:
        return _json_ok(
            {
                "notification": duplicate.to_dict(),
                "duplicate_skipped": True,
            }
        )

    notification = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        notification_type=notification_type,
        title=title,
        message=message,
        related_resource_type=resource_type,
        related_resource_id=resource_id,
        delivery_status="sent",
    )

    try:
        db.session.add(notification)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Unable to create notification", 500)

    return _json_ok(
        {
            "notification": notification.to_dict(),
            "duplicate_skipped": False,
        },
        201,
    )
