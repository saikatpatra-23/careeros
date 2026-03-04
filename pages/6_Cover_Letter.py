# -*- coding: utf-8 -*-
"""
Page 6 — Cover Letter Generator
Paste a JD, pick a tone, get a tailored cover letter ready to send.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from datetime import datetime
from auth import require_login, get_user_email
from persistence.store import UserStore
from modules.coverletter.generator import generate_cover_letter

st.set_page_config(page_title="Cover Letter – CareerOS", page_icon="✉️", layout="wide")
require_login()

email = get_user_email()
store = UserStore(email)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.page-header {
    background: linear-gradient(135deg, #064E3B 0%, #059669 100%);
    border-radius: 14px; padding: 24px 28px; color: white; margin-bottom: 24px;
}
.page-header h2 { margin: 0 0 4px 0; font-size: 1.6rem; font-weight: 700; }
.page-header p  { margin: 0; opacity: 0.88; font-size: 0.95rem; }

.subject-box {
    background: #F0FDF4; border-radius: 10px;
    padding: 14px 18px; border-left: 4px solid #10B981;
    font-size: 0.875rem; color: #065F46; margin-bottom: 16px;
}
.subject-label { font-size: 0.75rem; font-weight: 600; color: #059669;
                 text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.subject-text  { font-size: 0.95rem; font-weight: 600; color: #064E3B; }

.letter-box {
    background: white; border-radius: 12px;
    padding: 28px 32px; border: 1.5px solid #D1D5DB;
    font-size: 0.9rem; line-height: 1.75; color: #1F2937;
    white-space: pre-wrap; font-family: 'Inter', sans-serif;
}

.meta-pill {
    display: inline-block; background: #F3F4F6; border-radius: 100px;
    padding: 3px 12px; font-size: 0.78rem; color: #6B7280;
    font-weight: 500; margin-right: 8px;
}

.hook-box {
    background: #EFF6FF; border-radius: 10px;
    padding: 14px 18px; border-left: 4px solid #3B82F6;
    font-size: 0.875rem; color: #1E40AF; margin-top: 16px;
    font-style: italic;
}

.tailor-box {
    background: #FFFBEB; border-radius: 10px;
    padding: 12px 16px; border-left: 4px solid #F59E0B;
    font-size: 0.825rem; color: #78350F; margin-top: 12px;
}

.hist-card {
    background: white; border-radius: 10px;
    padding: 14px 18px; border: 1.5px solid #E5E7EB; margin: 8px 0;
}
.hist-date { font-size: 0.75rem; color: #9CA3AF; }
.hist-role { font-size: 0.9rem; font-weight: 600; color: #1F2937; }

.tip-row {
    background: #F0FDF4; border-radius: 10px;
    padding: 12px 16px; font-size: 0.825rem; color: #065F46;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>✉️ Cover Letter Generator</h2>
    <p>Paste a JD → CareerOS writes a tailored cover letter that actually gets read by Indian recruiters.</p>
</div>
""", unsafe_allow_html=True)

# ── Resume check ──────────────────────────────────────────────────────────────
resume_saved = store.load_resume()
resume_data  = resume_saved.get("structured_data", {})

if not resume_data:
    st.warning("Build your resume first — the cover letter is personalised from your resume data.")
    st.page_link("pages/1_Resume_Builder.py", label="Go to Resume Builder →", icon="📄")
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_gen, tab_history = st.tabs(["✍️ Generate Letter", "📁 Saved Letters"])

# =============================================================================
# TAB 1 — GENERATE
# =============================================================================
with tab_gen:
    st.markdown("""
    <div class="tip-row">
        💡 <strong>Pro tip:</strong> Paste the JD for maximum tailoring. Leave blank for a general letter targeting your saved role.
        Send the letter in the email body — not as an attachment. Most Indian recruiters don't open attachments from unknown candidates.
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("#### Job Description")
        jd_input = st.text_area(
            "Paste JD here (optional but recommended)",
            height=280,
            placeholder="Paste the full job description here...\n\nIf left blank, CareerOS generates a strong general letter for your target role.",
            label_visibility="collapsed",
        )

        st.markdown("#### Tone")
        tone = st.radio(
            "Tone",
            options=["Professional", "Confident", "Concise"],
            horizontal=True,
            label_visibility="collapsed",
            help="Professional = formal but warm. Confident = assertive, achievement-led. Concise = ultra-short, punchy.",
        )
        st.caption(
            "**Professional** — formal but warm | "
            "**Confident** — assertive, achievement-led | "
            "**Concise** — ultra-short, punchy"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button(
            "✉️ Generate Cover Letter",
            type="primary",
            use_container_width=True,
        )

    with col_right:
        st.markdown("#### Your Resume Context")
        st.markdown(f"""
        <div style="background:#F8FAFC;border-radius:10px;padding:16px 18px;border:1.5px solid #E5E7EB;">
            <div style="font-size:0.8rem;color:#6B7280;margin-bottom:4px;">Targeting</div>
            <div style="font-size:1rem;font-weight:600;color:#1F2937;">{resume_data.get('target_title', 'Not set')}</div>
            <div style="font-size:0.8rem;color:#6B7280;margin-top:10px;margin-bottom:4px;">Key Skills used</div>
            <div style="font-size:0.85rem;color:#374151;">{', '.join(resume_data.get('ats_keywords', [])[:8])}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#F0F9FF;border-radius:10px;padding:14px 16px;font-size:0.825rem;color:#0C4A6E;">
            <strong>What makes a great Indian cover letter:</strong><br><br>
            ✓ Opens with an insight or hook — not "I am writing to..."<br>
            ✓ 2-3 quantified achievements relevant to the JD<br>
            ✓ Names the company specifically — shows you're not spray-and-pray<br>
            ✓ 250-350 words — short enough to be read, long enough to matter<br>
            ✓ Ends with a specific ask (not "hope to hear from you")
        </div>
        """, unsafe_allow_html=True)

    # ── Generation ────────────────────────────────────────────────────────────
    if generate_btn:
        with st.spinner("Writing your cover letter..."):
            try:
                result = generate_cover_letter(
                    resume_data=resume_data,
                    jd=jd_input,
                    tone=tone,
                )

                # Save to history
                store.save_cover_letter({
                    "date":          datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "tone":          tone,
                    "jd_snippet":    jd_input[:200] if jd_input.strip() else "",
                    "subject_line":  result.get("subject_line", ""),
                    "cover_letter":  result.get("cover_letter", ""),
                    "word_count":    result.get("word_count", 0),
                })

                st.session_state["last_cover_letter"] = result

            except Exception as e:
                st.error(f"Generation failed: {e}")

    # ── Display result ────────────────────────────────────────────────────────
    result = st.session_state.get("last_cover_letter")
    if result:
        st.divider()
        st.markdown("### Your Cover Letter")

        cover_text   = result.get("cover_letter", "")
        subject_line = result.get("subject_line", "")
        word_count   = result.get("word_count", len(cover_text.split()))
        hook         = result.get("opening_hook", "")
        tailor_note  = result.get("tailoring_notes", "")

        # Subject line
        if subject_line:
            st.markdown(f"""
            <div class="subject-box">
                <div class="subject-label">📧 Email Subject Line</div>
                <div class="subject-text">{subject_line}</div>
            </div>
            """, unsafe_allow_html=True)

        # Meta
        st.markdown(
            f'<span class="meta-pill">📝 {word_count} words</span>'
            f'<span class="meta-pill">🎨 {tone} tone</span>'
            f'<span class="meta-pill">{"📌 JD-tailored" if jd_input.strip() else "📌 General letter"}</span>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Letter body
        st.markdown(f'<div class="letter-box">{cover_text}</div>', unsafe_allow_html=True)

        # Hook callout
        if hook:
            st.markdown(f"""
            <div class="hook-box">
                <strong>Opening hook:</strong> "{hook}"
            </div>
            """, unsafe_allow_html=True)

        # Tailoring note
        if tailor_note:
            st.markdown(f"""
            <div class="tailor-box">
                🎯 <strong>Tailoring logic:</strong> {tailor_note}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Action buttons
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                label="⬇️ Download as .txt",
                data=f"Subject: {subject_line}\n\n{cover_text}",
                file_name="cover_letter.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with c2:
            if st.button("🔄 Regenerate", use_container_width=True):
                st.session_state.pop("last_cover_letter", None)
                st.rerun()
        with c3:
            st.page_link(
                "pages/4_ATS_Checker.py",
                label="Check ATS Score →",
                icon="🎯",
                use_container_width=True,
            )

        st.markdown("""
        <div style="background:#F0FDF4;border-radius:10px;padding:12px 16px;
                    font-size:0.8rem;color:#065F46;margin-top:12px;">
            ✅ <strong>Next step:</strong> Paste this letter into the email body when applying.
            Don't attach it as a PDF — most Indian recruiters won't open attachments from unknown candidates.
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# TAB 2 — HISTORY
# =============================================================================
with tab_history:
    st.markdown("### Saved Cover Letters")
    st.caption("Last 10 letters you generated are saved here.")

    history = store.load_cover_letters()

    if not history:
        st.info("No letters generated yet. Use the Generate tab to create your first cover letter.")
        st.markdown("""
        <div style="background:#F8FAFC;border-radius:12px;padding:24px;
                    text-align:center;color:#6B7280;margin-top:16px;">
            <div style="font-size:2rem;">✉️</div>
            <div style="font-size:0.9rem;margin-top:8px;">No letters yet</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, letter in enumerate(history):
            date       = letter.get("date", "Unknown date")
            tone_used  = letter.get("tone", "")
            word_count = letter.get("word_count", 0)
            subject    = letter.get("subject_line", "Cover Letter")
            jd_snip    = letter.get("jd_snippet", "")
            body       = letter.get("cover_letter", "")

            with st.expander(f"**{date}** — {subject[:60]}{'...' if len(subject) > 60 else ''}"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**Subject:** {subject}")
                    if jd_snip:
                        st.caption(f"JD: {jd_snip[:100]}...")
                with col_b:
                    st.markdown(
                        f'<span class="meta-pill">{tone_used}</span>'
                        f'<span class="meta-pill">{word_count}w</span>',
                        unsafe_allow_html=True,
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f'<div class="letter-box">{body}</div>', unsafe_allow_html=True)

                st.download_button(
                    label="⬇️ Download",
                    data=f"Subject: {subject}\n\n{body}",
                    file_name=f"cover_letter_{date[:10]}.txt",
                    mime="text/plain",
                    key=f"dl_{i}",
                )
