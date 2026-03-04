# -*- coding: utf-8 -*-
"""
CareerOS — Main entry point / Dashboard.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="CareerOS",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import require_login, get_user_email, get_user_name, get_user_avatar
from persistence.store import UserStore

require_login()

# ── User context ──────────────────────────────────────────────────────────────
email   = get_user_email()
name    = get_user_name()
store   = UserStore(email)
summary = store.summary()
first_name = name.split()[0] if name else "there"

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hero banner */
.hero {
    background: linear-gradient(135deg, #1B4F9C 0%, #2563EB 60%, #3B82F6 100%);
    border-radius: 16px;
    padding: 36px 40px;
    margin-bottom: 8px;
    color: white;
}
.hero h1 { font-size: 2.2rem; font-weight: 700; margin: 0 0 6px 0; }
.hero p  { font-size: 1.05rem; opacity: 0.9; margin: 0; }

/* Step cards */
.step-card {
    background: white;
    border-radius: 14px;
    padding: 22px 24px;
    border: 1.5px solid #E2E8F0;
    height: 100%;
    transition: box-shadow 0.2s;
    position: relative;
}
.step-card:hover { box-shadow: 0 4px 20px rgba(27,79,156,0.1); }
.step-badge {
    display: inline-block;
    background: #EBF3FB;
    color: #1B4F9C;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    margin-bottom: 10px;
}
.step-badge.done { background: #D1FAE5; color: #065F46; }
.step-title { font-size: 1.05rem; font-weight: 700; color: #1F273A; margin: 6px 0 8px 0; }
.step-body  { font-size: 0.875rem; color: #6B7280; line-height: 1.55; }

/* Progress bar custom */
.prog-wrap {
    background: #E2E8F0;
    border-radius: 100px;
    height: 8px;
    margin: 16px 0 6px 0;
    overflow: hidden;
}
.prog-fill {
    height: 8px;
    border-radius: 100px;
    background: linear-gradient(90deg, #1B4F9C, #3B82F6);
}

/* Tip card */
.tip-card {
    background: linear-gradient(135deg, #FFF7ED, #FEF3C7);
    border-radius: 12px;
    padding: 16px 20px;
    border-left: 4px solid #F59E0B;
    font-size: 0.875rem;
    color: #78350F;
    line-height: 1.55;
}

/* Stat pill */
.stat-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
.stat-pill {
    background: rgba(255,255,255,0.2);
    border-radius: 100px;
    padding: 4px 14px;
    font-size: 0.8rem;
    color: white;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ── Header / Hero ─────────────────────────────────────────────────────────────
col_hero, col_user = st.columns([4, 1])
with col_hero:
    steps_done = sum([summary["has_resume"], bool(store.load_profile_optimizer().get("naukri"))])
    st.markdown(f"""
    <div class="hero">
        <h1>👋 Welcome back, {first_name}!</h1>
        <p>Your AI-powered career coach for the Indian job market — built by someone who knows how recruiters think.</p>
        <div class="stat-row">
            <span class="stat-pill">🇮🇳 India-focused</span>
            <span class="stat-pill">🤖 Powered by Claude AI</span>
            <span class="stat-pill">📊 {steps_done}/2 steps complete</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<small style='color:#888;'>{email}</small>", unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        st.logout()

st.divider()

# ── Did-you-know recruiter tip ─────────────────────────────────────────────────
import random
tips = [
    "💡 <strong>Recruiter insight:</strong> Indian HRs spend just 6 seconds on the first scan. Headline → Company → Skills → Summary — that's the order they look.",
    "💡 <strong>Naukri tip:</strong> Only 4-star and 5-star profiles appear in default recruiter searches. An incomplete profile = invisible profile.",
    "💡 <strong>Resume truth:</strong> 'Responsible for...' is the #1 phrase Indian recruiters hate. Replace with achievement verbs: Delivered, Led, Reduced, Designed.",
    "💡 <strong>ATS fact:</strong> Multi-column resume templates from Canva fail RChilli parsing (the ATS Naukri uses). Single-column always wins.",
    "💡 <strong>Market fact:</strong> Mid-career candidates (5-10 yrs) fill 65% of Indian IT hires in 2025. Your experience is in demand — you just need to present it right.",
    "💡 <strong>LinkedIn tip:</strong> Turning on 'Open to Work' for recruiters only (not the green banner) doubles InMail outreach — without signaling desperation publicly.",
    "💡 <strong>Salary fact:</strong> CBAP certification adds 15-25% salary premium for BA roles. CSM/PSM adds 20-30% for Scrum Master roles.",
    "💡 <strong>Career insight:</strong> Referrals fill 60-70% of mid-senior Indian roles before they're even posted publicly. Your LinkedIn network is your hidden job board.",
]
st.markdown(f'<div class="tip-card">{random.choice(tips)}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Steps ─────────────────────────────────────────────────────────────────────
st.markdown("### Your Career Toolkit")

c1, c2, c3, c4 = st.columns(4)

with c1:
    has_resume = summary["has_resume"]
    badge_cls  = "done" if has_resume else ""
    badge_lbl  = "✅ Done" if has_resume else "Step 1"
    role_text  = f"Targeting: <strong>{summary['target_role']}</strong>" if summary['target_role'] else "Not built yet"
    pct = 100 if has_resume else 0
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {badge_cls}">{badge_lbl}</span>
        <div class="step-title">📄 Resume Builder</div>
        <div class="step-body">
            Deep probing chat with CareerOS — bilingual (Hindi + English).<br>
            Get an ATS-friendly, repositioned resume in 15 minutes.<br><br>
            {role_text}
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/1_Resume_Builder.py", label="Build / Update Resume →", icon="📄")

with c2:
    opt     = store.load_profile_optimizer()
    has_opt = bool(opt.get("naukri"))
    badge2  = "done" if has_opt else ("pending" if has_resume else "locked")
    lbl2    = "✅ Done" if has_opt else ("Step 2" if has_resume else "🔒 Locked")
    pct2    = 100 if has_opt else 0
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {'done' if has_opt else ''}">{lbl2}</span>
        <div class="step-title">🔗 Profile Optimizer</div>
        <div class="step-body">
            Copy-pasteable Naukri headline, summary, and LinkedIn About.<br>
            Optimised for recruiter search ranking and resumeworked.com score 75+.<br><br>
            {'Naukri & LinkedIn content ready!' if has_opt else 'Build your resume first to unlock.'}
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct2}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if has_resume:
        st.page_link("pages/2_Profile_Optimizer.py", label="Optimize Profiles →", icon="🔗")
    else:
        st.info("Complete Resume Builder first.")

with c3:
    has_ats = has_resume
    badge3  = "Ready" if has_ats else "🔒 Locked"
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {'done' if has_ats else ''}">{badge3}</span>
        <div class="step-title">🎯 ATS Score Checker</div>
        <div class="step-body">
            Paste any job description — CareerOS tells you your match score,
            missing keywords, and exactly what to fix before you apply.<br><br>
            {'Check any job in 10 seconds.' if has_ats else 'Build your resume first to unlock.'}
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{'100' if has_ats else '0'}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if has_ats:
        st.page_link("pages/4_ATS_Checker.py", label="Check Any Job →", icon="🎯")
    else:
        st.info("Complete Resume Builder first.")

with c4:
    has_apply = has_resume
    badge4    = "Step 4" if has_apply else "🔒 Locked"
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {'done' if has_apply else ''}">{badge4}</span>
        <div class="step-title">🤖 Smart Job Apply</div>
        <div class="step-body">
            Claude reads every JD, scores it against your profile, and applies only
            where it genuinely fits. Runs on your PC at 9:30 AM and 2 PM daily.<br><br>
            {'Configure preferences and set up the local runner.' if has_apply else 'Build your resume first to unlock.'}
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{'100' if has_apply else '0'}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if has_apply:
        st.page_link("pages/5_Smart_Apply.py", label="Set Up Auto-Apply →", icon="🤖")
    else:
        st.info("Complete Resume Builder first.")

st.divider()
st.caption("CareerOS • Built for the Indian job market • Powered by Claude AI • Your data stays on this server.")
