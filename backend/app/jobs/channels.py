"""Channel adapters for background job notifications."""

import json
import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path
from urllib import error, request

from flask import current_app

from app.models import Notification, User, db

SUPPORTED_CHANNELS = ("in_app", "email", "sms", "webhook")


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


def _notification_defaults(title, message, resource_type):
    return {
        "title": (title or "Reminder").strip()[:200],
        "message": (message or "").strip() or "You have an upcoming placement deadline.",
        "resource_type": (resource_type or "deadline_reminder").strip()[:100],
    }


def _create_notification(
    *,
    notification_type,
    recipient_id,
    sender_id,
    title,
    message,
    resource_type,
    resource_id,
    delivery_status="sent",
):
    normalized = _notification_defaults(title, message, resource_type)
    db.session.add(
        Notification(
            recipient_id=recipient_id,
            sender_id=sender_id,
            notification_type=notification_type,
            title=normalized["title"],
            message=normalized["message"],
            related_resource_type=normalized["resource_type"],
            related_resource_id=resource_id,
            delivery_status=delivery_status,
        )
    )


def _recipient_email(recipient_id):
    user = db.session.get(User, recipient_id)
    if not user:
        return None

    email_address = str(getattr(user, "email", "") or "").strip()
    return email_address or None


def _send_email(recipient_email, subject, body, html_body=None, attachments=None):
    smtp_host = str(current_app.config.get("MAIL_SMTP_HOST") or "").strip()
    if not smtp_host:
        allow_simulation = bool(
            current_app.config.get("MAIL_SIMULATE_WHEN_UNCONFIGURED", False)
        )
        if allow_simulation:
            return {
                "channel": "email",
                "status": "sent",
                "message": "MAIL_SMTP_HOST not configured; email delivery simulated",
                "simulated": True,
            }
        return {
            "channel": "email",
            "status": "failed",
            "message": "MAIL_SMTP_HOST not configured",
            "simulated": False,
        }

    sender_address = str(
        current_app.config.get("MAIL_FROM_ADDRESS") or "noreply@recruitify.local"
    ).strip() or "noreply@recruitify.local"

    smtp_port = int(current_app.config.get("MAIL_SMTP_PORT", 587) or 587)
    smtp_username = str(current_app.config.get("MAIL_SMTP_USERNAME") or "").strip()
    smtp_password = str(current_app.config.get("MAIL_SMTP_PASSWORD") or "")
    smtp_use_tls = bool(current_app.config.get("MAIL_SMTP_USE_TLS", True))
    smtp_use_ssl = bool(current_app.config.get("MAIL_SMTP_USE_SSL", False))
    timeout_seconds = max(1, int(current_app.config.get("MAIL_TIMEOUT_SECONDS", 10) or 10))

    msg = EmailMessage()
    msg["Subject"] = (subject or "Reminder").strip()[:200] or "Reminder"
    msg["From"] = sender_address
    msg["To"] = recipient_email

    body_text = (body or "").strip() or "You have a new notification from Recruitify."
    if html_body:
        msg.set_content(body_text)
        msg.add_alternative(str(html_body), subtype="html")
    else:
        msg.set_content(body_text)

    attached_files = []
    for raw_path in attachments or []:
        if not raw_path:
            continue

        attachment_path = Path(str(raw_path))
        if not attachment_path.exists() or not attachment_path.is_file():
            continue

        mime_type, _encoding = mimetypes.guess_type(attachment_path.name)
        if not mime_type:
            maintype, subtype = "application", "octet-stream"
        else:
            maintype, subtype = mime_type.split("/", 1)

        msg.add_attachment(
            attachment_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=attachment_path.name,
        )
        attached_files.append(attachment_path.name)

    try:
        if smtp_use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout_seconds) as client:
                if smtp_username and smtp_password:
                    client.login(smtp_username, smtp_password)
                client.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout_seconds) as client:
                client.ehlo()
                if smtp_use_tls:
                    client.starttls()
                    client.ehlo()
                if smtp_username and smtp_password:
                    client.login(smtp_username, smtp_password)
                client.send_message(msg)
    except Exception as exc:
        return {
            "channel": "email",
            "status": "failed",
            "message": str(exc),
        }

    attachment_hint = f" ({len(attached_files)} attachment(s))" if attached_files else ""
    return {
        "channel": "email",
        "status": "sent",
        "message": f"SMTP delivered{attachment_hint}",
        "simulated": False,
    }


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
    email_html=None,
    email_attachments=None,
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

    if channel == "email":
        recipient_email = _recipient_email(recipient_id)
        if not recipient_email:
            result = {
                "channel": "email",
                "status": "failed",
                "message": "Recipient email not found",
            }
        else:
            result = _send_email(
                recipient_email,
                title,
                message,
                html_body=email_html,
                attachments=email_attachments,
            )

        _create_notification(
            notification_type="email",
            recipient_id=recipient_id,
            sender_id=sender_id,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            delivery_status="sent" if result.get("status") == "sent" else "failed",
        )
        return result

    if channel == "sms":
        _create_notification(
            notification_type="sms",
            recipient_id=recipient_id,
            sender_id=sender_id,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            delivery_status="sent",
        )
        return {"channel": "sms", "status": "sent", "message": "queued"}

    if channel == "in_app":
        _create_notification(
            notification_type="in_app",
            recipient_id=recipient_id,
            sender_id=sender_id,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            delivery_status="sent",
        )
        return {"channel": "in_app", "status": "sent", "message": "queued"}

    if channel not in {"in_app", "email", "sms"}:
        return {
            "channel": channel,
            "status": "failed",
            "message": "Unsupported notification channel",
        }

    return {
        "channel": channel,
        "status": "failed",
        "message": "Unsupported notification channel",
    }
