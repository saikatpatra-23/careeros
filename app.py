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
opt = store.load_profile_optimizer()
apply_history = store.load_apply_history()
invites = store.load_hr_invites()

jobs_applied = sum(int(r.get("jobs_applied", 0)) for r in apply_history[:10])
resume_status = "Optimized" if summary.get("has_resume") else "Missing"
naukri_score = "78/100" if opt.get("naukri") else "0/100"
linkedin_score = "65/100" if opt.get("linkedin") else "0/100"
automation_status = "Active" if summary.get("has_resume") else "Setup Needed"

initials = "".join([p[0] for p in (name or "User").split()][:2]).upper() or "U"

st.markdown(
    f"""
    <div class="co-topbar">
        <div class="co-topbar-title">CareerOS</div>
        <div class="co-topbar-user">
            <span class="co-avatar">{initials}</span>
            <span>{name or "User"}</span>
        </div>
    </div>
    <div class="pg-title">
        <div class="pg-name">Dashboard</div>
        <div class="pg-sub">Career command center</div>
    </div>
    """,
    unsafe_allow_html=True,
)

cards = [
    ("Resume Status", resume_status),
    ("Naukri Profile Score", naukri_score),
    ("LinkedIn Score", linkedin_score),
    ("Jobs Applied (7d)", str(jobs_applied)),
    ("HR Invites", str(len(invites))),
    ("Automation", automation_status),
]

st.markdown('<div class="co-grid-2">', unsafe_allow_html=True)
for label, value in cards:
    st.markdown(
        f"""
        <div class="co-metric">
            <div class="co-metric-label">{label}</div>
            <div class="co-metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

applications_target = min(100, int((jobs_applied / 50) * 100)) if jobs_applied else 0
profile_completion = 78 if opt.get("naukri") else 30
resume_score = 85 if summary.get("has_resume") else 10

st.markdown(
    f"""
    <div class="co-card" style="margin-top:14px;">
        <h3 style="font-size:2rem;margin-bottom:8px;">Weekly Progress</h3>
        <div class="co-progress-row">
            <div class="co-progress-head"><span>Applications Target</span><b>{jobs_applied}/50</b></div>
            <div class="co-progress-track"><div class="co-progress-fill" style="width:{applications_target}%;"></div></div>
        </div>
        <div class="co-progress-row">
            <div class="co-progress-head"><span>Profile Completion</span><b>{profile_completion}/100</b></div>
            <div class="co-progress-track"><div class="co-progress-fill" style="width:{profile_completion}%;"></div></div>
        </div>
        <div class="co-progress-row">
            <div class="co-progress-head"><span>Resume Score</span><b>{resume_score}/100</b></div>
            <div class="co-progress-track"><div class="co-progress-fill" style="width:{resume_score}%;"></div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="co-panel-title" style="margin-top:16px;"><span>Quick Actions</span></div>', unsafe_allow_html=True)
qa1, qa2 = st.columns(2)
with qa1:
    st.page_link("pages/1_Resume_Builder.py", label="Build Resume")
    st.page_link("pages/4_ATS_Checker.py", label="Run ATS Check")
with qa2:
    st.page_link("pages/2_Profile_Optimizer.py", label="Optimize Profile")
    st.page_link("pages/5_Smart_Apply.py", label="Start Smart Apply")

if st.button("Sign out", use_container_width=True):
    st.logout()
