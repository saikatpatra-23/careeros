# -*- coding: utf-8 -*-
"""
CareerOS results ingest endpoint.

Used by the local runner to sync run results into user storage.
This page is internal and should not be visible/useful to beta users.
"""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from config import _get_secret
from persistence.store import UserStore

st.set_page_config(page_title="CareerOS Sync", page_icon="S", layout="centered")


def _query_value(key: str) -> str:
    """Return a single query-param value from Streamlit's query-param mapping."""
    val = st.query_params.get(key, "")
    if isinstance(val, list):
        return val[0] if val else ""
    return str(val or "")


def _admin_emails() -> set[str]:
    raw = (
        _get_secret("INTERNAL_ADMIN_EMAILS", "")
        or _get_secret("ADMIN_EMAILS", "")
        or _get_secret("OWNER_EMAIL", "")
    )
    if not raw:
        return set()
    return {item.strip().lower() for item in raw.replace(";", ",").split(",") if item.strip()}


def _is_admin_logged_in() -> bool:
    try:
        if not st.user.is_logged_in:
            return False
        email = getattr(st.user, "email", "").strip().lower()
    except Exception:
        return False
    return bool(email and email in _admin_emails())


SYNC_SECRET = _get_secret("SYNC_SECRET", "")
action = _query_value("action")
token = _query_value("token")
data_b64 = _query_value("data")


def _invalid_token_response() -> None:
    st.json({"status": "error", "message": "invalid token"})
    st.stop()


# Health check for runner: require token.
if action == "ping":
    if not SYNC_SECRET or token != SYNC_SECRET:
        _invalid_token_response()
    st.json({"status": "ok", "service": "CareerOS Results Ingest"})
    st.stop()


# Ingest mode: require token + payload.
if data_b64 and token:
    if not SYNC_SECRET or token != SYNC_SECRET:
        _invalid_token_response()

    try:
        payload = json.loads(base64.b64decode(data_b64).decode("utf-8"))
        email = payload.get("email", "").strip()
        results = payload.get("results", {})
        if not email or not isinstance(results, dict):
            st.json({"status": "error", "message": "invalid payload"})
            st.stop()

        store = UserStore(email)
        store.save_apply_run(results)
        for invite in results.get("hr_invites", []):
            store.save_hr_invite(invite)

        st.json(
            {
                "status": "ok",
                "jobs_applied": results.get("jobs_applied", 0),
                "jobs_found": results.get("jobs_found", 0),
            }
        )
        st.stop()
    except Exception as exc:
        st.json({"status": "error", "message": f"sync failed: {exc}"})
        st.stop()


# Manual view: admin-only.
if _is_admin_logged_in():
    st.markdown("## CareerOS Internal Sync Endpoint")
    st.markdown("This page is internal. Beta users should not use it.")
    st.code(
        "https://<app>.streamlit.app/api_ingest?token=<SYNC_SECRET>&data=<base64_payload>",
        language="text",
    )
else:
    st.error("Not found.")
