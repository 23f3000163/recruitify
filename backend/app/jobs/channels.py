"""Channel adapters for background job notifications."""

import json
from urllib import error, request

from app.models import Notification, db

SUPPORTED_CHANNELS = ("email", "sms", "webhook")


def parse_channels(raw_channels):
    """Normalize channel config into a deterministic ordered list."""
    if isinstance(raw_channels, (list, tuple, set)):
        values = [str(item or "").strip().lower() for item in raw_channels]
    else:
        values = [part.strip().lower() for part in str(raw_channels or "").split(",")]

    normalized = []
    for channel in values:
        if channel in SUPPORTED_CHANNELS and channel not in normalized:
            normalized.append(channel)

    return normalized or ["email"]


def _send_webhook(webhook_url, payload):
    if not webhook_url:
        return {"channel": "webhook", "status": "failed", "message": "JOBS_WEBHOOK_URL not configured"}

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with request.urlopen(req, timeout=3) as response:
            response_code = int(getattr(response, "status", 0))
    except error.HTTPError as exc:
        return {
            "channel": "webhook",
            "status": "failed",
            "message": f"HTTP {exc.code}",
        }
    except Exception as exc:
        return {
            "channel": "webhook",
            "status": "failed",
            "message": str(exc),
        }

    if 200 <= response_code < 300:
        return {"channel": "webhook", "status": "sent", "message": f"HTTP {response_code}"}

    return {
        "channel": "webhook",
        "status": "failed",
        "message": f"Unexpected response {response_code}",
    }


def send_channel_notification(
    *,
    channel,
    recipient_id,
    title,
    message,
    sender_id=None,
    resource_type=None,
    resource_id=None,
    webhook_url=None,
    webhook_payload=None,
):
    """Send a reminder through one configured delivery channel."""
    if channel == "webhook":
        payload = webhook_payload or {
            "recipient_id": recipient_id,
            "title": title,
            "message": message,
            "resource_type": resource_type,
            "resource_id": resource_id,
        }
        return _send_webhook(webhook_url, payload)

    if channel not in {"email", "sms"}:
        return {
            "channel": channel,
            "status": "failed",
            "message": "Unsupported notification channel",
        }

    db.session.add(
        Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
            notification_type=channel,
            title=(title or "Reminder").strip()[:200],
            message=(message or "").strip() or "You have an upcoming placement deadline.",
            related_resource_type=(resource_type or "deadline_reminder").strip()[:100],
            related_resource_id=resource_id,
            delivery_status="sent",
        )
    )

    return {"channel": channel, "status": "sent", "message": "queued"}
