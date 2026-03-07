# -*- coding: utf-8 -*-
"""
Google OAuth gate for CareerOS.
Uses Streamlit's native st.login() (requires Streamlit 1.41+ with [auth] secrets configured).
"""
import streamlit as st
from modules.telemetry.tracker import track_login


def require_login() -> None:
    """Block the page if user is not logged in. Show Google login button."""
    from modules.ui.styles import inject_global_css

    inject_global_css()

    try:
        logged_in = st.user.is_logged_in
    except AttributeError:
        st.markdown(
            """
            <div class="co-hero" style="margin-top: 24px;">
                <span class="co-hero-badge">Local Setup Needed</span>
                <div class="co-hero-title">OAuth is not configured on this machine</div>
                <div class="co-hero-copy">
                    Add the <code>[auth]</code> section to <code>.streamlit/secrets.toml</code> using
                    <code>.streamlit/secrets.toml.example</code> as the template, then restart Streamlit.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()
        return

    if logged_in:
        try:
            track_login(getattr(st.user, "email", ""), getattr(st.user, "name", ""))
        except Exception:
            pass
        return

    st.markdown(
        """
        <div class="co-hero" style="margin-top: 24px;">
            <span class="co-hero-badge">CareerOS Access</span>
            <div class="co-hero-title">Your AI job-search operating system for India</div>
            <div class="co-hero-copy">
                Build a sharper resume, convert it into recruiter-facing Naukri and LinkedIn content,
                and automate the repetitive parts of your search from one focused workspace.
            </div>
            <div class="co-inline-stats">
                <span class="co-pill">Resume Builder</span>
                <span class="co-pill">Profile Optimizer</span>
                <span class="co-pill">ATS Checker</span>
                <span class="co-pill">Smart Apply</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="co-card" style="max-width: 520px; margin: 0 auto 16px auto; text-align: center;">
            <span class="co-badge live">Google OAuth</span>
            <h3 style="margin: 6px 0 10px 0;">Sign in to open your CareerOS workspace</h3>
            <p class="co-muted" style="margin-bottom: 18px;">
                Your data stays tied to your Google identity and is stored only in your CareerOS user space.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1.2, 1.6, 1.2])
    with col2:
        if st.button("Sign in with Google", type="primary", use_container_width=True):
            st.login()
        st.caption("No account creation flow. Google is used only for sign-in and user isolation.")
    st.stop()


def get_user_email() -> str:
    return getattr(st.user, "email", "user@gmail.com")


def get_user_name() -> str:
    return getattr(st.user, "name", "User")


def get_user_avatar() -> str:
    return getattr(st.user, "picture", "")
