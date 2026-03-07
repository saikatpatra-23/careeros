# -*- coding: utf-8 -*-
"""
Page 5 - Smart Job Apply
Configure preferences, download local runner config, view run history.
"""
import io
import os
import sys
import json
import zipfile
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email
from modules.telemetry.tracker import install_error_tracking, track_page_view
from modules.ui.styles import inject_global_css
from persistence.store import UserStore
from config import ANTHROPIC_API_KEY, _get_secret
from pathlib import Path

def _get_fernet_key() -> str:
    return _get_secret("FERNET_KEY", "")

def _get_sync_url() -> str:
    """Build the results sync URL using the app URL + SYNC_SECRET."""
    secret   = _get_secret("SYNC_SECRET", "")
    app_url  = _get_secret("APP_URL", "")
    if not secret or not app_url:
        return ""
    return f"{app_url.rstrip('/')}/api_ingest?token={secret}&data="

def _supabase_fetch(table: str, params: str) -> list:
    """Fetch rows from Supabase via REST API. Returns [] if not configured."""
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
        f"user_email=eq.{email}&order=created_at.desc&limit=30",
    )
    if rows:
        for r in rows:
            r.setdefault("date", r.get("run_date", ""))
        return rows
    return store.load_apply_history()

def _load_hr_invites(email: str, store: UserStore) -> list:
    rows = _supabase_fetch(
        "hr_invites",
        f"user_email=eq.{email}&order=created_at.desc&limit=50",
    )
    return rows if rows else store.load_hr_invites()

st.set_page_config(page_title="Smart Apply - CareerOS", page_icon="S", layout="wide")
require_login()
inject_global_css()

email = get_user_email()
install_error_tracking(email=email, page="Smart Apply")
track_page_view(email=email, page="Smart Apply")
store = UserStore(email)
saved_opt = store.load_profile_optimizer()

# Styles
st.markdown("""
<style>
.how-step {
    background: #1A1D27; border-radius: 10px;
    padding: 14px 18px; border: 1px solid rgba(255,255,255,0.07); margin: 6px 0;
}
.how-step-num {
    display: inline-block; background: rgba(79,142,247,0.2); color: #4F8EF7;
    border-radius: 50%; width: 26px; height: 26px;
    text-align: center; line-height: 26px; font-size: 0.82rem;
    font-weight: 700; margin-right: 10px;
}
.stat-box {
    background: #1A1D27; border-radius: 10px;
    padding: 18px; border: 1px solid rgba(255,255,255,0.07); text-align: center;
}
.stat-num { font-size: 1.9rem; font-weight: 800; color: #4F8EF7; }
.stat-lbl { font-size: 0.78rem; color: #6B7280; margin-top: 2px; }

.run-card {
    background: #1A1D27; border-radius: 10px;
    padding: 12px 16px; border: 1px solid rgba(255,255,255,0.07); margin: 6px 0;
}
.applied-pill {
    display: inline-block; background: rgba(16,185,129,0.15); color: #10B981;
    border-radius: 100px; padding: 2px 10px; font-size: 0.76rem;
    font-weight: 600; margin-right: 4px;
}
.skipped-pill {
    display: inline-block; background: rgba(239,68,68,0.12); color: #F87171;
    border-radius: 100px; padding: 2px 10px; font-size: 0.76rem;
    font-weight: 600; margin-right: 4px;
}
.warning-box {
    background: rgba(245,158,11,0.07); border-radius: 8px;
    padding: 12px 16px; border-left: 3px solid #F59E0B;
    font-size: 0.875rem; color: #C49A20; margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="pg-title"><span class="pg-icon">SA</span><span class="pg-name">Smart Auto-Apply</span><span class="pg-sub">AI scoring + auto-apply at 9:30 AM &amp; 2 PM</span></div>', unsafe_allow_html=True)

# Resume check
resume_saved = store.load_resume()
resume_data  = resume_saved.get("structured_data", {})
profile      = store.load_profile()

if not resume_data:
    st.warning("Build your resume first. Smart Apply needs it to match jobs intelligently.")
    st.page_link("pages/1_Resume_Builder.py", label="Go to Resume Builder")
    st.stop()

# Tabs
tab_prefs, tab_setup, tab_history, tab_inbox = st.tabs([
    "Job Preferences", "Setup & Run", "Run History", "Recruiter Inbox"
])

# =============================================================================
# TAB 1 - JOB PREFERENCES
# =============================================================================
with tab_prefs:
    st.markdown("### Configure What Jobs to Apply To")
    st.caption("CareerOS uses these settings every time it runs to find and filter jobs.")

    saved_prefs = store.load_apply_prefs()

    with st.form("prefs_form"):
        col1, col2 = st.columns(2)

        with col1:
            target_title = st.text_input(
                "Target Job Title",
                value=saved_prefs.get("target_title", resume_data.get("target_title", "")),
                help="Primary role to search for on Naukri. E.g. 'Business Analyst'"
            )
            locations = st.multiselect(
                "Preferred Locations",
                options=["Mumbai", "Pune", "Bengaluru", "Hyderabad", "Chennai",
                         "Delhi NCR", "Thane", "Navi Mumbai", "Noida", "Gurugram",
                         "Kolkata", "Ahmedabad", "Remote"],
                default=saved_prefs.get("locations",
                    profile.get("preferred_locations", ["Pune"])
                    if isinstance(profile.get("preferred_locations"), list)
                    else ["Pune"]
                ),
            )
            work_mode = st.selectbox(
                "Work Mode Preference",
                options=["Any", "Remote", "Hybrid", "Work from Office"],
                index=["Any", "Remote", "Hybrid", "Work from Office"].index(
                    saved_prefs.get("work_mode", "Any")
                ),
            )

        with col2:
            salary_min = st.number_input(
                "Minimum CTC (LPA)",
                min_value=0, max_value=100,
                value=int(saved_prefs.get("salary_min", profile.get("salary_min", 0)) or 0),
                step=1,
                help="Jobs below this CTC will be skipped. Set 0 to apply to all."
            )
            max_jobs = st.slider(
                "Max Applications per Run",
                min_value=1, max_value=20,
                value=int(saved_prefs.get("max_jobs", 5)),
                help="How many jobs to apply to in one automated run. Start with 5."
            )
            exp_min = st.number_input(
                "Min Experience Required (years)",
                min_value=0, max_value=20,
                value=int(saved_prefs.get("exp_min", 3)),
                help="Skip jobs requiring less experience than this."
            )

        st.markdown("#### Additional Target Titles")
        st.caption("CareerOS will also search these roles. Separate with commas.")
        alt_titles = st.text_input(
            "Alternate titles (optional)",
            value=", ".join(saved_prefs.get("alt_titles", [])),
            placeholder="e.g. Senior Business Analyst, Functional Consultant, Product Analyst",
            label_visibility="collapsed",
        )

        st.markdown("#### Search Breadth")
        c3, c4 = st.columns(2)
        with c3:
            search_titles_per_run = st.slider(
                "Titles per run",
                min_value=1, max_value=8,
                value=int(saved_prefs.get("search_titles_per_run", 4)),
                help="How many target or alternate titles to search each run."
            )
        with c4:
            search_locations_per_run = st.slider(
                "Locations per run",
                min_value=1, max_value=8,
                value=int(saved_prefs.get("search_locations_per_run", 3)),
                help="How many preferred locations to include each run."
            )

        max_jobs_to_scan = st.slider(
            "Max Jobs to Scan Per Run",
            min_value=20, max_value=150,
            value=int(saved_prefs.get("max_jobs_to_scan", 60)),
            step=5,
            help="How many unique jobs CareerOS should evaluate before it stops searching."
        )

        st.markdown("#### Workflow Webhooks")
        make_webhook_url = st.text_input(
            "Make.com Webhook URL (optional)",
            value=saved_prefs.get("make_webhook_url", ""),
            help="CareerOS will POST run and apply events here if configured."
        )
        mailbolt_webhook_url = st.text_input(
            "Mailbolt Webhook URL (optional)",
            value=saved_prefs.get("mailbolt_webhook_url", ""),
            help="Optional Mailbolt or email automation webhook for summaries and digests."
        )

        st.markdown("#### Domains to AVOID")
        st.caption("Jobs in these domains will be hard-rejected regardless of title match.")
        avoid_domains = st.multiselect(
            "Avoid domains",
            options=["Capital Markets / Investment Banking", "Pharma / Clinical",
                     "K-12 Education", "FMCG Brand Management", "Medical Devices",
                     "Real Estate", "Insurance Products", "Manufacturing / Shopfloor"],
            default=saved_prefs.get("avoid_domains", []),
            label_visibility="collapsed",
        )

        saved = st.form_submit_button("Save Preferences", type="primary", use_container_width=True)

    if saved:
        prefs = {
            "target_title":  target_title,
            "locations":     locations,
            "work_mode":     work_mode,
            "salary_min":    salary_min,
            "max_jobs":      max_jobs,
            "max_jobs_to_scan": max_jobs_to_scan,
            "exp_min":       exp_min,
            "search_titles_per_run": search_titles_per_run,
            "search_locations_per_run": search_locations_per_run,
            "make_webhook_url": make_webhook_url.strip(),
            "mailbolt_webhook_url": mailbolt_webhook_url.strip(),
            "alt_titles":    [t.strip() for t in alt_titles.split(",") if t.strip()],
            "avoid_domains": avoid_domains,
        }
        store.save_apply_prefs(prefs)
        st.success("Preferences saved! Generate your config file in the Setup tab.")


# =============================================================================
# TAB 2 - SETUP & RUN
# =============================================================================
with tab_setup:
    st.markdown("### How Smart Apply Works")

    st.markdown("""
    <div class="warning-box">
         <strong>Why does it run on your PC, not in the cloud?</strong><br>
        Naukri actively blocks cloud server IPs (AWS, GCP, Azure) as bots.
        Your home/office IP is trusted. The local runner uses your residential IP to browse
        Naukri exactly like you would, with a real browser.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    steps = [
        ("Download the installer package", "One ZIP has everything inside. Click the button below."),
        ("Unzip to any folder", "e.g. <code>C:\\CareerOS\\</code>. Keep the folder intact."),
        ("Run the installer once", "Right-click PowerShell, choose <strong>Run as Administrator</strong>, navigate to the folder, then run <code>.\\install_service.ps1</code>."),
        ("Done - it runs forever", "CareerOS Watcher starts on every boot, runs at <strong>9:30 AM</strong> and <strong>2 PM</strong> daily. Results appear in Run History automatically."),
    ]

    for i, (title, body) in enumerate(steps, 1):
        st.markdown(f"""
        <div class="how-step">
            <span class="how-step-num">{i}</span>
            <strong>{title}</strong><br>
            <span style="font-size:0.875rem;color:#6B7280;margin-left:38px;display:block;">{body}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Download Installer Package")
    st.caption("Everything pre-configured for you. Just unzip, run the installer as Admin, and you're live.")

    prefs        = store.load_apply_prefs()
    config_data = {
        "user_email":           email,
        "naukri_email":         profile.get("naukri_email", ""),
        "naukri_pass_enc":      profile.get("naukri_pass_enc", ""),
        "fernet_key":           _get_fernet_key(),
        "anthropic_key":        ANTHROPIC_API_KEY,
        "headless":             True,
        "supabase_url":         _get_secret("SUPABASE_URL", ""),
        "supabase_key":         _get_secret("SUPABASE_KEY", ""),
        "careeros_sync_url":    _get_sync_url(),
        "make_webhook_url":     prefs.get("make_webhook_url", ""),
        "mailbolt_webhook_url": prefs.get("mailbolt_webhook_url", ""),
        "notif_pref":           profile.get("notif_pref", "ntfy"),
        "notification_contact": profile.get("ntfy_topic", ""),
        "current_location":     prefs.get("current_location", prefs.get("locations", ["Mumbai"])[0] if prefs.get("locations") else "Mumbai"),
        "preferred_locations":  prefs.get("locations", ["Pune"]),
        "salary_min":           prefs.get("salary_min", 0),
        "max_jobs_per_run":     prefs.get("max_jobs", 5),
        "max_jobs_to_scan":     prefs.get("max_jobs_to_scan", 60),
        "search_titles_per_run": prefs.get("search_titles_per_run", 4),
        "search_locations_per_run": prefs.get("search_locations_per_run", 3),
        "exp_min":              prefs.get("exp_min", 3),
        "alt_titles":           prefs.get("alt_titles", []),
        "naukri_profile_data":   saved_opt.get("naukri", {}),
        "resume_data": {
            "target_title":  resume_data.get("target_title", ""),
            "domain_family": resume_saved.get("domain_family", "enterprise_IT"),
            "summary":       resume_data.get("summary", ""),
            "ats_keywords":  resume_data.get("ats_keywords", []),
            "experience":    resume_data.get("experience", []),
            "skills":        resume_data.get("skills", {}),
        },
    }

    # Build ZIP in memory
    job_applier_dir = Path(__file__).parent.parent / "job_applier"

    install_readme = """CareerOS Local Runner - Quick Install
=======================================

REQUIREMENT: Google Chrome must be installed on this PC.
  Download from: https://www.google.com/chrome/
  (Chrome runs hidden in the background; no window will open)

INSTALL AS WINDOWS SERVICE (runs on boot, no login needed):
  1. Open PowerShell as Administrator
     (Right-click the Start menu and open Windows PowerShell (Admin))
  2. Navigate to this folder:
     cd "C:\\CareerOS"   (or wherever you unzipped)
  3. Run the installer:
     .\\install_service.ps1
  4. Done. CareerOS starts automatically on every boot.

VERIFY IT'S RUNNING:
  Get-Service CareerOSWatcher

STOP / UNINSTALL:
  Stop-Service CareerOSWatcher
  .\\install_service.ps1 -Uninstall

MANUAL TRIGGER (runs immediately):
  Create an empty file named  trigger.txt  in this folder.
  The watcher picks it up within 60 seconds.

SCHEDULED TIMES: 9:30 AM and 2:00 PM daily.

LOGS: logs\\service.log
RESULTS: Appear in CareerOS web app -> Smart Apply -> Run History
"""

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("careeros_config.json",
                    json.dumps(config_data, indent=2, ensure_ascii=False))
        zf.writestr("INSTALL.txt", install_readme)

        for fname in ["watcher.py", "run.py", "update_profile.py", "install_service.ps1",
                      "start_watcher.bat", "requirements.txt"]:
            fpath = job_applier_dir / fname
            if fpath.exists():
                zf.write(fpath, fname)

        # Ensure logs directory exists inside ZIP
        zf.writestr("logs/.gitkeep", "")

    zip_buffer.seek(0)

    st.info("Everything is pre-configured. Just unzip, run `install_service.ps1` as Admin, and CareerOS starts working automatically.")

    st.download_button(
        label="Download CareerOS Installer (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="careeros_installer.zip",
        mime="application/zip",
        use_container_width=True,
        type="primary",
    )

    st.divider()
    st.markdown("### Service Management")
    st.caption("After installing the service, use these commands to manage it.")

    with st.expander("PowerShell commands"):
        st.code("""# Check status
Get-Service CareerOSWatcher

# Stop the service
Stop-Service CareerOSWatcher

# Restart
Restart-Service CareerOSWatcher

# View logs
notepad logs\\service.log

# Uninstall completely
.\\install_service.ps1 -Uninstall
""", language="powershell")


# =============================================================================
# TAB 3 - RUN HISTORY
# =============================================================================
with tab_history:
    st.markdown("### Application Run History")
    st.caption("Every run your local CareerOS runner completes is logged here.")

    history = _load_run_history(email, store)

    if not history:
        st.info("No runs yet. Set up the local runner and complete your first run. Results will appear here automatically.")
        st.markdown("""
        <div style="background:#F8FAFC;border-radius:12px;padding:20px;text-align:center;color:#6B7280;margin-top:16px;">
            <div style="font-size:2rem;">RUN</div>
            <div style="font-size:0.9rem;margin-top:8px;">Waiting for first run...</div>
            <div style="font-size:0.8rem;margin-top:4px;">Go to Setup tab to get started.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary stats
        total_applied = sum(r.get("jobs_applied", 0) for r in history)
        total_found   = sum(r.get("jobs_found", 0) for r in history)
        total_skipped = sum(r.get("jobs_skipped", 0) for r in history)
        total_runs    = len(history)

        c1, c2, c3, c4 = st.columns(4)
        for col, num, label in [
            (c1, total_runs,    "Total Runs"),
            (c2, total_found,   "Jobs Scanned"),
            (c3, total_applied, "Applied"),
            (c4, total_skipped, "Skipped"),
        ]:
            col.markdown(f"""
            <div class="stat-box">
                <div class="stat-num">{num}</div>
                <div class="stat-lbl">{label}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        for run in history:
            applied_count = run.get("jobs_applied", 0)
            skipped_count = run.get("jobs_skipped", 0)
            run_date      = run.get("date", "Unknown date")
            applied_list  = run.get("applied_list", [])
            skipped_list  = run.get("skipped_list", [])

            with st.expander(f"**{run_date}** - Applied: {applied_count} | Skipped: {skipped_count}"):
                if applied_list:
                    st.markdown("**Applied To:**")
                    for job in applied_list:
                        url = job.get("url", "")
                        link = f"[{job.get('title')} @ {job.get('company')}]({url})" if url else f"{job.get('title')} @ {job.get('company')}"
                        st.markdown(f"- {link}")

                if skipped_list:
                    st.markdown("**Skipped:**")
                    for job in skipped_list[:10]:
                        reason = job.get("reason", "")
                        st.markdown(f"- **{job.get('title')} @ {job.get('company')}** - *{reason}*")
                    if len(skipped_list) > 10:
                        st.caption(f"...and {len(skipped_list) - 10} more")

                # HR invites processed in this run
                hr_invites = run.get("hr_invites", [])
                if hr_invites:
                    st.markdown("**HR Invites Processed:**")
                    for inv in hr_invites:
                        status = "Applied" if inv.get("applied") else "Skipped"
                        st.markdown(
                            f"- {status} - **{inv.get('title')} @ {inv.get('company')}**"
                            + (f" (HR: {inv.get('hr_name')})" if inv.get("hr_name") else "")
                        )

                errors = run.get("errors", [])
                if errors:
                    st.markdown("**Errors:**")
                    for e in errors:
                        st.caption(e)


# =============================================================================
# TAB 4 - RECRUITER INBOX
# =============================================================================
with tab_inbox:
    st.markdown("### Recruiter Inbox")
    st.caption(
        "HR invites detected by CareerOS from Gmail monitor (real-time) "
        "and from Naukri inbox check (on every scheduled run)."
    )

    st.markdown("""
    <div class="warning-box">
         <strong>Why this tab matters:</strong> An HR invite has 10x higher callback rate than
        a cold application. CareerOS detects these automatically and applies on your behalf
        within minutes, before the HR moves on.
    </div>
    """, unsafe_allow_html=True)

    # Gmail Monitor setup card
    with st.expander("Set Up Gmail Monitor (one-time, 2 minutes)", expanded=False):
        st.markdown("""
        The Gmail Monitor runs 24/7 on **Google's own servers**; no laptop needed.
        It detects Naukri HR invites and profile views the moment they hit your inbox.

        **Steps:**
        1. Open [script.google.com](https://script.google.com) in your browser
        2. Click **New project** and paste the script from the Setup tab below
        3. Set your `MAKE_WEBHOOK_URL` at the top of the script (from your config file)
        4. Click **Run setupTrigger()** and authorize when prompted
        5. Done. It runs every 5 minutes forever.
        """)
        st.code(
            "// Find this file in your careeros download:\n"
            "// careeros/scripts/gmail_monitor.gs\n"
            "// Paste entire contents into Google Apps Script",
            language="javascript"
        )

    st.divider()

    # Show HR invite history
    hr_invites = _load_hr_invites(email, store)

    # Also pull invites from run history (only needed when Supabase is not configured)
    run_history = _load_run_history(email, store) if not _get_secret("SUPABASE_URL", "") else []
    for run in run_history:
        for inv in run.get("hr_invites", []):
            inv["detected_at"] = run.get("date", "")
            hr_invites.append(inv)

    # Deduplicate by company + title
    seen = set()
    unique_invites = []
    for inv in hr_invites:
        key = (inv.get("company", ""), inv.get("title", ""))
        if key not in seen:
            seen.add(key)
            unique_invites.append(inv)

    if not unique_invites:
        st.info("No HR invites detected yet.")
        st.markdown("""
        <div style="background:#F8FAFC;border-radius:12px;padding:24px;
                    text-align:center;color:#6B7280;margin-top:16px;">
            <div style="font-size:2.5rem;">INBOX</div>
            <div style="font-size:0.95rem;font-weight:600;margin-top:12px;">Inbox empty</div>
            <div style="font-size:0.85rem;margin-top:6px;">
                Set up the Gmail Monitor above and keep your Naukri profile active.<br>
                When HRs reach out, they'll appear here automatically.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary stats
        total    = len(unique_invites)
        applied  = sum(1 for i in unique_invites if i.get("applied"))
        skipped  = total - applied

        c1, c2, c3 = st.columns(3)
        for col, num, label, color in [
            (c1, total,   "Total Invites",   "#1E1B4B"),
            (c2, applied, "Auto-Applied",    "#065F46"),
            (c3, skipped, "Skipped (no fit)","#991B1B"),
        ]:
            col.markdown(f"""
            <div class="stat-box">
                <div class="stat-num" style="color:{color};">{num}</div>
                <div class="stat-lbl">{label}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        for inv in unique_invites:
            applied_flag = inv.get("applied", False)
            status_pill  = (
                '<span class="applied-pill">Applied</span>'
                if applied_flag else
                '<span class="skipped-pill">Skipped</span>'
            )
            url  = inv.get("url", "")
            link = f"[{inv.get('title','Role')} @ {inv.get('company','')}]({url})" if url else f"{inv.get('title','Role')} @ {inv.get('company','')}"
            date = inv.get("detected_at", "")

            with st.expander(f"{inv.get('company','Unknown')} - {inv.get('title','Unknown role')}"):
                st.markdown(status_pill, unsafe_allow_html=True)
                if inv.get("hr_name"):
                    st.markdown(f"**HR:** {inv.get('hr_name')}")
                st.markdown(f"**Job:** {link}")
                if date:
                    st.caption(f"Detected: {date}")
                if inv.get("reason"):
                    st.caption(f"CareerOS reasoning: {inv.get('reason')}")


