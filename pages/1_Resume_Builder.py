# -*- coding: utf-8 -*-
"""
Page 1 — Resume Builder
Deep probing chat → Role suggestion → ATS Word resume download.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email, get_user_name
from persistence.store import UserStore
from modules.resume.session import ResumeBuilderSession
from modules.resume.word_export import export_to_docx, get_filename
from modules.resume.pdf_export import export_to_pdf, get_pdf_filename
from modules.resume.parser import (
    extract_text_from_docx, extract_text_from_pdf,
    extract_text_from_image, parse_resume_to_json,
)
from modules.ui.styles import inject_global_css
from config import MIN_PROBE_ROUNDS

def _get_api_key() -> str:
    """Read API key at runtime so st.secrets is available."""
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")

st.set_page_config(page_title="Resume Builder – CareerOS", page_icon="📄", layout="wide")
require_login()
inject_global_css()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Milestone bar — dark */
.milestone-bar {
    display: flex; align-items: center; gap: 0;
    margin: 14px 0; background: #1A1D27;
    border-radius: 10px; padding: 12px 18px;
    border: 1px solid rgba(255,255,255,0.07);
}
.milestone {
    display: flex; flex-direction: column; align-items: center;
    flex: 1; font-size: 0.68rem; color: #6B7280;
    text-align: center; position: relative;
}
.milestone.active { color: #4F8EF7; font-weight: 600; }
.milestone.done   { color: #10B981; }
.milestone .dot {
    width: 26px; height: 26px; border-radius: 50%;
    background: rgba(255,255,255,0.06);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; margin-bottom: 4px;
    border: 1.5px solid rgba(255,255,255,0.1);
}
.milestone.active .dot { background: rgba(79,142,247,0.15); border-color: #4F8EF7; color: #4F8EF7; }
.milestone.done   .dot { background: rgba(16,185,129,0.15); border-color: #10B981;  color: #10B981; }
.milestone-line {
    height: 2px; flex: 1; background: rgba(255,255,255,0.07);
    margin-bottom: 20px; min-width: 16px;
}
.milestone-line.done { background: #10B981; }

/* Info banner */
.info-banner {
    background: rgba(79,142,247,0.08);
    border-radius: 8px; padding: 10px 14px;
    font-size: 0.85rem; color: #93B4F8;
    border-left: 3px solid #4F8EF7; margin: 10px 0;
}

/* Role card */
.role-card {
    background: #1A1D27; border-radius: 12px;
    padding: 18px 22px;
    border: 1px solid rgba(16,185,129,0.25);
    border-left: 4px solid #10B981; margin: 12px 0;
}
.warn-card {
    background: rgba(245,158,11,0.07);
    border-radius: 8px; padding: 12px 16px;
    border-left: 3px solid #F59E0B;
    margin: 8px 0; font-size: 0.875rem; color: #C49A20;
}

/* Unlock banner */
.unlock-banner {
    background: rgba(16,185,129,0.1);
    border-radius: 10px; padding: 14px 18px;
    border-left: 4px solid #10B981;
    font-size: 0.9rem; color: #10B981;
    font-weight: 600; text-align: center; margin: 10px 0;
}

/* Chat */
.stChatMessage { border-radius: 10px !important; }
.stChatInputContainer { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

email = get_user_email()
name  = get_user_name()
store = UserStore(email)

# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "rb_step":      1,
        "rb_session":   None,
        "rb_chat":      [],
        "rb_resume":    None,
        "rb_doc_bytes": None,
        "rb_pdf_bytes": None,
        "rb_exchange":  0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

st.markdown('<div class="pg-title"><span class="pg-icon">📄</span><span class="pg-name">Resume Builder</span><span class="pg-sub">Chat → ATS resume → Word + PDF</span></div>', unsafe_allow_html=True)


# ── Milestone bar helper ───────────────────────────────────────────────────────
def _milestone_bar(exchanges, ready):
    milestones = [
        ("👋", "Start"),
        ("🗣️", "Your Story"),
        ("📊", "Achievements"),
        ("💡", "Role Match"),
        ("✅", "Ready!"),
    ]
    # Map exchanges to milestone index
    idx = 0
    if exchanges >= 2:  idx = 1
    if exchanges >= 4:  idx = 2
    if exchanges >= 6:  idx = 3
    if ready:           idx = 4

    parts = []
    for i, (icon, label) in enumerate(milestones):
        if i < idx:
            cls = "done"; dot_icon = "✓"
        elif i == idx:
            cls = "active"; dot_icon = icon
        else:
            cls = ""; dot_icon = icon

        parts.append(f'<div class="milestone {cls}"><div class="dot">{dot_icon}</div>{label}</div>')
        if i < len(milestones) - 1:
            line_cls = "done" if i < idx else ""
            parts.append(f'<div class="milestone-line {line_cls}"></div>')

    st.markdown(f'<div class="milestone-bar">{"".join(parts)}</div>', unsafe_allow_html=True)


def _start_new_session(existing_profile):
    with st.spinner("Starting CareerOS session..."):
        session = ResumeBuilderSession(api_key=_get_api_key(), existing_profile=existing_profile)
        opening = session.start()
    st.session_state.rb_session  = session
    st.session_state.rb_chat     = [("assistant", opening)]
    st.session_state.rb_step     = 2
    st.rerun()


# =============================================================================
# STEP 1 — INTRO
# =============================================================================
if st.session_state.rb_step == 1:
    existing  = store.load_profile()
    has_prev  = bool(existing.get("current_title"))

    _milestone_bar(0, False)

    col_info, col_how = st.columns([3, 2])
    with col_info:
        st.markdown("### How it works")
        st.markdown("""
CareerOS will have a **real conversation** with you — in Hindi or English, whichever feels natural.

It will ask about your work, your achievements, and what makes you good at what you do. Then it will:

1. **Suggest the best role** for you based on your actual signals (not just what you say you want)
2. **Reposition your experience** into strong, ATS-optimised language
3. **Generate a Word resume** ready to upload to Naukri, LinkedIn, and email

**Roughly 10-15 minutes → professional resume ready.**
        """)

        if has_prev:
            st.info(f"Previous profile found: **{existing.get('current_title')}** at **{existing.get('current_company', '')}**")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Continue from last session", type="primary", use_container_width=True):
                    saved_chat = store.load_chat_history()
                    if saved_chat:
                        session = ResumeBuilderSession.restore(_get_api_key(), saved_chat, len(saved_chat) // 2)
                        st.session_state.rb_session  = session
                        st.session_state.rb_chat     = [(m["role"], m["content"]) for m in saved_chat]
                        st.session_state.rb_exchange  = session.exchange_count
                        st.session_state.rb_step      = 2
                        st.rerun()
            with col_b:
                if st.button("Start fresh", use_container_width=True):
                    _start_new_session(existing)
        else:
            if st.button("Start Building My Resume →", type="primary", use_container_width=True):
                _start_new_session(existing)

        st.markdown("---")
        st.markdown("#### Or upload an existing resume")
        st.caption("We'll parse it and jump straight to the download step.")
        uploaded = st.file_uploader(
            "Upload resume",
            type=["pdf", "docx", "jpg", "jpeg", "png"],
            label_visibility="collapsed",
            key="rb_upload_step1",
        )
        if uploaded is not None:
            with st.spinner("Parsing your resume... (15-30 seconds)"):
                try:
                    file_bytes = uploaded.read()
                    ext = uploaded.name.rsplit(".", 1)[-1].lower()
                    if ext == "docx":
                        text = extract_text_from_docx(file_bytes)
                    elif ext == "pdf":
                        text = extract_text_from_pdf(file_bytes)
                    else:
                        text = extract_text_from_image(file_bytes, _get_api_key())
                    parsed = parse_resume_to_json(text, _get_api_key())
                    store.save_resume({
                        "version":         1,
                        "structured_data": parsed,
                        "target_role":     parsed.get("target_title", ""),
                        "domain_family":   parsed.get("domain_family", ""),
                        "ats_keywords":    parsed.get("ats_keywords", []),
                        "role_suggestion": parsed.get("role_suggestion", {}),
                        "created_at":      __import__("datetime").datetime.now().isoformat(),
                    })
                    st.session_state.rb_resume = parsed
                    st.session_state.rb_step   = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not parse resume: {e}")

    with col_how:
        st.markdown("### What makes CareerOS different")
        st.markdown("""
<div style="background:white;border-radius:12px;padding:20px;border:1.5px solid #E2E8F0;">

**Knows how Naukri works** — RChilli ATS, search ranking, keyword density

**Knows how recruiters think** — 6-second scan, what triggers a call

**Bilingual** — Hindi ya English, dono chalega

**Repositions your story** — operational language → leadership language automatically

**Honest** — if you want role X but fit role Y, we'll tell you + give you a bridge path

**India-specific salary bands** — know your market worth

</div>
        """, unsafe_allow_html=True)


# =============================================================================
# STEP 2 — PROBING CHAT
# =============================================================================
if st.session_state.rb_step == 2:
    session: ResumeBuilderSession = st.session_state.rb_session
    exchanges = st.session_state.rb_exchange
    can_gen   = session.ready_to_generate or exchanges >= MIN_PROBE_ROUNDS

    # Milestone bar
    _milestone_bar(exchanges, session.ready_to_generate)

    # Unlock banner
    if session.ready_to_generate:
        st.markdown('<div class="unlock-banner">🎉 CareerOS has enough context! You can generate your resume now — or keep chatting to add more detail.</div>', unsafe_allow_html=True)
    elif can_gen:
        st.markdown(f'<div class="info-banner">You\'ve shared enough to get started! Generate when ready, or keep going for a more detailed resume.</div>', unsafe_allow_html=True)
    else:
        remaining = MIN_PROBE_ROUNDS - exchanges
        st.markdown(f'<div class="info-banner">🗣️ Keep sharing — {remaining} more exchange{"s" if remaining != 1 else ""} before you can generate. The more detail, the stronger your resume.</div>', unsafe_allow_html=True)

    st.divider()

    # ── Chat history using st.chat_message ────────────────────────────────────
    for role, text in st.session_state.rb_chat:
        if role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(text)
        else:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(text)

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input(
        "Hindi ya English — jisme comfortable ho usi mein jawab do...",
        key=f"rb_chat_input_{exchanges}",
    )

    if user_input and user_input.strip():
        # Show user message immediately
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input.strip())

        # Get AI response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("CareerOS is thinking..."):
                try:
                    reply = session.send(user_input.strip())
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()
            st.markdown(reply)

        st.session_state.rb_chat.append(("user", user_input.strip()))
        st.session_state.rb_chat.append(("assistant", reply))
        st.session_state.rb_exchange = session.exchange_count
        store.save_chat_history(session.get_messages_for_storage())
        st.rerun()

    st.divider()

    # ── Action buttons ────────────────────────────────────────────────────────
    gen_col, restart_col = st.columns([3, 1])
    with gen_col:
        if can_gen:
            if st.button("✨ Generate My Resume Now", type="primary", use_container_width=True):
                with st.spinner("CareerOS is building your resume... (30-60 seconds)"):
                    try:
                        resume_data = session.generate_resume()
                    except Exception as e:
                        st.error(f"Generation failed: {e}")
                        st.stop()
                store.save_resume({
                    "version":         1,
                    "structured_data": resume_data,
                    "target_role":     resume_data.get("target_title", ""),
                    "domain_family":   resume_data.get("domain_family", ""),
                    "ats_keywords":    resume_data.get("ats_keywords", []),
                    "role_suggestion": resume_data.get("role_suggestion", {}),
                    "created_at":      __import__("datetime").datetime.now().isoformat(),
                })
                st.session_state.rb_resume = resume_data
                st.session_state.rb_step   = 3
                st.rerun()
        else:
            st.button(
                f"✨ Generate My Resume (share {MIN_PROBE_ROUNDS - exchanges} more exchange{'s' if MIN_PROBE_ROUNDS - exchanges != 1 else ''})",
                disabled=True,
                use_container_width=True,
            )

    with restart_col:
        if st.button("Start Over", use_container_width=True):
            for k in ["rb_step", "rb_session", "rb_chat", "rb_resume", "rb_doc_bytes", "rb_pdf_bytes", "rb_exchange"]:
                st.session_state.pop(k, None)
            _init()
            st.rerun()


# =============================================================================
# STEP 3 — RESULT
# =============================================================================
if st.session_state.rb_step == 3:
    resume_data = st.session_state.rb_resume or store.load_resume().get("structured_data", {})
    if not resume_data:
        st.error("Resume data not found. Please go back and generate again.")
        st.stop()

    _milestone_bar(99, True)
    st.markdown('<div class="unlock-banner">🎉 Your resume is ready! Review below, then download your Word file.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    role_suggestion = resume_data.get("role_suggestion", {})

    # Role suggestion card
    if role_suggestion:
        primary    = role_suggestion.get("primary_role", "")
        confidence = role_suggestion.get("confidence", "")
        reasoning  = role_suggestion.get("reasoning", "")
        warning    = role_suggestion.get("domain_mismatch_warning", "")
        gap        = role_suggestion.get("gap_assessment", "")
        alts       = role_suggestion.get("alternate_roles", [])
        salary     = role_suggestion.get("salary_band_india", "")
        conf_color = "#059669" if confidence == "High" else "#D97706"

        st.markdown(f"""
        <div class="role-card">
            <div style="font-size:0.8rem;color:#6B7280;font-weight:600;text-transform:uppercase;letter-spacing:.05em;">CareerOS Role Recommendation</div>
            <div style="font-size:1.35rem;font-weight:700;color:#1F273A;margin:6px 0 4px 0;">🎯 {primary}</div>
            <span style="background:{conf_color};color:white;padding:2px 10px;border-radius:100px;font-size:0.75rem;font-weight:600;">{confidence} Confidence</span>
            <br><br>
            <div style="color:#374151;line-height:1.6;">{reasoning}</div>
            <br>
            <div style="font-size:0.875rem;color:#6B7280;">
                <strong>Alternate roles:</strong> {", ".join(alts)}<br>
                <strong>Salary band (India):</strong> {salary}
            </div>
        </div>""", unsafe_allow_html=True)

        if warning:
            st.markdown(f'<div class="warn-card">⚠️ <strong>Domain Mismatch Warning:</strong> {warning}</div>', unsafe_allow_html=True)
        if gap and gap.lower() not in ("none", "none significant", ""):
            st.markdown(f'<div class="warn-card">📍 <strong>Gap to address:</strong> {gap}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### Resume Preview")

    col_l, col_r = st.columns(2)

    with col_l:
        with st.expander("Professional Summary", expanded=True):
            st.write(resume_data.get("summary", ""))
        with st.expander("ATS Keywords"):
            keywords = resume_data.get("ats_keywords", [])
            st.markdown(" • ".join(f"`{k}`" for k in keywords))

    with col_r:
        skills = resume_data.get("skills", {})
        with st.expander("Skills"):
            for category, items in skills.items():
                if items:
                    st.markdown(f"**{category}:** {', '.join(items)}")

    exp_list = resume_data.get("experience", [])
    if exp_list:
        with st.expander("Work Experience", expanded=True):
            for job in exp_list:
                st.markdown(f"**{job.get('title')} @ {job.get('company')}** — {job.get('period','')}")
                for b in job.get("bullets", []):
                    st.markdown(f"- {b}")
                st.markdown("")

    # Download
    st.divider()
    word_col, pdf_col, back_col = st.columns([2, 2, 1])

    with word_col:
        if st.button("📄 Build Word (.docx)", type="primary", use_container_width=True):
            with st.spinner("Building Word resume..."):
                try:
                    st.session_state.rb_doc_bytes = export_to_docx(resume_data)
                except Exception as e:
                    st.error(f"Export failed: {e}")
        if st.session_state.rb_doc_bytes:
            st.download_button(
                label="⬇️ Download Word (.docx)",
                data=st.session_state.rb_doc_bytes,
                file_name=get_filename(resume_data),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

    with pdf_col:
        if st.button("📑 Build PDF (.pdf)", use_container_width=True):
            with st.spinner("Building PDF resume..."):
                try:
                    st.session_state.rb_pdf_bytes = export_to_pdf(resume_data)
                except Exception as e:
                    st.error(f"PDF export failed: {e}")
        if st.session_state.rb_pdf_bytes:
            st.download_button(
                label="⬇️ Download PDF (.pdf)",
                data=st.session_state.rb_pdf_bytes,
                file_name=get_pdf_filename(resume_data),
                mime="application/pdf",
                use_container_width=True,
            )

    if st.session_state.rb_doc_bytes or st.session_state.rb_pdf_bytes:
        st.success("Resume ready! Upload directly to Naukri or attach to job applications.")

    with back_col:
        if st.button("← Back to Chat", use_container_width=True):
            st.session_state.rb_step = 2
            st.rerun()

    st.divider()
    st.markdown("""
    <div style="background:white;border-radius:12px;padding:20px;border:1.5px solid #E2E8F0;text-align:center;">
        <strong>Next step:</strong> Go to <strong>Profile Optimizer</strong> → get your Naukri headline,
        summary, and LinkedIn About — copy-paste ready for recruiter search ranking.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/2_Profile_Optimizer.py", label="Go to Profile Optimizer →", icon="🔗")
