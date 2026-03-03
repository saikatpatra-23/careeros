# -*- coding: utf-8 -*-
"""
Google OAuth gate for CareerOS.
Uses Streamlit's native st.login() (requires Streamlit 1.41+ with [auth] secrets configured).
"""
import streamlit as st


def require_login() -> None:
    """Block the page if user is not logged in. Show Google login button."""

    # Guard: [auth] section not yet configured in secrets.toml
    try:
        logged_in = st.user.is_logged_in
    except AttributeError:
        st.error(
            "**OAuth not configured.** "
            "Add the `[auth]` section to Streamlit Cloud secrets. "
            "See `.streamlit/secrets.toml.example` for the required format."
        )
        st.stop()
        return

    if logged_in:
        return

    st.markdown("""
    <div style='max-width:420px; margin: 80px auto; text-align:center;'>
        <h1 style='color:#1B4F9C; font-size:2rem;'>CareerOS</h1>
        <p style='color:#555; font-size:1rem; margin-bottom:8px;'>
            Your AI-powered career coach for the Indian job market.
        </p>
        <p style='color:#888; font-size:0.85rem;'>
            Resume building &bull; Role clarity &bull; Naukri &amp; LinkedIn optimization
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign in with Google", type="primary", use_container_width=True):
            st.login()
        st.markdown(
            "<p style='color:#aaa; font-size:0.75rem; text-align:center; margin-top:12px;'>"
            "Your data is stored only on this server and never shared.</p>",
            unsafe_allow_html=True,
        )
    st.stop()


def get_user_email() -> str:
    return getattr(st.user, "email", "user@gmail.com")


def get_user_name() -> str:
    return getattr(st.user, "name", "User")


def get_user_avatar() -> str:
    return getattr(st.user, "picture", "")
