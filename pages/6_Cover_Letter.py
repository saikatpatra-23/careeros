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
from modules.telemetry.tracker import install_error_tracking, log_error, track_page_view
from modules.ui.styles import inject_global_css
from persistence.store import UserStore
from modules.coverletter.generator import generate_cover_letter

st.set_page_config(page_title="Cover Letter - CareerOS", page_icon="L", layout="wide")
require_login()
inject_global_css()

email = get_user_email()
install_error_tracking(email=email, page="Cover Letter")
track_page_view(email=email, page="Cover Letter")
store = UserStore(email)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.subject-box {
    background: rgba(16,185,129,0.08); border-radius: 10px;
    padding: 12px 16px; border-left: 3px solid #10B981;
    font-size: 0.875rem; color: #10B981; margin-bottom: 14px;
}
.subject-label { font-size: 0.7rem; font-weight: 700; color: #10B981;
                 text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.subject-text  { font-size: 0.9rem; font-weight: 600; color: #6EE7B7; }

.letter-box {
    background: #121927; border-radius: 10px;
    padding: 22px 26px; border: 1px solid rgba(255,255,255,0.07);
    font-size: 0.875rem; line-height: 1.8; color: #C9D1D9;
    white-space: pre-wrap;
}

.meta-pill {
    display: inline-block; background: rgba(255,255,255,0.07); border-radius: 100px;
    padding: 3px 12px; font-size: 0.76rem; color: #9CA3AF;
    font-weight: 500; margin-right: 8px; border: 1px solid rgba(255,255,255,0.07);
}

.hook-box {
    background: rgba(59,130,246,0.08); border-radius: 10px;
    padding: 12px 16px; border-left: 3px solid #3B82F6;
    font-size: 0.875rem; color: #93B4F8; margin-top: 14px;
    font-style: italic;
}

.tailor-box {
    background: rgba(245,158,11,0.07); border-radius: 8px;
    padding: 10px 14px; border-left: 3px solid #F59E0B;
    font-size: 0.82rem; color: #C49A20; margin-top: 10px;
}

.hist-card {
    background: #1A1D27; border-radius: 10px;
    padding: 12px 16px; border: 1px solid rgba(255,255,255,0.07); margin: 6px 0;
}
.hist-date { font-size: 0.73rem; color: #6B7280; }
.hist-role { font-size: 0.875rem; font-weight: 600; color: #E2E8F0; }

.tip-row {
    background: rgba(16,185,129,0.07); border-radius: 8px;
    padding: 10px 14px; font-size: 0.82rem; color: #10B981;
    margin-bottom: 16px; border-left: 3px solid #10B981;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="pg-title"><span class="pg-name">Cover Letter</span><span class="pg-sub">JD to recruiter-ready draft in seconds</span></div>', unsafe_allow_html=True)

# ── Resume check ──────────────────────────────────────────────────────────────
resume_saved = store.load_resume()
resume_data  = resume_saved.get("structured_data", {})

if not resume_data:
    st.warning("Build your resume first. Cover letter drafting uses your saved resume context.")
    st.page_link("pages/1_Resume_Builder.py", label="Go to Resume Builder")
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_gen, tab_history = st.tabs(["Generate Letter", "Saved Letters"])

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
            "Generate Cover Letter",
            type="primary",
            use_container_width=True,
        )

    with col_right:
        st.markdown("#### Your Resume Context")
        st.markdown(f"""
        <div style="background:#121927;border-radius:10px;padding:16px 18px;border:1px solid #2b3345;">
            <div style="font-size:0.8rem;color:#9aa8c3;margin-bottom:4px;">Targeting</div>
            <div style="font-size:1rem;font-weight:600;color:#e7eefc;">{resume_data.get('target_title', 'Not set')}</div>
            <div style="font-size:0.8rem;color:#9aa8c3;margin-top:10px;margin-bottom:4px;">Key Skills used</div>
            <div style="font-size:0.85rem;color:#c9d6f4;">{', '.join(resume_data.get('ats_keywords', [])[:8])}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(59,130,246,0.12);border-radius:10px;padding:14px 16px;font-size:0.825rem;color:#bfdbfe;">
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
                log_error(email=email, page="Cover Letter", exc=e, handled=True)
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
                f'<span class="meta-pill">{"JD-tailored" if jd_input.strip() else "General letter"}</span>',
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
            if st.button("Regenerate", use_container_width=True):
                st.session_state.pop("last_cover_letter", None)
                st.rerun()
        with c3:
            st.page_link(
                "pages/4_ATS_Checker.py",
                label="Check ATS Score",
                use_container_width=True,
            )

        st.markdown("""
        <div style="background:rgba(16,185,129,0.13);border-radius:10px;padding:12px 16px;
                    font-size:0.8rem;color:#86efac;margin-top:12px;">
            <strong>Next step:</strong> Paste this letter into the email body when applying.
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
        <div style="background:#111827;border-radius:12px;padding:24px;
                    text-align:center;color:#9aa8c3;margin-top:16px;border:1px dashed #2f3b56;">
            <div style="font-size:2rem;">Mail</div>
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
