# -*- coding: utf-8 -*-
"""
Google OAuth gate for CareerOS.
Uses Streamlit's native st.login() (requires Streamlit 1.41+ with [auth] secrets configured).
"""
import streamlit as st
from config import _get_secret
from modules.telemetry.tracker import track_login
import os
import hashlib


# Emergency owner fallback: protects admin access even if Streamlit secrets are unreadable.
# This is hash-based and only grants access to explicit owner emails.
_FALLBACK_ADMIN_EMAIL_SHA256 = {
    "a9789753a7913b3241e0092562a79ade409339b313fcd519e1fc7bdd362d75b5",  # saikatpatra64@gmail.com
}


def _nested_get(container, path: tuple[str, ...]):
    cur = container
    for part in path:
        try:
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                cur = cur[part]
        except Exception:
            return None
        if cur is None:
            return None
    return cur


def _parse_admin_emails(raw) -> set[str]:
    items: list[str] = []
    if isinstance(raw, str):
        normalized = raw.replace(";", ",").replace("\n", ",")
        items.extend(normalized.split(","))
    elif isinstance(raw, (list, tuple, set)):
        for val in raw:
            if isinstance(val, str):
                normalized = val.replace(";", ",").replace("\n", ",")
                items.extend(normalized.split(","))
    admins = set()
    for item in items:
        email = item.strip().strip('"').strip("'").lower()
        if email:
            admins.add(email)
    return admins


def _collect_secret_kv() -> dict[str, object]:
    flat: dict[str, object] = {}
    try:
        secrets_obj = st.secrets
    except Exception:
        return flat

    def _walk(prefix: str, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{prefix}.{k}" if prefix else str(k)
                _walk(key, v)
            return
        flat[prefix.lower()] = obj

    try:
        _walk("", secrets_obj)
    except Exception:
        pass
    return flat


def get_admin_emails() -> set[str]:
    parsed = set()

    # Primary path: existing helper (env var -> st.secrets top-level)
    for raw in (
        _get_secret("INTERNAL_ADMIN_EMAILS", ""),
        _get_secret("ADMIN_EMAILS", ""),
        _get_secret("OWNER_EMAIL", ""),
        _get_secret("internal_admin_emails", ""),
        _get_secret("admin_emails", ""),
        _get_secret("owner_email", ""),
    ):
        parsed |= _parse_admin_emails(raw)

    # Secondary path: direct st.secrets reads for nested sections.
    try:
        secrets_obj = st.secrets
    except Exception:
        secrets_obj = None

    if secrets_obj is not None:
        candidates = []
        for key in (
            "INTERNAL_ADMIN_EMAILS",
            "ADMIN_EMAILS",
            "OWNER_EMAIL",
            "internal_admin_emails",
            "admin_emails",
            "owner_email",
        ):
            value = _nested_get(secrets_obj, (key,))
            if value is not None:
                candidates.append(value)

        for path in (
            ("admin", "emails"),
            ("admin", "admin_emails"),
            ("admin", "internal_admin_emails"),
            ("security", "admin_emails"),
            ("security", "internal_admin_emails"),
        ):
            value = _nested_get(secrets_obj, path)
            if value is not None:
                candidates.append(value)

        for raw in candidates:
            parsed |= _parse_admin_emails(raw)

    # Tertiary path: scan flattened secrets/env with case-insensitive key matching.
    flat = _collect_secret_kv()
    for key, value in flat.items():
        if (
            "internal_admin_emails" in key
            or key.endswith("admin_emails")
            or key.endswith("owner_email")
        ):
            parsed |= _parse_admin_emails(value)

    for env_key, env_val in os.environ.items():
        k = env_key.strip().lower()
        if (
            k == "internal_admin_emails"
            or k == "admin_emails"
            or k == "owner_email"
            or k.endswith("_internal_admin_emails")
            or k.endswith("_admin_emails")
            or k.endswith("_owner_email")
        ):
            parsed |= _parse_admin_emails(env_val)

    return parsed


def is_admin_user(email: str) -> bool:
    normalized = email.strip().lower()
    if normalized in get_admin_emails():
        return True
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest in _FALLBACK_ADMIN_EMAIL_SHA256


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
        try:
            email = getattr(st.user, "email", "").strip().lower()
            if not is_admin_user(email):
                st.markdown(
                    """
                    <style>
                    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="7_Admin_Analytics"],
                    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="Admin_Analytics"],
                    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="admin_analytics"],
                    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="Admin+Analytics"],
                    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="admin+analytics"] {
                        display: none !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
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
