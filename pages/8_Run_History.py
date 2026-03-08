"""
Page 8 - Run History
Standalone timeline for Smart Apply runs and recruiter invites.
"""
import os
import sys
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email
from modules.telemetry.tracker import install_error_tracking, track_page_view
from modules.ui.styles import inject_global_css
from persistence.store import UserStore
from config import _get_secret


def _supabase_fetch(table: str, params: str) -> list:
    url = _get_secret("SUPABASE_URL", "")
    key = _get_secret("SUPABASE_KEY", "")
    if not url or not key:
        return []
    try:
        resp = requests.get(
            f"{url.rstrip('/')}/rest/v1/{table}?{params}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=10,
        )
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


def _load_run_history(email: str, store: UserStore) -> list:
    rows = _supabase_fetch(
        "run_history",
        f"user_email=eq.{email}&order=created_at.desc&limit=40",
    )
    if rows:
        for r in rows:
            r.setdefault("date", r.get("run_date", ""))
        return rows
    return store.load_apply_history()


def _load_hr_invites(email: str, store: UserStore) -> list:
    rows = _supabase_fetch(
        "hr_invites",
        f"user_email=eq.{email}&order=created_at.desc&limit=60",
    )
    if rows:
        return rows
    return store.load_hr_invites()


st.set_page_config(page_title="Run History - CareerOS", page_icon="H", layout="wide")
require_login()
inject_global_css()

email = get_user_email()
install_error_tracking(email=email, page="Run History")
track_page_view(email=email, page="Run History")
store = UserStore(email)

st.markdown('<div class="pg-title"><span class="pg-name">Run History</span><span class="pg-sub">Every Smart Apply run, results, and invite activity</span></div>', unsafe_allow_html=True)

history = _load_run_history(email, store)
invites = _load_hr_invites(email, store)

if not history:
    st.markdown(
        """
        <div class="co-empty-state">
            <div style="font-size:1.8rem;font-weight:700;">No runs yet</div>
            <div style="margin-top:8px;">Start Smart Apply setup and your first run will appear here automatically.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/5_Smart_Apply.py", label="Open Smart Apply")
    st.stop()

total_runs = len(history)
total_found = sum(int(r.get("jobs_found", 0) or 0) for r in history)
total_applied = sum(int(r.get("jobs_applied", 0) or 0) for r in history)
total_skipped = sum(int(r.get("jobs_skipped", 0) or 0) for r in history)

st.markdown('<div class="co-grid-2">', unsafe_allow_html=True)
for label, value in [
    ("Total Runs", total_runs),
    ("Jobs Found", total_found),
    ("Applied", total_applied),
    ("Skipped", total_skipped),
]:
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

st.markdown('<div class="co-section-kicker">Timeline</div><div class="co-section-title">Recent Runs</div>', unsafe_allow_html=True)
for run in history[:20]:
    run_date = run.get("date", "Unknown")
    found = int(run.get("jobs_found", 0) or 0)
    applied = int(run.get("jobs_applied", 0) or 0)
    skipped = int(run.get("jobs_skipped", 0) or 0)
    with st.expander(f"{run_date} | Found {found} | Applied {applied} | Skipped {skipped}"):
        applied_list = run.get("applied_list", []) or []
        skipped_list = run.get("skipped_list", []) or []
        errors = run.get("errors", []) or []
        if applied_list:
            st.markdown("**Applied jobs**")
            for job in applied_list[:12]:
                title = job.get("title", "Role")
                company = job.get("company", "Company")
                url = job.get("url", "")
                text = f"[{title} @ {company}]({url})" if url else f"{title} @ {company}"
                st.markdown(f"- {text}")
        if skipped_list:
            st.markdown("**Skipped jobs**")
            for job in skipped_list[:12]:
                reason = job.get("reason", "")
                st.markdown(f"- {job.get('title', 'Role')} @ {job.get('company', 'Company')} ({reason})")
        if errors:
            st.markdown("**Run errors**")
            for err in errors:
                st.caption(str(err))

st.markdown('<div class="co-section-kicker">Inbox</div><div class="co-section-title">Recruiter Invites</div>', unsafe_allow_html=True)
if not invites:
    st.markdown('<div class="co-empty-state">No recruiter invites detected yet.</div>', unsafe_allow_html=True)
else:
    for invite in invites[:30]:
        title = invite.get("title", "Role")
        company = invite.get("company", "Company")
        hr = invite.get("hr_name", "")
        state = "Applied" if invite.get("applied") else "Pending/Skipped"
        date = invite.get("detected_at") or invite.get("created_at") or ""
        with st.expander(f"{company} | {title} | {state}"):
            if hr:
                st.markdown(f"**Recruiter:** {hr}")
            if date:
                st.caption(f"Detected: {date}")
            if invite.get("reason"):
                st.caption(f"Reasoning: {invite.get('reason')}")
