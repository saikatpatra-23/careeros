# -*- coding: utf-8 -*-
"""
Page 0 — User Setup / Onboarding
Collects phone, notification preference, and Naukri credentials.
Runs once after first login. Data used for automation + marketing.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email, get_user_name
from modules.ui.styles import inject_global_css
from persistence.store import UserStore
from config import _get_secret
from modules.notifications.ntfy import get_topic, notify_test
import base64, json
from cryptography.fernet import Fernet

st.set_page_config(page_title="Setup – CareerOS", page_icon="⚙️", layout="centered")
require_login()
inject_global_css()

email = get_user_email()
name  = get_user_name()
store = UserStore(email)

st.markdown("""
<style>
.security-note {
    background: rgba(16,185,129,0.08); border-radius: 8px; padding: 12px 16px;
    border-left: 3px solid #10B981; font-size: 0.84rem; color: #10B981;
    margin: 14px 0; line-height: 1.6;
}
.section-title {
    font-size: 0.82rem; font-weight: 700; color: #6B7280;
    margin: 22px 0 8px 0; padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    text-transform: uppercase; letter-spacing: 0.06em;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="pg-title"><span class="pg-icon">⚙️</span><span class="pg-name">Setup</span><span class="pg-sub">One-time personalisation</span></div>', unsafe_allow_html=True)

# Load existing setup
profile = store.load_profile()
already_setup = profile.get("setup_complete", False)

if already_setup:
    st.success("Setup already complete! You can update your preferences here anytime.")

st.markdown('<div class="section-title">📱 Notifications (Push — Instant & Free)</div>', unsafe_allow_html=True)

ntfy_topic = get_topic(email)

st.markdown(f"""
<div style="background:rgba(16,185,129,0.07);border-radius:10px;padding:16px 20px;border:1px solid rgba(16,185,129,0.2);margin-bottom:14px;">
    <div style="font-size:0.7rem;font-weight:700;color:#10B981;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">Your Notification Channel</div>
    <div style="font-family:monospace;font-size:1rem;font-weight:700;color:#6EE7B7;background:rgba(16,185,129,0.12);padding:6px 12px;border-radius:6px;display:inline-block;margin-bottom:10px;">{ntfy_topic}</div>
    <div style="font-size:0.83rem;color:#9CA3AF;line-height:1.65;">
        <b style="color:#E2E8F0;">One-time setup (30 sec):</b><br>
        1. Open <b style="color:#E2E8F0;">ntfy app</b> on your phone &nbsp;·&nbsp;
        2. Tap <b style="color:#E2E8F0;">+</b> → paste topic → Subscribe &nbsp;·&nbsp;
        3. Click <b style="color:#E2E8F0;">Test</b> below
    </div>
</div>
""", unsafe_allow_html=True)

col_test, col_info = st.columns([1, 2])
with col_test:
    if st.button("🔔 Test Notification", use_container_width=True):
        ok = notify_test(ntfy_topic)
        if ok:
            st.success("Sent! Check your ntfy app.")
        else:
            st.error("Failed. Check your internet connection.")
with col_info:
    st.caption(
        "ntfy is free, open-source, and works without an account. "
        "CareerOS uses it to alert you instantly when an HR invites you, "
        "views your profile, or when a job run completes."
    )

phone = profile.get("phone", "")
notif_pref = "ntfy"
contact_value = ntfy_topic

st.markdown('<div class="section-title">🔐 Naukri Credentials</div>', unsafe_allow_html=True)

st.markdown("""
<div class="security-note">
🔒 <strong>How we protect your credentials:</strong><br>
Your password is <strong>never stored</strong>. We capture an encrypted session token only —
the same way your browser remembers you. Only you can authorise access. We cannot see your password.
</div>
""", unsafe_allow_html=True)

naukri_email = st.text_input(
    "Naukri registered email",
    value=profile.get("naukri_email", ""),
    placeholder="yourname@gmail.com",
)
naukri_pass = st.text_input(
    "Naukri password",
    type="password",
    placeholder="Enter to encrypt and save",
    help="Stored as AES-256 encrypted token. Never stored as plain text.",
)

st.markdown('<div class="section-title">💼 Job Preferences</div>', unsafe_allow_html=True)
st.caption("These are auto-filled from your resume once you build it. You can override here.")

col1, col2 = st.columns(2)
with col1:
    preferred_locations = st.multiselect(
        "Preferred cities",
        ["Bengaluru", "Pune", "Mumbai", "Hyderabad", "Chennai",
         "Noida", "Gurgaon", "Kolkata", "Remote", "Any"],
        default=profile.get("preferred_locations", []),
    )
with col2:
    salary_min = st.number_input(
        "Minimum salary (LPA)",
        min_value=0, max_value=100,
        value=profile.get("salary_min", 0),
        step=1,
    )

work_mode = st.selectbox(
    "Work mode preference",
    ["Any", "Work from office", "Hybrid", "Remote"],
    index=["Any", "Work from office", "Hybrid", "Remote"].index(
        profile.get("work_mode", "Any")
    ),
)

st.divider()

if st.button("Save Setup →", type="primary", use_container_width=True):
    if notif_pref == "WhatsApp" and not phone.strip():
        st.warning("Please enter your WhatsApp number.")
        st.stop()
    if not naukri_email.strip():
        st.warning("Please enter your Naukri email.")
        st.stop()

    # Encrypt password if provided
    encrypted_pass = profile.get("naukri_pass_enc", "")
    if naukri_pass.strip():
        try:
            key = _get_secret("FERNET_KEY").encode()
            f   = Fernet(key)
            encrypted_pass = f.encrypt(naukri_pass.encode()).decode()
        except Exception:
            # If no FERNET_KEY, store a placeholder (add key to secrets)
            encrypted_pass = "__NEEDS_FERNET_KEY__"
            st.warning("Encryption key not configured — add FERNET_KEY to Streamlit secrets.")

    # Save to UserStore
    profile.update({
        "setup_complete":      True,
        "notif_pref":          "ntfy",
        "ntfy_topic":          ntfy_topic,
        "phone":               phone.strip(),
        "contact_value":       ntfy_topic,
        "naukri_email":        naukri_email.strip(),
        "naukri_pass_enc":     encrypted_pass,
        "preferred_locations": preferred_locations,
        "salary_min":          salary_min,
        "work_mode":           work_mode,
        "google_email":        email,
        "name":                name,
    })
    store.save_profile(profile)

    # Send to Make.com (CRM + marketing data)
    try:
        import requests
        make_url = _get_secret("MAKE_CRM_WEBHOOK", "")
        if make_url:
            requests.post(make_url, json={
                "name":     name,
                "email":    email,
                "phone":    phone.strip(),
                "notif":    notif_pref,
                "location": preferred_locations,
                "salary_min": salary_min,
            }, timeout=5)
    except Exception:
        pass  # Don't block user if webhook fails

    st.success("Setup saved! You're ready to use CareerOS.")
    st.balloons()
    st.page_link("app.py", label="Go to Dashboard →", icon="🚀")
