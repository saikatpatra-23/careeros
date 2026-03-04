# -*- coding: utf-8 -*-
"""
CareerOS — Push Notifications via ntfy.sh
Free, no account needed. User subscribes to their unique topic in the ntfy app.
"""
from __future__ import annotations
import hashlib
import requests

NTFY_BASE = "https://ntfy.sh"


def get_topic(email: str) -> str:
    """Deterministic, non-guessable topic from user email. Same every time."""
    h = hashlib.md5(email.lower().strip().encode()).hexdigest()[:10]
    return f"careeros-{h}"


def send(
    topic: str,
    title: str,
    message: str,
    priority: str = "default",   # min | low | default | high | urgent
    tags: list[str] | None = None,
    click_url: str = "",
) -> bool:
    """
    Send a push notification via ntfy.sh.
    Returns True if delivered, False on any error.
    """
    headers: dict[str, str] = {
        "Title":    title,
        "Priority": priority,
    }
    if tags:
        headers["Tags"] = ",".join(tags)
    if click_url:
        headers["Click"] = click_url

    try:
        r = requests.post(
            f"{NTFY_BASE}/{topic}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=6,
        )
        return r.status_code == 200
    except Exception:
        return False


# ── Typed notification helpers ────────────────────────────────────────────────

def notify_hr_invite(topic: str, company: str, role: str, hr_name: str,
                     apply_url: str = "", applied: bool = False) -> bool:
    status = "Auto-applied by CareerOS" if applied else "Needs your attention"
    return send(
        topic    = topic,
        title    = f"HR Invite — {company}",
        message  = (
            f"Role: {role}\n"
            f"HR: {hr_name or 'Unknown'}\n"
            f"Status: {status}"
        ),
        priority = "urgent",
        tags     = ["fire", "briefcase"],
        click_url= apply_url,
    )


def notify_profile_view(topic: str, company: str) -> bool:
    return send(
        topic    = topic,
        title    = f"Profile Viewed — {company}",
        message  = "An HR from this company viewed your Naukri profile. Invite may follow.",
        priority = "high",
        tags     = ["eyes"],
    )


def notify_run_complete(topic: str, jobs_found: int, jobs_applied: int,
                        hr_invites: int = 0) -> bool:
    parts = [f"Jobs scanned: {jobs_found}", f"Applied: {jobs_applied}"]
    if hr_invites:
        parts.insert(0, f"HR invites processed: {hr_invites}")
    return send(
        topic    = topic,
        title    = "CareerOS Run Complete",
        message  = "\n".join(parts),
        priority = "low",
        tags     = ["white_check_mark"],
    )


def notify_test(topic: str) -> bool:
    return send(
        topic    = topic,
        title    = "CareerOS is connected!",
        message  = "Notifications are working. You'll be alerted instantly for HR invites, profile views, and job run results.",
        priority = "default",
        tags     = ["tada"],
    )
