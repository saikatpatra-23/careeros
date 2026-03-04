# -*- coding: utf-8 -*-
"""
Page 5 — Smart Job Apply
Configure preferences, download local runner config, view run history.
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email
from persistence.store import UserStore
from config import ANTHROPIC_API_KEY

st.set_page_config(page_title="Smart Apply – CareerOS", page_icon="🤖", layout="wide")
require_login()

email = get_user_email()
store = UserStore(email)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.page-header {
    background: linear-gradient(135deg, #1E1B4B 0%, #3730A3 100%);
    border-radius: 14px; padding: 24px 28px; color: white; margin-bottom: 24px;
}
.page-header h2 { margin: 0 0 4px 0; font-size: 1.6rem; font-weight: 700; }
.page-header p  { margin: 0; opacity: 0.88; font-size: 0.95rem; }

.how-step {
    background: white; border-radius: 10px;
    padding: 16px 20px; border: 1.5px solid #E5E7EB;
    margin: 8px 0;
}
.how-step-num {
    display: inline-block; background: #3730A3; color: white;
    border-radius: 50%; width: 28px; height: 28px;
    text-align: center; line-height: 28px; font-size: 0.85rem;
    font-weight: 700; margin-right: 10px;
}
.stat-box {
    background: white; border-radius: 12px;
    padding: 20px; border: 1.5px solid #E5E7EB;
    text-align: center;
}
.stat-num { font-size: 2rem; font-weight: 800; color: #1E1B4B; }
.stat-lbl { font-size: 0.8rem; color: #6B7280; margin-top: 2px; }

.run-card {
    background: white; border-radius: 10px;
    padding: 14px 18px; border: 1.5px solid #E5E7EB;
    margin: 8px 0;
}
.applied-pill {
    display: inline-block; background: #D1FAE5; color: #065F46;
    border-radius: 100px; padding: 2px 10px; font-size: 0.78rem;
    font-weight: 600; margin-right: 4px;
}
.skipped-pill {
    display: inline-block; background: #FEE2E2; color: #991B1B;
    border-radius: 100px; padding: 2px 10px; font-size: 0.78rem;
    font-weight: 600; margin-right: 4px;
}
.warning-box {
    background: #FFFBEB; border-radius: 12px;
    padding: 16px 20px; border-left: 4px solid #F59E0B;
    font-size: 0.875rem; color: #78350F; margin: 12px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>🤖 Smart Job Apply</h2>
    <p>CareerOS reads every JD with Claude AI, scores it against your profile, and only applies where it genuinely fits.
    No spray-and-pray. No domain mismatches.</p>
</div>
""", unsafe_allow_html=True)

# ── Resume check ──────────────────────────────────────────────────────────────
resume_saved = store.load_resume()
resume_data  = resume_saved.get("structured_data", {})
profile      = store.load_profile()

if not resume_data:
    st.warning("Build your resume first — Smart Apply needs it to match jobs intelligently.")
    st.page_link("pages/1_Resume_Builder.py", label="Go to Resume Builder →", icon="📄")
    st.stop()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_prefs, tab_setup, tab_history = st.tabs([
    "⚙️ Job Preferences", "🚀 Setup & Run", "📊 Run History"
])

# =============================================================================
# TAB 1 — JOB PREFERENCES
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
            "exp_min":       exp_min,
            "alt_titles":    [t.strip() for t in alt_titles.split(",") if t.strip()],
            "avoid_domains": avoid_domains,
        }
        store.save_apply_prefs(prefs)
        st.success("Preferences saved! Generate your config file in the Setup tab.")


# =============================================================================
# TAB 2 — SETUP & RUN
# =============================================================================
with tab_setup:
    st.markdown("### How Smart Apply Works")

    st.markdown("""
    <div class="warning-box">
        ⚠️ <strong>Why does it run on your PC, not in the cloud?</strong><br>
        Naukri actively blocks cloud server IPs (AWS, GCP, Azure) as bots.
        Your home/office IP is trusted. The local runner uses your residential IP to browse
        Naukri exactly like you would — with a real browser.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    steps = [
        ("Download your config file", "Click the button below → save <code>careeros_config.json</code> to your PC."),
        ("Place it in the CareerOS folder", "Put it alongside <code>watcher.py</code> and <code>run.py</code> in the job_applier folder."),
        ("Run the watcher", "Open Command Prompt: <code>python watcher.py</code><br>It will auto-run at <strong>9:30 AM</strong> and <strong>2:00 PM</strong> daily."),
        ("Or trigger manually", "Create an empty file named <code>trigger.txt</code> in the same folder — watcher picks it up instantly."),
        ("Results appear here", "After each run, come back to the <strong>Run History</strong> tab to see what was applied and what was skipped."),
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
    st.markdown("### Download Your Config File")
    st.caption("This file contains your preferences and encrypted Naukri credentials. Keep it safe — treat it like a password.")

    prefs   = store.load_apply_prefs()
    naukri_creds = profile.get("naukri_creds", {})

    config_data = {
        "user_email":            email,
        "naukri_email":          profile.get("naukri_email", ""),
        "naukri_pass_enc":       naukri_creds.get("pass_enc", ""),
        "fernet_key":            naukri_creds.get("fernet_key", ""),
        "anthropic_key":         "",
        "make_webhook_url":      "",
        "notif_pref":            profile.get("notif_pref", "email"),
        "notification_contact":  profile.get("notification_contact", ""),
        "preferred_locations":   prefs.get("locations", ["Pune"]),
        "salary_min":            prefs.get("salary_min", 0),
        "max_jobs_per_run":      prefs.get("max_jobs", 5),
        "exp_min":               prefs.get("exp_min", 3),
        "avoid_domains":         prefs.get("avoid_domains", []),
        "alt_titles":            prefs.get("alt_titles", []),
        "resume_data": {
            "target_title":  resume_data.get("target_title", ""),
            "domain_family": resume_saved.get("domain_family", "enterprise_IT"),
            "summary":       resume_data.get("summary", ""),
            "ats_keywords":  resume_data.get("ats_keywords", []),
            "experience":    resume_data.get("experience", []),
            "skills":        resume_data.get("skills", {}),
        },
    }

    config_json = json.dumps(config_data, indent=2, ensure_ascii=False)

    st.warning("⚠️ Add your **Anthropic API key** to the downloaded file before running — the `anthropic_key` field.")

    st.download_button(
        label="⬇️ Download careeros_config.json",
        data=config_json,
        file_name="careeros_config.json",
        mime="application/json",
        use_container_width=True,
        type="primary",
    )

    st.divider()
    st.markdown("### Scheduling (Windows Task Scheduler)")
    st.caption("Set this up once — then forget it. The watcher runs twice daily automatically.")

    with st.expander("View Task Scheduler setup commands"):
        st.code("""# Open Command Prompt as Administrator and run:

schtasks /create /tn "CareerOS Watcher" ^
  /tr "pythonw D:\\path\\to\\careeros\\job_applier\\watcher.py" ^
  /sc onlogon /ru %USERNAME% /f

# This starts the watcher automatically on PC login.
# The watcher itself handles 9:30 AM and 2:00 PM scheduling internally.

# To check it's running:
tasklist | findstr python

# To stop it:
schtasks /end /tn "CareerOS Watcher"
""", language="bat")


# =============================================================================
# TAB 3 — RUN HISTORY
# =============================================================================
with tab_history:
    st.markdown("### Application Run History")
    st.caption("Every run your local CareerOS runner completes is logged here.")

    history = store.load_apply_history()

    if not history:
        st.info("No runs yet. Set up the local runner and complete your first run — results will appear here automatically.")
        st.markdown("""
        <div style="background:#F8FAFC;border-radius:12px;padding:20px;text-align:center;color:#6B7280;margin-top:16px;">
            <div style="font-size:2rem;">🤖</div>
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

            with st.expander(f"**{run_date}** — Applied: {applied_count} | Skipped: {skipped_count}"):
                if applied_list:
                    st.markdown("**✅ Applied To:**")
                    for job in applied_list:
                        url = job.get("url", "")
                        link = f"[{job.get('title')} @ {job.get('company')}]({url})" if url else f"{job.get('title')} @ {job.get('company')}"
                        st.markdown(f"- {link}")

                if skipped_list:
                    st.markdown("**❌ Skipped:**")
                    for job in skipped_list[:10]:
                        reason = job.get("reason", "")
                        st.markdown(f"- **{job.get('title')} @ {job.get('company')}** — *{reason}*")
                    if len(skipped_list) > 10:
                        st.caption(f"...and {len(skipped_list) - 10} more")

                errors = run.get("errors", [])
                if errors:
                    st.markdown("**⚠️ Errors:**")
                    for e in errors:
                        st.caption(e)
