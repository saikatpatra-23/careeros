"""CareerOS — Dashboard (lovable.app design system)"""
import json
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import get_user_email, get_user_name, require_login
from modules.telemetry.tracker import install_error_tracking, track_page_view
from modules.ui.styles import inject_global_css
from persistence.store import UserStore

st.set_page_config(
    page_title="CareerOS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
require_login()
inject_global_css()

email = get_user_email()
name  = get_user_name()
install_error_tracking(email=email, page="Dashboard")
track_page_view(email=email, page="Dashboard")
store = UserStore(email)
summary = store.summary()

initials = "".join([p[0] for p in (name or "User").split()][:2]).upper() or "U"


# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="co-topbar">
        <div class="co-topbar-title">⚡ CareerOS</div>
        <div class="co-topbar-user">
            <span class="co-avatar">{initials}</span>
            <span>{name or "User"}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Page title ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="pg-title">
        <div class="pg-name">Dashboard</div>
        <div class="pg-sub">Your career command center</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Data helpers ──────────────────────────────────────────────────────────────
def _load_last_run() -> dict:
    report_path = "D:/Claude Project/naukri_report.json"
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        runs = data.get("runs", [])
        return runs[-1] if runs else {}
    except Exception:
        return {}


def _resume_status() -> tuple[str, str]:
    """Returns (label, css_class)."""
    if summary.get("has_resume"):
        role = summary.get("target_role", "")
        return (f"Built{' — ' + role if role else ''}", "good")
    return ("Not Built", "")


def _profile_status() -> tuple[str, str]:
    profile = store.load_profile()
    if profile.get("current_title") or profile.get("headline"):
        return ("Complete", "good")
    return ("Setup Needed", "")


last_run    = _load_last_run()
hr_invites  = store.load_hr_invites()
resume_st, resume_cls = _resume_status()
profile_st, profile_cls = _profile_status()

applied_7d  = last_run.get("applied", "—")
automation  = "Active" if last_run.get("timestamp") else "Not Run"
auto_cls    = "good" if last_run.get("timestamp") else ""

# ── Resume quality score from last quality report ─────────────────────────────
quality_report = store.load("quality_report.json", {})
resume_score   = quality_report.get("score", 0) if quality_report else 0

# ── Stat cards ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="lov-stats-grid">

      <div class="lov-stat">
        <div class="lov-stat-header">
          <span class="lov-stat-label">Resume Status</span>
          <span class="lov-stat-icon">📄</span>
        </div>
        <div class="lov-stat-value {resume_cls}">{resume_st}</div>
      </div>

      <div class="lov-stat">
        <div class="lov-stat-header">
          <span class="lov-stat-label">Naukri Profile</span>
          <span class="lov-stat-icon">📊</span>
        </div>
        <div class="lov-stat-value {profile_cls}">{profile_st}</div>
      </div>

      <div class="lov-stat">
        <div class="lov-stat-header">
          <span class="lov-stat-label">Resume Score</span>
          <span class="lov-stat-icon">✦</span>
        </div>
        <div class="lov-stat-value {'good' if resume_score >= 80 else ''}">{f'{resume_score}/100' if resume_score else '—'}</div>
      </div>

      <div class="lov-stat">
        <div class="lov-stat-header">
          <span class="lov-stat-label">Jobs Applied (last run)</span>
          <span class="lov-stat-icon">🚀</span>
        </div>
        <div class="lov-stat-value">{applied_7d}</div>
      </div>

      <div class="lov-stat">
        <div class="lov-stat-header">
          <span class="lov-stat-label">HR Invites</span>
          <span class="lov-stat-icon">✉️</span>
        </div>
        <div class="lov-stat-value">{len(hr_invites) if hr_invites else '—'}</div>
      </div>

      <div class="lov-stat">
        <div class="lov-stat-header">
          <span class="lov-stat-label">Automation</span>
          <span class="lov-stat-icon">⚡</span>
        </div>
        <div class="lov-stat-value {auto_cls}">{automation}</div>
      </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ── Weekly Progress ───────────────────────────────────────────────────────────
resume_pct  = min(resume_score, 100) if resume_score else 0
profile_pct = 100 if profile_cls == "good" else (40 if store.load_profile() else 0)
applied_num = last_run.get("applied", 0) if isinstance(last_run.get("applied"), int) else 0
apply_target = 50
apply_pct   = min(int(applied_num / apply_target * 100), 100)

st.markdown(
    f"""
    <div class="lov-card">
      <div class="lov-card-title">Weekly Progress</div>

      <div class="lov-progress">
        <div class="lov-progress-head">
          <span class="lov-progress-label">Resume Score</span>
          <span class="lov-progress-val">{resume_score if resume_score else '—'}/100</span>
        </div>
        <div class="lov-progress-track">
          <div class="lov-progress-fill" style="width:{resume_pct}%;"></div>
        </div>
      </div>

      <div class="lov-progress">
        <div class="lov-progress-head">
          <span class="lov-progress-label">Profile Completion</span>
          <span class="lov-progress-val">{profile_pct}%</span>
        </div>
        <div class="lov-progress-track">
          <div class="lov-progress-fill" style="width:{profile_pct}%;"></div>
        </div>
      </div>

      <div class="lov-progress">
        <div class="lov-progress-head">
          <span class="lov-progress-label">Applications Target</span>
          <span class="lov-progress-val">{applied_num}/{apply_target}</span>
        </div>
        <div class="lov-progress-track">
          <div class="lov-progress-fill" style="width:{apply_pct}%;"></div>
        </div>
      </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ── Quick Actions ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="lov-card-title" style="margin-bottom:12px;">Quick Actions</div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.page_link("pages/1_Resume_Builder.py",    label="📄  Build Resume",      use_container_width=True)
with c2:
    st.page_link("pages/2_Profile_Optimizer.py", label="👤  Optimize Profile",  use_container_width=True)
with c3:
    st.page_link("pages/4_ATS_Checker.py",       label="🎯  Run ATS Check",     use_container_width=True)
with c4:
    st.page_link("pages/5_Smart_Apply.py",       label="🚀  Smart Apply",       use_container_width=True)

st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

if st.button("Sign out", use_container_width=True):
    st.logout()
