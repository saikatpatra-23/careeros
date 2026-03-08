"""CareerOS - Dashboard"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import get_user_email, get_user_name, require_login
from modules.telemetry.tracker import install_error_tracking, track_page_view
from modules.ui.styles import inject_global_css
from persistence.store import UserStore

st.set_page_config(page_title="CareerOS", page_icon="C", layout="wide", initial_sidebar_state="expanded")
require_login()
inject_global_css()

email = get_user_email()
name = get_user_name()
install_error_tracking(email=email, page="Dashboard")
track_page_view(email=email, page="Dashboard")
store = UserStore(email)

summary = store.summary()

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
        <div class="pg-name">Dashboard</div>
        <div class="pg-sub">Welcome to CareerOS</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="co-card" style="margin-top:8px;">
        <h3 style="font-size:2rem;margin-bottom:10px;">Welcome to your AI Career Command Center</h3>
        <p class="co-muted" style="font-size:1rem;line-height:1.7;margin:0;">
            CareerOS helps Indian professionals optimize resume + profiles, improve ATS match, and automate smart job actions.
            Use Quick Actions below to jump directly to the workflow you need.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="co-panel-title" style="margin-top:16px;"><span>Quick Actions</span></div>', unsafe_allow_html=True)

actions = [
    ("Resume Builder", "Build or upload resume with AI chat", "pages/1_Resume_Builder.py", "Open Resume Builder"),
    ("Profile Optimizer", "Generate Naukri + LinkedIn profile content", "pages/2_Profile_Optimizer.py", "Open Profile Optimizer"),
    ("ATS Checker", "Check JD match and get exact fixes", "pages/4_ATS_Checker.py", "Open ATS Checker"),
    ("Smart Apply", "Configure automation and download runner", "pages/5_Smart_Apply.py", "Open Smart Apply"),
]

for i in range(0, len(actions), 2):
    col1, col2 = st.columns(2)
    for col, item in zip((col1, col2), actions[i:i + 2]):
        title, desc, target, cta = item
        with col:
            st.markdown('<div class="co-card" style="min-height:160px;">', unsafe_allow_html=True)
            st.markdown(f"### {title}")
            st.markdown(f'<div class="co-muted" style="margin-bottom:12px;">{desc}</div>', unsafe_allow_html=True)
            st.page_link(target, label=cta, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

if st.button("Sign out", use_container_width=True):
    st.logout()
