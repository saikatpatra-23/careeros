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
from persistence.store import UserStore
from config import _get_secret
import base64, json
from cryptography.fernet import Fernet

st.set_page_config(page_title="Setup – CareerOS", page_icon="⚙️", layout="centered")
require_login()

email = get_user_email()
name  = get_user_name()
store = UserStore(email)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.setup-header {
    background: linear-gradient(135deg, #1B4F9C 0%, #2563EB 100%);
    border-radius: 14px; padding: 28px 32px; color: white; margin-bottom: 28px;
}
.setup-header h2 { margin: 0 0 6px 0; font-size: 1.6rem; font-weight: 700; }
.setup-header p  { margin: 0; opacity: 0.88; font-size: 0.95rem; }
.security-note {
    background: #F0FDF4; border-radius: 10px; padding: 14px 18px;
    border-left: 4px solid #059669; font-size: 0.85rem; color: #065F46;
    margin: 16px 0; line-height: 1.6;
}
.section-title {
    font-size: 1rem; font-weight: 700; color: #1F273A;
    margin: 24px 0 8px 0; padding-bottom: 6px;
    border-bottom: 1.5px solid #E2E8F0;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="setup-header">
    <h2>⚙️ Quick Setup</h2>
    <p>One-time setup to personalise CareerOS and enable job automation for you.</p>
</div>
""", unsafe_allow_html=True)

# Load existing setup
profile = store.load_profile()
already_setup = profile.get("setup_complete", False)

if already_setup:
    st.success("Setup already complete! You can update your preferences here anytime.")

st.markdown('<div class="section-title">📱 Notification Preference</div>', unsafe_allow_html=True)

notif_pref = st.radio(
    "How should CareerOS notify you about job applications?",
    ["WhatsApp", "Email"],
    index=0 if profile.get("notif_pref", "WhatsApp") == "WhatsApp" else 1,
    horizontal=True,
)

if notif_pref == "WhatsApp":
    phone = st.text_input(
        "WhatsApp number (with country code)",
        value=profile.get("phone", ""),
        placeholder="+91 98765 43210",
    )
    contact_value = phone
else:
    contact_value = email
    st.info(f"Notifications will be sent to: **{email}**")
    phone = profile.get("phone", "")

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
        "notif_pref":          notif_pref,
        "phone":               phone.strip(),
        "contact_value":       contact_value,
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
