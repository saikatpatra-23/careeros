# -*- coding: utf-8 -*-
"""
Admin-only telemetry page for beta operations.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from auth import get_admin_emails, get_user_email, is_admin_user, require_login
from modules.telemetry.tracker import read_events, track_page_view
from modules.ui.styles import inject_global_css

st.set_page_config(page_title="Admin Analytics - CareerOS", page_icon="A", layout="wide")
require_login()
inject_global_css()

email = get_user_email().strip().lower()
if not is_admin_user(email):
    st.error("Unauthorized.")
    st.caption(
        f"Logged-in email: {email}. "
        f"Configured admin allowlist entries: {len(get_admin_emails())}. "
        "Add your email to INTERNAL_ADMIN_EMAILS in Streamlit secrets."
    )
    st.stop()

track_page_view(email, "Admin Analytics")
events = read_events(limit=5000)

st.markdown(
    '<div class="pg-title"><span class="pg-icon">AD</span><span class="pg-name">Admin Analytics</span><span class="pg-sub">Beta user login, page visits, and errors</span></div>',
    unsafe_allow_html=True,
)

if not events:
    st.info("No telemetry events yet.")
    st.stop()

login_users = sorted({e.get("email", "") for e in events if e.get("event_type") == "login" and e.get("email")})
page_views = [e for e in events if e.get("event_type") == "page_view"]
errors = [e for e in events if e.get("event_type") == "error"]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Users Logged In", len(login_users))
with col2:
    st.metric("Page Views", len(page_views))
with col3:
    st.metric("Errors", len(errors))

st.markdown("### Logged-in Users")
st.dataframe([{"email": u} for u in login_users], use_container_width=True, hide_index=True)

st.markdown("### Most Visited Pages")
page_counts = Counter([(e.get("page") or "unknown") for e in page_views])
st.dataframe(
    [{"page": page, "views": count} for page, count in page_counts.most_common(20)],
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Recent Errors")
recent_errors = sorted(errors, key=lambda x: x.get("ts", ""), reverse=True)[:100]
st.dataframe(
    [
        {
            "ts": e.get("ts", ""),
            "email": e.get("email_masked") or e.get("email"),
            "page": e.get("page", ""),
            "type": (e.get("details") or {}).get("type", ""),
            "message": (e.get("details") or {}).get("message", ""),
            "handled": (e.get("details") or {}).get("handled", True),
        }
        for e in recent_errors
    ],
    use_container_width=True,
    hide_index=True,
)

with st.expander("Raw Recent Events"):
    latest = sorted(events, key=lambda x: x.get("ts", ""), reverse=True)[:200]
    st.json(latest)
