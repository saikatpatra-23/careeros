# -*- coding: utf-8 -*-
"""
Page 3 — Role Clarity
5 quick questions → CareerOS tells you what role fits best.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json, re
import streamlit as st
import anthropic
from auth import require_login, get_user_email
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

st.set_page_config(page_title="Role Clarity – CareerOS", page_icon="💡", layout="centered")
require_login()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.page-header {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    border-radius: 14px;
    padding: 24px 28px;
    color: white;
    margin-bottom: 24px;
}
.page-header h2 { margin: 0 0 4px 0; font-size: 1.6rem; font-weight: 700; }
.page-header p  { margin: 0; opacity: 0.88; font-size: 0.95rem; }

.result-card {
    background: white;
    border-radius: 16px;
    padding: 24px 28px;
    border: 1.5px solid #E2E8F0;
    border-left: 5px solid #059669;
    margin: 16px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.advice-card {
    background: #FFFBEB;
    border-radius: 12px;
    padding: 16px 20px;
    border-left: 4px solid #F59E0B;
    margin: 12px 0;
    font-size: 0.9rem;
    color: #78350F;
    line-height: 1.6;
}
.step-card {
    background: white;
    border-radius: 10px;
    padding: 14px 18px;
    border: 1.5px solid #E2E8F0;
    margin: 8px 0;
    font-size: 0.9rem;
    color: #374151;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>💡 Role Clarity</h2>
    <p>Not sure what role fits you? Answer 5 quick questions — CareerOS will tell you what role fits best and why.</p>
</div>
""", unsafe_allow_html=True)

ROLE_CLARITY_PROMPT = """You are CareerOS, expert career coach for Indian job market.
Based on 5 answers, output a JSON role recommendation with these keys:
{{
  "primary_role": "Best fitting role title",
  "confidence": "High/Medium",
  "reasoning": "2-3 lines why this role fits — specific to what they said",
  "alternate_roles": ["Role 2", "Role 3"],
  "honest_advice": "If their target differs from recommendation, give honest bridge advice with specific steps",
  "salary_band": "X-Y LPA for this role in India at their experience level (use 2025-26 market rates)",
  "next_steps": ["Step 1 to move toward this role", "Step 2", "Step 3"]
}}
Output ONLY the JSON."""

st.markdown("### Tell CareerOS about yourself")
st.markdown("*Answer honestly — there are no wrong answers. The more specific you are, the better the recommendation.*")
st.markdown("<br>", unsafe_allow_html=True)

with st.form("role_form"):
    q1 = st.text_area(
        "1. Describe your day-to-day work in your last/current job. What do you ACTUALLY do most?",
        placeholder="E.g. Main requirements gather karta hun, testing team ke saath kaam karta hun, clients se meetings karta hun...",
        height=90,
    )
    q2 = st.text_area(
        "2. What do colleagues/manager come to YOU for help with?",
        placeholder="E.g. Sab log mujhse documents likhwate hain / project status update maangte hain / data analysis ke liye aate hain...",
        height=70,
    )
    q3 = st.text_area(
        "3. What part of your work makes time fly — the thing you enjoy doing most?",
        placeholder="E.g. Jab client se requirement nikalta hun / jab data mein pattern milta hai / jab team deliver karti hai...",
        height=70,
    )

    col1, col2 = st.columns(2)
    with col1:
        q4 = st.text_input("4. Total years of experience", placeholder="E.g. 5 years")
    with col2:
        q5 = st.text_input(
            "5. What role are you targeting? (Unsure is okay too)",
            placeholder="E.g. BA, Product Manager, Not sure...",
        )

    submitted = st.form_submit_button(
        "Get My Role Recommendation →",
        type="primary",
        use_container_width=True,
    )

if submitted and all([q1.strip(), q2.strip(), q3.strip(), q4.strip()]):
    user_input = f"""
    Q1. Day-to-day work: {q1}
    Q2. What people ask me for: {q2}
    Q3. What I enjoy most: {q3}
    Q4. Years of experience: {q4}
    Q5. Target role: {q5 or 'Not sure'}
    """
    with st.spinner("CareerOS is analysing your profile..."):
        try:
            client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1500,
                system=ROLE_CLARITY_PROMPT,
                messages=[{"role": "user", "content": user_input}],
            )
            raw     = response.content[0].text
            cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
            result  = json.loads(cleaned[cleaned.find("{"):cleaned.rfind("}")+1])
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    primary    = result.get("primary_role", "")
    confidence = result.get("confidence", "")
    reasoning  = result.get("reasoning", "")
    alts       = result.get("alternate_roles", [])
    advice     = result.get("honest_advice", "")
    salary     = result.get("salary_band", "")
    next_steps = result.get("next_steps", [])

    conf_color = "#059669" if confidence == "High" else "#D97706"

    st.divider()
    st.markdown("### CareerOS Recommendation")

    st.markdown(f"""
    <div class="result-card">
        <div style="font-size:0.75rem;color:#9CA3AF;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">Your Best-Fit Role</div>
        <div style="font-size:1.5rem;font-weight:700;color:#1F273A;margin:8px 0 6px 0;">🎯 {primary}</div>
        <span style="background:{conf_color};color:white;padding:3px 12px;border-radius:100px;font-size:0.78rem;font-weight:600;">{confidence} Confidence</span>
        <br><br>
        <div style="color:#374151;line-height:1.65;font-size:0.95rem;">{reasoning}</div>
        <br>
        <div style="font-size:0.875rem;color:#6B7280;">
            <strong>Alternate roles:</strong> {", ".join(alts)}<br>
            <strong>Salary in India:</strong> {salary}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if advice:
        st.markdown(f"""
        <div class="advice-card">
            📍 <strong>Honest Advice:</strong> {advice}
        </div>
        """, unsafe_allow_html=True)

    if next_steps:
        st.markdown("#### Your Next Steps")
        for i, step in enumerate(next_steps, 1):
            st.markdown(f"""
            <div class="step-card">
                <strong style="color:#1B4F9C;">{i}.</strong> {step}
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="background:white;border-radius:12px;padding:18px 22px;border:1.5px solid #E2E8F0;text-align:center;font-size:0.9rem;color:#374151;">
        Ready to build your resume for this role? Go to <strong>Resume Builder</strong> — CareerOS will ask deep questions and generate an ATS-ready Word resume.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/1_Resume_Builder.py", label="Build My Resume →", icon="📄")

elif submitted:
    st.warning("Please answer at least questions 1-4 before submitting.")
