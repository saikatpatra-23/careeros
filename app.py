# -*- coding: utf-8 -*-
"""
CareerOS — Main entry point / Dashboard.
"""
import streamlit as st
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="CareerOS",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import require_login, get_user_email, get_user_name, get_user_avatar
from persistence.store import UserStore
from modules.ui.styles import inject_global_css

require_login()
inject_global_css()

# ── User context ──────────────────────────────────────────────────────────────
email      = get_user_email()
name       = get_user_name()
store      = UserStore(email)
summary    = store.summary()
first_name = name.split()[0] if name else "there"

# ── Page CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hero */
.hero {
    background: linear-gradient(135deg, #1B4F9C 0%, #2563EB 60%, #3B82F6 100%);
    border-radius: 18px;
    padding: 32px 36px;
    margin-bottom: 8px;
    color: white;
}
.hero h1 { font-size: 2rem; font-weight: 800; margin: 0 0 6px 0; line-height: 1.2; }
.hero p  { font-size: 1rem; opacity: 0.9; margin: 0; line-height: 1.5; }
.stat-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.stat-pill {
    background: rgba(255,255,255,0.18);
    border-radius: 100px;
    padding: 4px 14px;
    font-size: 0.8rem;
    color: white;
    font-weight: 500;
    border: 1px solid rgba(255,255,255,0.25);
}

/* Step cards */
.step-card {
    background: white;
    border-radius: 16px;
    padding: 20px 22px;
    border: 1.5px solid #E2E8F0;
    height: 100%;
    transition: box-shadow 0.2s, border-color 0.2s;
    position: relative;
    overflow: hidden;
}
.step-card:hover { box-shadow: 0 6px 24px rgba(27,79,156,0.10); border-color: #BFDBFE; }
.step-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1B4F9C, #3B82F6);
    opacity: 0;
    transition: opacity 0.2s;
}
.step-card:hover::before { opacity: 1; }

.step-badge {
    display: inline-block;
    background: #EBF3FB;
    color: #1B4F9C;
    border-radius: 8px;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 10px;
    margin-bottom: 10px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.step-badge.done   { background: #D1FAE5; color: #065F46; }
.step-badge.locked { background: #F3F4F6; color: #9CA3AF; }
.step-badge.soon   { background: #FEF3C7; color: #92400E; }

.step-icon  { font-size: 1.6rem; margin-bottom: 8px; display: block; }
.step-title { font-size: 1rem; font-weight: 700; color: #1F273A; margin: 4px 0 8px 0; }
.step-body  { font-size: 0.85rem; color: #6B7280; line-height: 1.6; }
.step-meta  { font-size: 0.8rem; color: #374151; font-weight: 600; margin-top: 8px; }

/* Progress bar */
.prog-wrap {
    background: #E2E8F0;
    border-radius: 100px;
    height: 5px;
    margin: 14px 0 6px 0;
    overflow: hidden;
}
.prog-fill {
    height: 5px;
    border-radius: 100px;
    background: linear-gradient(90deg, #1B4F9C, #3B82F6);
    transition: width 0.6s ease;
}

/* Tip card */
.tip-card {
    background: linear-gradient(135deg, #FFF7ED, #FEF9EC);
    border-radius: 14px;
    padding: 16px 20px;
    border-left: 4px solid #F59E0B;
    font-size: 0.875rem;
    color: #78350F;
    line-height: 1.6;
    border: 1px solid #FDE68A;
    border-left: 4px solid #F59E0B;
}

/* Section heading */
.section-heading {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1F273A;
    margin: 0 0 4px 0;
}
.section-sub {
    font-size: 0.82rem;
    color: #9CA3AF;
    margin: 0 0 16px 0;
}

/* User chip */
.user-chip {
    display: flex;
    align-items: center;
    gap: 10px;
    background: white;
    border-radius: 100px;
    padding: 8px 16px 8px 10px;
    border: 1.5px solid #E2E8F0;
    font-size: 0.85rem;
    color: #374151;
    font-weight: 500;
    width: fit-content;
    margin-left: auto;
}

/* Mobile overrides */
@media (max-width: 768px) {
    .hero { padding: 20px 18px; border-radius: 14px; }
    .hero h1 { font-size: 1.5rem; }
    .step-card { padding: 16px 18px; }
    .step-body { font-size: 0.82rem; }
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
opt        = store.load_profile_optimizer()
steps_done = sum([summary["has_resume"], bool(opt.get("naukri"))])
total_steps = 4

col_hero, col_user = st.columns([5, 1])
with col_hero:
    st.markdown(f"""
    <div class="hero">
        <h1>👋 Welcome back, {first_name}!</h1>
        <p>Your AI career coach for the Indian job market — built for how recruiters actually hire.</p>
        <div class="stat-row">
            <span class="stat-pill">🇮🇳 India-first</span>
            <span class="stat-pill">🤖 Claude AI</span>
            <span class="stat-pill">📊 {steps_done}/{total_steps} steps complete</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<small style='color:#9CA3AF;display:block;text-align:right;'>{email}</small>", unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        st.logout()

# ── Recruiter tip ──────────────────────────────────────────────────────────────
tips = [
    "💡 <strong>Recruiter insight:</strong> Indian HRs spend just 6 seconds on the first scan. Headline → Company → Skills → Summary — that's the order they look.",
    "💡 <strong>Naukri tip:</strong> Only 4-star and 5-star profiles appear in default recruiter searches. An incomplete profile = invisible profile.",
    "💡 <strong>Resume truth:</strong> 'Responsible for...' is the #1 phrase Indian recruiters hate. Replace with achievement verbs: Delivered, Led, Reduced, Designed.",
    "💡 <strong>ATS fact:</strong> Multi-column Canva templates fail RChilli parsing (Naukri's ATS). Single-column always wins.",
    "💡 <strong>Market fact:</strong> Mid-career candidates (5-10 yrs) fill 65% of Indian IT hires. Your experience is in demand — you just need to present it right.",
    "💡 <strong>LinkedIn tip:</strong> 'Open to Work' for recruiters only (no green banner) doubles InMail outreach — without signaling desperation publicly.",
    "💡 <strong>Salary fact:</strong> CBAP certification adds 15-25% salary premium for BA roles. CSM/PSM adds 20-30% for Scrum Master roles.",
    "💡 <strong>Career insight:</strong> Referrals fill 60-70% of mid-senior Indian roles before they're even posted publicly. Your network is your hidden job board.",
]
st.markdown(f'<div class="tip-card">{random.choice(tips)}</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Career Toolkit ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-heading">Your Career Toolkit</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Complete each step in order for the best results.</p>', unsafe_allow_html=True)

has_resume = summary["has_resume"]
has_opt    = bool(opt.get("naukri"))
has_ats    = has_resume
has_apply  = has_resume

c1, c2, c3, c4 = st.columns(4)

with c1:
    pct       = 100 if has_resume else 0
    badge_cls = "done" if has_resume else ""
    badge_lbl = "✅ Done" if has_resume else "Step 1"
    role_text = f"<span class='step-meta'>🎯 Targeting: {summary['target_role']}</span>" if summary.get("target_role") else ""
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {badge_cls}">{badge_lbl}</span>
        <div class="step-title">📄 Resume Builder</div>
        <div class="step-body">
            Bilingual AI chat (Hindi + English) → ATS-friendly Word &amp; PDF resume in 15 min.
        </div>
        {role_text}
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/1_Resume_Builder.py", label="Build / Update Resume →", icon="📄")

with c2:
    pct2 = 100 if has_opt else 0
    lbl2 = "✅ Done" if has_opt else ("Step 2" if has_resume else "🔒 Locked")
    cls2 = "done" if has_opt else ("locked" if not has_resume else "")
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {cls2}">{lbl2}</span>
        <div class="step-title">🔗 Profile Optimizer</div>
        <div class="step-body">
            Copy-paste Naukri headline, summary &amp; LinkedIn About. Optimised for recruiter search + resumeworked.com 75+.
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct2}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if has_resume:
        st.page_link("pages/2_Profile_Optimizer.py", label="Optimize Profiles →", icon="🔗")
    else:
        st.caption("Complete Resume Builder first.")

with c3:
    pct3 = 100 if has_ats else 0
    lbl3 = "Ready" if has_ats else "🔒 Locked"
    cls3 = "done" if has_ats else "locked"
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {cls3}">{lbl3}</span>
        <div class="step-title">🎯 ATS Score Checker</div>
        <div class="step-body">
            Paste any JD → see your match score, missing keywords, and exactly what to fix before applying.
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct3}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if has_ats:
        st.page_link("pages/4_ATS_Checker.py", label="Check Any Job →", icon="🎯")
    else:
        st.caption("Complete Resume Builder first.")

with c4:
    pct4 = 100 if has_apply else 0
    lbl4 = "Step 4" if has_apply else "🔒 Locked"
    cls4 = "done" if has_apply else "locked"
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {cls4}">{lbl4}</span>
        <div class="step-title">🤖 Smart Auto-Apply</div>
        <div class="step-body">
            AI reads every JD, scores fit, and applies only to matching roles. Runs at 9:30 AM &amp; 2 PM daily.
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct4}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if has_apply:
        st.page_link("pages/5_Smart_Apply.py", label="Set Up Auto-Apply →", icon="🤖")
    else:
        st.caption("Complete Resume Builder first.")

st.divider()

# ── Application Tools ──────────────────────────────────────────────────────────
st.markdown('<p class="section-heading">Application Tools</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">One-click tools for every stage of your job search.</p>', unsafe_allow_html=True)

cover_letters = store.load_cover_letters()
cl_count      = len(cover_letters)
has_cl        = has_resume

tool_c1, tool_c2, tool_c3 = st.columns(3)

with tool_c1:
    badge_cl = f"✅ {cl_count} generated" if cl_count > 0 else ("Ready" if has_cl else "🔒 Locked")
    cls_cl   = "done" if cl_count > 0 else ("" if has_cl else "locked")
    st.markdown(f"""
    <div class="step-card">
        <span class="step-badge {cls_cl}">{badge_cl}</span>
        <div class="step-title">✉️ Cover Letter Generator</div>
        <div class="step-body">
            Paste a JD → tailored cover letter in 10 seconds.<br>
            250-350 words, India-optimised, 3 tones to choose from.
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{'100' if has_cl else '0'}%"></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if has_cl:
        st.page_link("pages/6_Cover_Letter.py", label="Write Cover Letter →", icon="✉️")
    else:
        st.caption("Complete Resume Builder first.")

with tool_c2:
    st.markdown("""
    <div class="step-card">
        <span class="step-badge soon">Coming Soon</span>
        <div class="step-title">📋 Application Tracker</div>
        <div class="step-body">
            Track every job you've applied to. Follow-up reminders, status updates,
            and interview scheduling — all in one place.
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:0%"></div></div>
    </div>
    """, unsafe_allow_html=True)

with tool_c3:
    st.markdown("""
    <div class="step-card">
        <span class="step-badge soon">Coming Soon</span>
        <div class="step-title">🎤 Interview Prep</div>
        <div class="step-body">
            Role-specific Q&amp;A, HR round prep, STAR-format answers tailored
            to your background and the company you're interviewing at.
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:0%"></div></div>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption("CareerOS · Built for the Indian job market · Powered by Claude AI · Your data stays on this server.")
