"""CareerOS - Dashboard"""
import os
import random
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="CareerOS",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import get_user_email, get_user_name, require_login
from modules.ui.styles import inject_global_css
from persistence.store import UserStore

require_login()
inject_global_css()

email = get_user_email()
name = get_user_name()
store = UserStore(email)
summary = store.summary()
first_name = name.split()[0] if name else "there"
opt = store.load_profile_optimizer()
cover_letters = store.load_cover_letters()

has_res = summary["has_resume"]
has_opt = bool(opt.get("naukri"))
cl_count = len(cover_letters)
progress_count = sum([has_res, has_opt, cl_count > 0])

tips = [
    "Indian recruiters usually scan title, company, keywords, and notice period before they read the rest.",
    "Profiles refreshed weekly tend to stay more visible in recruiter search than stale profiles.",
    "If your resume is broad, make your Naukri headline narrower and more recruiter-searchable than your PDF title.",
    "The best beta UX is clarity: one strong role, a few cities, and crisp quantified achievements.",
]

st.markdown(
    f"""
    <div class="co-hero">
        <span class="co-hero-badge">CareerOS Workspace</span>
        <div class="co-hero-title">Build a sharper profile, then turn it into interviews</div>
        <div class="co-hero-copy">
            Welcome back, <b>{first_name}</b>. CareerOS is designed as a compact job-search operating system: create a strong resume,
            convert it into recruiter-facing profile content, and then automate the repetitive Naukri work from one place.
        </div>
        <div class="co-inline-stats">
            <span class="co-pill"><b>{progress_count}/3</b> core milestones complete</span>
            <span class="co-pill">Target role: <b>{summary.get('target_role') or 'Not set yet'}</b></span>
            <span class="co-pill">Cover letters: <b>{cl_count}</b></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

header_cols = st.columns([4.5, 1.2, 1.2])
with header_cols[0]:
    st.markdown(f'<div class="co-tip">{random.choice(tips)}</div>', unsafe_allow_html=True)
with header_cols[1]:
    st.page_link("pages/2_Profile_Optimizer.py", label="Open Optimizer", icon="??")
with header_cols[2]:
    if st.button("Sign out", use_container_width=True):
        st.logout()

st.markdown('<div class="co-section-kicker">Core Journey</div><div class="co-section-title">What to do next</div>', unsafe_allow_html=True)
core_cols = st.columns(4, gap="large")
core_cards = [
    {
        "title": "Resume Builder",
        "badge": "done" if has_res else "live",
        "badge_text": "Done" if has_res else "Start here",
        "body": "Create or import a resume, structure it, and give CareerOS a reliable source of truth.",
        "link": "pages/1_Resume_Builder.py",
        "icon": "??",
    },
    {
        "title": "Profile Optimizer",
        "badge": "done" if has_opt else "live",
        "badge_text": "Ready" if has_opt else "Recommended",
        "body": "Answer a few high-signal questions and turn your resume into a recruiter-facing Naukri + LinkedIn draft.",
        "link": "pages/2_Profile_Optimizer.py",
        "icon": "??",
    },
    {
        "title": "ATS Checker",
        "badge": "live" if has_res else "soon",
        "badge_text": "Ready" if has_res else "Needs resume",
        "body": "Check how close a specific JD is to your current resume before you apply.",
        "link": "pages/4_ATS_Checker.py",
        "icon": "??",
    },
    {
        "title": "Smart Apply",
        "badge": "live" if has_res else "soon",
        "badge_text": "Automation" if has_res else "Needs resume",
        "body": "Run Naukri search and apply workflows once your profile and targeting are dialed in.",
        "link": "pages/5_Smart_Apply.py",
        "icon": "??",
    },
]

for col, card in zip(core_cols, core_cards):
    with col:
        st.markdown(
            f"""
            <div class="co-card">
                <span class="co-badge {card['badge']}">{card['badge_text']}</span>
                <h4 style="margin:0 0 8px 0;">{card['icon']} {card['title']}</h4>
                <p class="co-muted" style="margin-bottom:14px;">{card['body']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(card["link"], label=f"Open {card['title']}", icon=card["icon"])

st.divider()

st.markdown('<div class="co-section-kicker">Utility Layer</div><div class="co-section-title">Support tools around the core journey</div>', unsafe_allow_html=True)
utility_cols = st.columns(3, gap="large")
utility_cards = [
    {
        "title": "Cover Letter",
        "badge": "done" if cl_count else "live",
        "badge_text": f"{cl_count} saved" if cl_count else "Ready",
        "body": "Generate job-specific cover letters in seconds once your base profile is strong.",
        "link": "pages/6_Cover_Letter.py",
        "icon": "??",
    },
    {
        "title": "Role Clarity",
        "badge": "live",
        "badge_text": "Strategy",
        "body": "Narrow vague career intent into a sharper role direction before profile generation.",
        "link": "pages/3_Role_Clarity.py",
        "icon": "??",
    },
    {
        "title": "Setup",
        "badge": "live",
        "badge_text": "Profile",
        "body": "Store Naukri credentials, notification routing, and basic job preferences.",
        "link": "pages/0_Setup.py",
        "icon": "??",
    },
]

for col, card in zip(utility_cols, utility_cards):
    with col:
        st.markdown(
            f"""
            <div class="co-card tight">
                <span class="co-badge {card['badge']}">{card['badge_text']}</span>
                <h4 style="margin:0 0 8px 0;">{card['icon']} {card['title']}</h4>
                <p class="co-muted">{card['body']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(card["link"], label=f"Open {card['title']}", icon=card["icon"])

st.caption("CareerOS | India-focused job operating system | Claude-powered | Personal data stored per user")
