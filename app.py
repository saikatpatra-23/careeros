# -*- coding: utf-8 -*-
"""CareerOS — Dashboard"""
import streamlit as st
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="CareerOS",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import require_login, get_user_email, get_user_name
from persistence.store import UserStore
from modules.ui.styles import inject_global_css

require_login()
inject_global_css()

email      = get_user_email()
name       = get_user_name()
store      = UserStore(email)
summary    = store.summary()
first_name = name.split()[0] if name else "there"

# ── Page CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.dash-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.dash-welcome { font-size: 1.15rem; font-weight: 700; color: #E2E8F0; }
.dash-sub     { font-size: 0.82rem; color: #6B7280; margin-top: 2px; }

.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
}

.step-card {
    background: #1A1D27;
    border-radius: 12px;
    padding: 16px 18px;
    border: 1px solid rgba(255,255,255,0.07);
    height: 100%;
    transition: border-color 0.18s, box-shadow 0.18s;
    cursor: default;
}
.step-card:hover {
    border-color: rgba(79,142,247,0.3);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.step-badge {
    display: inline-block;
    font-size: 0.67rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    margin-bottom: 8px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    background: rgba(79,142,247,0.12);
    color: #4F8EF7;
    border: 1px solid rgba(79,142,247,0.22);
}
.step-badge.done   { background: rgba(16,185,129,0.1);  color: #10B981; border-color: rgba(16,185,129,0.22); }
.step-badge.locked { background: rgba(255,255,255,0.04); color: #6B7280;  border-color: rgba(255,255,255,0.07); }
.step-badge.soon   { background: rgba(245,158,11,0.1);  color: #F59E0B; border-color: rgba(245,158,11,0.22); }
.step-title { font-size: 0.95rem; font-weight: 700; color: #E2E8F0; margin: 4px 0 6px 0; }
.step-body  { font-size: 0.8rem; color: #6B7280; line-height: 1.55; }
.step-meta  { font-size: 0.78rem; color: #4F8EF7; margin-top: 6px; font-weight: 600; }
.prog-wrap  { background: rgba(255,255,255,0.07); border-radius: 100px; height: 3px; margin: 12px 0 4px 0; overflow: hidden; }
.prog-fill  { height: 3px; border-radius: 100px; background: linear-gradient(90deg,#4F8EF7,#818CF8); }

.tip-strip {
    background: rgba(245,158,11,0.07);
    border-left: 3px solid #F59E0B;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #C49A20;
    line-height: 1.6;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Top bar ───────────────────────────────────────────────────────────────────
opt      = store.load_profile_optimizer()
has_res  = summary["has_resume"]
has_opt  = bool(opt.get("naukri"))
done_cnt = sum([has_res, has_opt])

col_welcome, col_signout = st.columns([5, 1])
with col_welcome:
    st.markdown(f"""
    <div class="dash-topbar">
        <div>
            <div class="dash-welcome">👋 Hey {first_name}</div>
            <div class="dash-sub">CareerOS · Indian Job Market · {done_cnt}/4 steps complete</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_signout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        st.logout()

# ── Daily tip ─────────────────────────────────────────────────────────────────
tips = [
    "💡 <b>6-second rule:</b> Indian HRs scan Headline → Company → Skills → Summary. In that order. Nail those four.",
    "💡 <b>Naukri:</b> Only 4★ and 5★ profiles appear in default recruiter search. Incomplete = invisible.",
    "💡 <b>Resume:</b> 'Responsible for...' is the #1 phrase recruiters hate. Use Delivered / Led / Reduced instead.",
    "💡 <b>ATS:</b> Canva multi-column templates fail RChilli (Naukri's parser). Single column always wins.",
    "💡 <b>Market:</b> Mid-career (5-10 yrs) fills 65% of Indian IT hires. You're in demand — just package it right.",
    "💡 <b>LinkedIn:</b> 'Open to Work' for recruiters only (no green banner) doubles InMail — without looking desperate.",
    "💡 <b>Salary:</b> CBAP adds 15-25% premium for BA roles. CSM/PSM adds 20-30% for Scrum Masters.",
    "💡 <b>Referrals:</b> 60-70% of mid-senior Indian roles are filled before posting. Your network is your job board.",
]
st.markdown(f'<div class="tip-strip">{random.choice(tips)}</div>', unsafe_allow_html=True)

# ── Career Toolkit ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Career Toolkit</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    pct  = 100 if has_res else 0
    cls  = "done" if has_res else ""
    lbl  = "✓ Done" if has_res else "Step 1"
    meta = f'<div class="step-meta">🎯 {summary["target_role"]}</div>' if summary.get("target_role") else ""
    st.html(f'<div class="step-card"><span class="step-badge {cls}">{lbl}</span><div class="step-title">📄 Resume Builder</div><div class="step-body">AI chat · ATS Word + PDF resume in 15 min. Hindi or English.</div>{meta}<div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div></div>')
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/1_Resume_Builder.py", label="Open →", icon="📄")

with c2:
    pct2 = 100 if has_opt else 0
    cls2 = "done" if has_opt else ("locked" if not has_res else "")
    lbl2 = "✓ Done" if has_opt else ("Step 2" if has_res else "🔒")
    st.html(f'<div class="step-card"><span class="step-badge {cls2}">{lbl2}</span><div class="step-title">🔗 Profile Optimizer</div><div class="step-body">Naukri headline, summary + LinkedIn About. Recruiters find you first.</div><div class="prog-wrap"><div class="prog-fill" style="width:{pct2}%"></div></div></div>')
    st.markdown("<br>", unsafe_allow_html=True)
    if has_res:
        st.page_link("pages/2_Profile_Optimizer.py", label="Open →", icon="🔗")
    else:
        st.caption("Build resume first")

with c3:
    pct3 = 100 if has_res else 0
    cls3 = "done" if has_res else "locked"
    lbl3 = "Ready" if has_res else "🔒"
    st.html(f'<div class="step-card"><span class="step-badge {cls3}">{lbl3}</span><div class="step-title">🎯 ATS Checker</div><div class="step-body">Paste any JD · match score, missing keywords, what to fix before applying.</div><div class="prog-wrap"><div class="prog-fill" style="width:{pct3}%"></div></div></div>')
    st.markdown("<br>", unsafe_allow_html=True)
    if has_res:
        st.page_link("pages/4_ATS_Checker.py", label="Open →", icon="🎯")
    else:
        st.caption("Build resume first")

with c4:
    pct4 = 100 if has_res else 0
    cls4 = "done" if has_res else "locked"
    lbl4 = "Step 4" if has_res else "🔒"
    st.html(f'<div class="step-card"><span class="step-badge {cls4}">{lbl4}</span><div class="step-title">🤖 Smart Auto-Apply</div><div class="step-body">AI scores every JD vs your profile. Applies at 9:30 AM + 2 PM daily.</div><div class="prog-wrap"><div class="prog-fill" style="width:{pct4}%"></div></div></div>')
    st.markdown("<br>", unsafe_allow_html=True)
    if has_res:
        st.page_link("pages/5_Smart_Apply.py", label="Open →", icon="🤖")
    else:
        st.caption("Build resume first")

st.divider()

# ── Application Tools ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Application Tools</div>', unsafe_allow_html=True)

cover_letters = store.load_cover_letters()
cl_count      = len(cover_letters)
t1, t2, t3    = st.columns(3)

with t1:
    cls_cl = "done" if cl_count > 0 else ("" if has_res else "locked")
    lbl_cl = f"✓ {cl_count} letters" if cl_count > 0 else ("Ready" if has_res else "🔒")
    pct_cl = 100 if has_res else 0
    st.html(f'<div class="step-card"><span class="step-badge {cls_cl}">{lbl_cl}</span><div class="step-title">✉️ Cover Letter</div><div class="step-body">Paste JD · tailored letter in 10 sec. 3 tones. India-optimised length.</div><div class="prog-wrap"><div class="prog-fill" style="width:{pct_cl}%"></div></div></div>')
    st.markdown("<br>", unsafe_allow_html=True)
    if has_res:
        st.page_link("pages/6_Cover_Letter.py", label="Open →", icon="✉️")
    else:
        st.caption("Build resume first")

with t2:
    st.html('<div class="step-card"><span class="step-badge soon">Soon</span><div class="step-title">📋 Application Tracker</div><div class="step-body">Track applications, follow-up reminders, interview scheduling.</div><div class="prog-wrap"><div class="prog-fill" style="width:0%"></div></div></div>')

with t3:
    st.html('<div class="step-card"><span class="step-badge soon">Soon</span><div class="step-title">🎤 Interview Prep</div><div class="step-body">STAR-format answers tailored to your background + target company.</div><div class="prog-wrap"><div class="prog-fill" style="width:0%"></div></div></div>')

st.divider()
st.caption("CareerOS · India-focused · Claude AI · Data stays on this server")
