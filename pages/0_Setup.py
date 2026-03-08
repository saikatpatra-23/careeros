# -*- coding: utf-8 -*-
"""Setup page for notification, credentials, and job preferences."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from cryptography.fernet import Fernet

from auth import get_user_email, get_user_name, require_login
from config import _get_secret
from modules.notifications.ntfy import get_topic, notify_test
from modules.telemetry.tracker import install_error_tracking, log_error, track_page_view
from modules.ui.styles import inject_global_css
from persistence.store import UserStore

st.set_page_config(page_title="Setup - CareerOS", page_icon="S", layout="wide")
require_login()
inject_global_css()

email = get_user_email()
name = get_user_name()
install_error_tracking(email=email, page="Setup")
track_page_view(email=email, page="Setup")
store = UserStore(email)
profile = store.load_profile()
ntfy_topic = get_topic(email)

initials = "".join([p[0] for p in (name or "User").split()][:2]).upper() or "U"

st.markdown(
    f"""
    <div class="co-topbar">
        <div class="co-topbar-title">⚡ CareerOS</div>
        <div class="co-topbar-user">
            <span class="co-avatar">{initials}</span>
            <span>{name or "User"}</span>
        </div>
    </div>
    <div class="pg-title">
        <div class="pg-name">Setup</div>
        <div class="pg-sub">Configure your CareerOS workspace</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="co-card">', unsafe_allow_html=True)
    st.markdown('<div class="co-panel-title"><span>Notification Setup</span></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="co-muted" style="margin-bottom:12px;">
            Use this code to connect notifications.
        </div>
        <div class="co-chip" style="font-family:'JetBrains Mono', monospace; font-size:1.02rem; margin-bottom:12px;">
            {ntfy_topic}
        </div>
        """,
        unsafe_allow_html=True,
    )
    n1, n2 = st.columns([1, 1.2])
    with n1:
        if st.button("Send Test Notification", type="primary", use_container_width=True):
            if notify_test(ntfy_topic):
                st.success("Test notification sent.")
            else:
                st.error("Failed to send test notification.")
    with n2:
        st.text_input("Notification code", value=ntfy_topic, disabled=True, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="co-card" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<div class="co-panel-title"><span>Naukri Credentials</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="co-muted" style="margin-bottom:12px;">Credentials are encrypted and never stored as plain text.</div>',
        unsafe_allow_html=True,
    )
    naukri_email = st.text_input(
        "Naukri Email",
        value=profile.get("naukri_email", ""),
        placeholder="your@email.com",
    )
    naukri_pass = st.text_input(
        "Naukri Password",
        type="password",
        placeholder="Enter password to encrypt and save",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="co-card" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<div class="co-panel-title"><span>Job Preferences</span></div>', unsafe_allow_html=True)
    preferred_locations = st.multiselect(
        "Preferred Cities",
        ["Bengaluru", "Pune", "Mumbai", "Hyderabad", "Chennai", "Delhi NCR", "Noida", "Gurugram", "Remote"],
        default=profile.get("preferred_locations", []),
    )
    salary_min = st.number_input(
        "Minimum Salary (LPA)",
        min_value=0,
        max_value=100,
        value=int(profile.get("salary_min", 0)),
        step=1,
    )
    work_mode = st.radio(
        "Work Mode",
        options=["Remote", "Hybrid", "Office", "Any"],
        horizontal=True,
        index=["Remote", "Hybrid", "Office", "Any"].index(profile.get("work_mode", "Any")) if profile.get("work_mode", "Any") in ["Remote", "Hybrid", "Office", "Any"] else 3,
    )
    st.markdown("</div>", unsafe_allow_html=True)

if st.button("Save Preferences", type="primary", use_container_width=True):
    if not naukri_email.strip():
        st.warning("Naukri email is required.")
        st.stop()

    encrypted_pass = profile.get("naukri_pass_enc", "")
    if naukri_pass.strip():
        try:
            key = _get_secret("FERNET_KEY", "").encode()
            if not key:
                raise ValueError("FERNET_KEY missing")
            encrypted_pass = Fernet(key).encrypt(naukri_pass.encode()).decode()
        except Exception as exc:
            log_error(email=email, page="Setup", exc=exc, handled=True)
            st.error("FERNET_KEY missing/invalid. Add it in secrets and retry.")
            st.stop()

    profile.update(
        {
            "setup_complete": True,
            "notif_pref": "ntfy",
            "ntfy_topic": ntfy_topic,
            "contact_value": ntfy_topic,
            "naukri_email": naukri_email.strip(),
            "naukri_pass_enc": encrypted_pass,
            "preferred_locations": preferred_locations,
            "salary_min": salary_min,
            "work_mode": work_mode,
            "google_email": email,
            "name": name,
        }
    )
    store.save_profile(profile)
    st.success("Setup saved successfully.")
    st.page_link("app.py", label="Open Dashboard")
