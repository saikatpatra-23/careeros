# -*- coding: utf-8 -*-
"""
Page 4 — ATS Score Checker
Paste any JD → CareerOS tells you how well your resume matches it.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email
from persistence.store import UserStore
from modules.ats.checker import check_ats
from modules.resume.parser import (
    extract_text_from_docx, extract_text_from_pdf,
    extract_text_from_image, parse_resume_to_json,
)
from modules.ui.styles import inject_global_css
from config import ANTHROPIC_API_KEY

st.set_page_config(page_title="ATS Checker – CareerOS", page_icon="🎯", layout="wide")
require_login()
inject_global_css()

email = get_user_email()
store = UserStore(email)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.score-ring { text-align: center; padding: 18px; border-radius: 14px; margin-bottom: 8px; }
.score-number { font-size: 3.6rem; font-weight: 800; line-height: 1; }
.score-label  { font-size: 0.82rem; color: #6B7280; margin-top: 4px; }

.verdict-card {
    border-radius: 10px; padding: 14px 18px;
    font-size: 0.9rem; font-weight: 600;
    margin-bottom: 14px; text-align: center;
}
.param-row {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
}
.param-label   { font-size: 0.85rem; font-weight: 600; color: #E2E8F0; width: 110px; flex-shrink: 0; }
.param-bar-wrap { flex: 1; background: rgba(255,255,255,0.08); border-radius: 100px; height: 6px; }
.param-comment { font-size: 0.78rem; color: #6B7280; width: 190px; flex-shrink: 0; text-align: right; }

.keyword-pill {
    display: inline-block; padding: 2px 10px; border-radius: 100px;
    font-size: 0.78rem; margin: 3px; font-weight: 500;
}
.rec-card {
    background: #1A1D27; border-radius: 10px;
    padding: 12px 16px; border: 1px solid rgba(255,255,255,0.07);
    margin: 6px 0; font-size: 0.85rem;
}
.rec-high   { border-left: 3px solid #EF4444; }
.rec-medium { border-left: 3px solid #F59E0B; }
.rec-low    { border-left: 3px solid #10B981; }

.gap-card {
    background: rgba(249,115,22,0.08); border-radius: 10px;
    padding: 12px 16px; border-left: 3px solid #F97316;
    font-size: 0.875rem; color: #FB923C; margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="pg-title"><span class="pg-icon">🎯</span><span class="pg-name">ATS Checker</span><span class="pg-sub">Paste any JD → match score + what to fix</span></div>', unsafe_allow_html=True)

# ── Resume check ──────────────────────────────────────────────────────────────
resume_saved = store.load_resume()
resume_data  = resume_saved.get("structured_data", {})

if "ats_uploaded_resume" not in st.session_state:
    st.session_state.ats_uploaded_resume = None

if not resume_data and not st.session_state.ats_uploaded_resume:
    st.warning("No resume found. Build your resume first — or upload one below for a one-time check.")
    st.page_link("pages/1_Resume_Builder.py", label="Go to Resume Builder →", icon="📄")

    st.markdown("#### Upload your resume for a one-time check")
    st.caption("This won't overwrite your saved resume — it's only used for this session.")
    uploaded_tmp = st.file_uploader(
        "Upload resume",
        type=["pdf", "docx", "jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="ats_upload_init",
    )
    if uploaded_tmp is not None:
        with st.spinner("Parsing resume... (15-30 seconds)"):
            try:
                file_bytes = uploaded_tmp.read()
                ext = uploaded_tmp.name.rsplit(".", 1)[-1].lower()
                if ext == "docx":
                    text = extract_text_from_docx(file_bytes)
                elif ext == "pdf":
                    text = extract_text_from_pdf(file_bytes)
                else:
                    text = extract_text_from_image(file_bytes, ANTHROPIC_API_KEY)
                parsed = parse_resume_to_json(text, ANTHROPIC_API_KEY)
                st.session_state.ats_uploaded_resume = parsed
                st.rerun()
            except Exception as e:
                st.error(f"Could not parse resume: {e}")
    st.stop()

# Use uploaded session resume if no saved resume
if not resume_data and st.session_state.ats_uploaded_resume:
    resume_data = st.session_state.ats_uploaded_resume

target_role = resume_data.get("target_title", "your target role")

col_resume_info, col_upload_alt = st.columns([3, 1])
with col_resume_info:
    st.success(f"Resume loaded: **{resume_data.get('name', '')}** — targeting **{target_role}**")
with col_upload_alt:
    with st.expander("Use a different resume"):
        uploaded_alt = st.file_uploader(
            "Replace for this session",
            type=["pdf", "docx", "jpg", "jpeg", "png"],
            label_visibility="collapsed",
            key="ats_upload_alt",
        )
        if uploaded_alt is not None:
            with st.spinner("Parsing..."):
                try:
                    file_bytes = uploaded_alt.read()
                    ext = uploaded_alt.name.rsplit(".", 1)[-1].lower()
                    if ext == "docx":
                        text = extract_text_from_docx(file_bytes)
                    elif ext == "pdf":
                        text = extract_text_from_pdf(file_bytes)
                    else:
                        text = extract_text_from_image(file_bytes, ANTHROPIC_API_KEY)
                    parsed = parse_resume_to_json(text, ANTHROPIC_API_KEY)
                    st.session_state.ats_uploaded_resume = parsed
                    resume_data = parsed
                    st.rerun()
                except Exception as e:
                    st.error(f"Parse failed: {e}")

st.divider()

# ── JD Input ─────────────────────────────────────────────────────────────────
st.markdown("### Paste the Job Description")
st.caption("Copy the full JD from Naukri, LinkedIn, or any company website and paste it below.")

jd = st.text_area(
    label="Job Description",
    placeholder="Paste the complete job description here — the more complete, the better the analysis...",
    height=220,
    label_visibility="collapsed",
)

col_btn, col_tip = st.columns([1, 3])
with col_btn:
    analyse = st.button("Analyse My Resume →", type="primary", use_container_width=True, disabled=not jd.strip())
with col_tip:
    st.markdown("<small style='color:#9CA3AF;'>Takes ~10 seconds • Uses your saved resume</small>", unsafe_allow_html=True)

# ── Analysis ──────────────────────────────────────────────────────────────────
if analyse and jd.strip():
    with st.spinner("CareerOS is analysing your resume against this JD..."):
        try:
            result = check_ats(resume_data, jd.strip(), ANTHROPIC_API_KEY)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    score   = result.get("overall_score", 0)
    verdict = result.get("verdict", "")
    reason  = result.get("verdict_reason", "")
    gap     = result.get("one_liner_gap", "")
    params  = result.get("naukri_parameters", {})
    found   = result.get("keywords_found", [])
    missing = result.get("keywords_missing", [])
    recs    = result.get("recommendations", [])
    headline_suggestion = result.get("resume_headline_suggestion", "")

    st.divider()
    st.markdown("## Your ATS Analysis")

    # ── Score + Verdict ───────────────────────────────────────────────────────
    col_score, col_verdict = st.columns([1, 2])

    with col_score:
        if score >= 80:
            color = "#10B981"; bg = "#ECFDF5"
        elif score >= 60:
            color = "#F59E0B"; bg = "#FFFBEB"
        elif score >= 40:
            color = "#F97316"; bg = "#FFF7ED"
        else:
            color = "#EF4444"; bg = "#FEF2F2"

        st.markdown(f"""
        <div class="score-ring" style="background:{bg};">
            <div class="score-number" style="color:{color};">{score}</div>
            <div class="score-label">out of 100</div>
        </div>
        """, unsafe_allow_html=True)

    with col_verdict:
        if score >= 80:
            v_bg = "#ECFDF5"; v_color = "#065F46"
        elif score >= 60:
            v_bg = "#FFFBEB"; v_color = "#92400E"
        elif score >= 40:
            v_bg = "#FFF7ED"; v_color = "#9A3412"
        else:
            v_bg = "#FEF2F2"; v_color = "#991B1B"

        st.markdown(f"""
        <div class="verdict-card" style="background:{v_bg}; color:{v_color};">
            {verdict}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"<p style='color:#374151;font-size:0.9rem;'>{reason}</p>", unsafe_allow_html=True)

        if gap:
            st.markdown(f"""
            <div class="gap-card">
                ⚠️ <strong>Biggest risk:</strong> {gap}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Naukri 6 Parameters ───────────────────────────────────────────────────
    st.markdown("### Naukri AI Relevance Score Breakdown")
    st.caption("These are the 6 parameters Naukri scores every applicant on — recruiters see High / Medium / Low Match.")

    param_labels = {
        "skills":      "Skills",
        "designation": "Designation",
        "experience":  "Experience",
        "salary":      "Salary",
        "location":    "Location",
        "education":   "Education",
    }

    for key, label in param_labels.items():
        p = params.get(key, {})
        p_score   = p.get("score", 0)
        p_comment = p.get("comment", "")

        if p_score >= 75:
            bar_color = "#10B981"
        elif p_score >= 50:
            bar_color = "#F59E0B"
        else:
            bar_color = "#EF4444"

        st.markdown(f"""
        <div class="param-row">
            <span class="param-label">{label}</span>
            <div class="param-bar-wrap">
                <div style="width:{p_score}%;height:8px;border-radius:100px;background:{bar_color};"></div>
            </div>
            <span style="font-size:0.875rem;font-weight:700;color:{bar_color};width:36px;flex-shrink:0;">{p_score}</span>
            <span class="param-comment">{p_comment}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Keywords ──────────────────────────────────────────────────────────────
    col_found, col_missing = st.columns(2)

    with col_found:
        st.markdown(f"### ✅ Keywords Found ({len(found)})")
        st.caption("These JD keywords are present in your resume — good signals for ATS.")
        if found:
            pills = " ".join([
                f'<span class="keyword-pill" style="background:#D1FAE5;color:#065F46;">{k}</span>'
                for k in found
            ])
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.markdown("<small style='color:#9CA3AF;'>None detected</small>", unsafe_allow_html=True)

    with col_missing:
        st.markdown(f"### ❌ Keywords Missing ({len(missing)})")
        st.caption("These JD keywords are absent from your resume — add them to improve your score.")
        if missing:
            pills = " ".join([
                f'<span class="keyword-pill" style="background:#FEE2E2;color:#991B1B;">{k}</span>'
                for k in missing
            ])
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.markdown("<small style='color:#9CA3AF;'>None — great coverage!</small>", unsafe_allow_html=True)

    st.divider()

    # ── Recommendations ───────────────────────────────────────────────────────
    st.markdown("### What to Fix")
    st.caption("Specific, actionable changes — not generic advice.")

    priority_style = {
        "High":   ("rec-high",   "🔴 High Priority"),
        "Medium": ("rec-medium", "🟡 Medium Priority"),
        "Low":    ("rec-low",    "🟢 Low Priority"),
    }

    for rec in recs:
        pri   = rec.get("priority", "Medium")
        cls, label = priority_style.get(pri, ("rec-medium", "Medium"))
        action = rec.get("action", "")
        where  = rec.get("where", "")
        st.markdown(f"""
        <div class="rec-card {cls}">
            <span style="font-size:0.75rem;font-weight:700;color:#6B7280;">{label} · {where}</span><br>
            <span style="color:#1F273A;">{action}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Headline Suggestion ───────────────────────────────────────────────────
    if headline_suggestion:
        st.divider()
        st.markdown("### Optimised Naukri Headline for This Job")
        st.caption("Copy this into Naukri → Edit Profile → Resume Headline before applying.")
        st.text_area("ats_headline", value=headline_suggestion, height=80, disabled=True, label_visibility="collapsed")

    # ── CTA ───────────────────────────────────────────────────────────────────
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div style="background:#EFF6FF;border-radius:12px;padding:16px 20px;border-left:4px solid #3B82F6;">
            <strong style="color:#1E40AF;">Want to tailor your resume for this job?</strong><br>
            <span style="font-size:0.875rem;color:#374151;">
            Go to Resume Builder, share the JD, and CareerOS will reposition your experience for this role.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.page_link("pages/1_Resume_Builder.py", label="Tailor Resume for This Job →", icon="📄")
    with col_b:
        st.markdown("""
        <div style="background:#F0FDF4;border-radius:12px;padding:16px 20px;border-left:4px solid #10B981;">
            <strong style="color:#065F46;">Profile optimised for this domain?</strong><br>
            <span style="font-size:0.875rem;color:#374151;">
            Make sure your Naukri headline and skills are updated before you apply.
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.page_link("pages/2_Profile_Optimizer.py", label="Check Profile Optimizer →", icon="🔗")
