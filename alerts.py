"""
Alert delivery. Sends milestone alerts via email (SendGrid) and/or
SMS (Twilio). Both are optional — if credentials aren't set, alerts
are logged instead of sent, so the system runs fine in dev.
"""

import logging
from typing import List

import httpx

from app.config import settings
from app.tracker import TrackedVehicle

log = logging.getLogger("alerts")


def _format_digest(alerts: List[TrackedVehicle]) -> str:
    lines = ["Inventory milestone alerts:\n"]
    for t in alerts:
        lines.append(f"• {t.alert}")
    lines.append(f"\n{len(alerts)} vehicle(s) crossed a milestone since the last check.")
    return "\n".join(lines)


def send_email(to_email: str, subject: str, body: str) -> bool:
    if not settings.SENDGRID_API_KEY:
        log.info("[email disabled] to=%s subject=%s\n%s", to_email, subject, body)
        return False
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": settings.ALERT_FROM_EMAIL},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}],
                },
            )
            resp.raise_for_status()
        return True
    except Exception as e:
        log.error("email send failed: %s", e)
        return False


def send_sms(to_number: str, body: str) -> bool:
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN):
        log.info("[sms disabled] to=%s\n%s", to_number, body)
        return False
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{settings.TWILIO_ACCOUNT_SID}/Messages.json",
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                data={"From": settings.TWILIO_FROM_NUMBER,
                      "To": to_number, "Body": body},
            )
            resp.raise_for_status()
        return True
    except Exception as e:
        log.error("sms send failed: %s", e)
        return False


def dispatch_alerts(alerts: List[TrackedVehicle], email: str = "", sms: str = ""):
    """Send a digest of newly-crossed milestone alerts."""
    if not alerts:
        return {"sent": False, "reason": "no new alerts"}

    digest = _format_digest(alerts)
    subject = f"{len(alerts)} inventory alert(s) — action needed"

    sent = {}
    if email:
        sent["email"] = send_email(email, subject, digest)
    if sms:
        # SMS keeps it short — just the count + first item.
        short = f"{len(alerts)} inventory alert(s). {alerts[0].alert}"
        sent["sms"] = send_sms(sms, short)
    return {"sent": True, "channels": sent, "digest": digest}
