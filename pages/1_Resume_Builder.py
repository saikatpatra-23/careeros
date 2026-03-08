# -*- coding: utf-8 -*-
"""
Page 1 — Resume Builder
Deep probing chat → Role suggestion → ATS Word resume download.
"""
import os, sys
import html
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email, get_user_name
from modules.telemetry.tracker import install_error_tracking, log_error, track_page_view
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

st.set_page_config(page_title="Resume Builder - CareerOS", page_icon="R", layout="wide")
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

.rb-chat-shell {
    border: 1px solid #2b3345;
    border-radius: 16px;
    background: linear-gradient(180deg, #161b27 0%, #111726 100%);
    overflow: hidden;
}
.rb-chat-head {
    padding: 14px 18px;
    border-bottom: 1px solid #232c3f;
    font-size: 1.5rem;
    font-weight: 800;
}
.rb-chat-body {
    padding: 16px 18px;
    display: grid;
    gap: 12px;
}
.rb-row { display: flex; }
.rb-row.user { justify-content: flex-end; }
.rb-bubble-ai {
    max-width: 78%;
    background: #2a313f;
    color: #eaf0ff;
    border-radius: 14px;
    padding: 12px 14px;
    line-height: 1.5;
}
.rb-bubble-user {
    max-width: 66%;
    background: #3c6df0;
    color: #f8fbff;
    border-radius: 14px;
    padding: 11px 14px;
    line-height: 1.4;
    font-weight: 600;
}

.rb-msg-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    margin: 10px 0;
}
.rb-msg-row-user {
    justify-content: flex-end;
}
.rb-avatar {
    width: 32px;
    height: 32px;
    border-radius: 999px;
    background: #1d2a47;
    border: 1px solid #2b3b61;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
}
.rb-avatar-user {
    background: #2a3347;
    border-color: #394760;
}
.rb-msg {
    max-width: 74%;
    border-radius: 14px;
    padding: 11px 14px;
    line-height: 1.6;
    font-size: 1rem;
}
.rb-msg-ai {
    background: #2a313f;
    border: 1px solid #3a4358;
    color: #eaf0ff;
}
.rb-msg-user {
    background: #2a313f;
    border: 1px solid #3a4358;
    color: #eaf0ff;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

email = get_user_email()
name  = get_user_name()
install_error_tracking(email=email, page="Resume Builder")
track_page_view(email=email, page="Resume Builder")
store = UserStore(email)

# Purge stale draft (>7 days idle) silently on every page load
store.purge_stale_draft(days=7)

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

st.markdown('<div class="pg-title"><span class="pg-name">Resume Builder</span><span class="pg-sub">Chat to ATS resume in Word + PDF</span></div>', unsafe_allow_html=True)


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
    st.session_state.rb_exchange = 0
    st.session_state.rb_step     = 2
    store.save_draft_state(step=2, exchange_count=0)
    st.rerun()


def _render_chat_bubble(role: str, text: str):
    safe = html.escape(text or "").replace("\n", "<br>")
    if role == "assistant":
        st.markdown(
            f'<div class="rb-msg-row"><div class="rb-avatar">🤖</div><div class="rb-msg rb-msg-ai">{safe}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="rb-msg-row rb-msg-row-user"><div class="rb-msg rb-msg-user">{safe}</div><div class="rb-avatar rb-avatar-user">🧑</div></div>',
            unsafe_allow_html=True,
        )


# =============================================================================
# STEP 1 — INTRO
# =============================================================================
if st.session_state.rb_step == 1:
    existing    = store.load_profile()
    saved_chat  = store.load_chat_history()
    draft_state = store.load_draft_state()
    vault       = store.load_resume_vault()

    has_draft   = bool(saved_chat)
    has_vault   = bool(vault)

    _milestone_bar(0, False)

    st.markdown(
        """
        <div class="rb-chat-shell">
            <div class="rb-chat-head">AI Resume Assistant</div>
            <div class="rb-chat-body">
                <div class="rb-row"><div class="rb-bubble-ai">Hi! I will build your ATS resume in chat. What is your current job title?</div></div>
                <div class="rb-row user"><div class="rb-bubble-user">Senior Product Manager at Flipkart</div></div>
                <div class="rb-row"><div class="rb-bubble-ai">Great. Share 2-3 key wins with numbers and team impact.</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("No long forms. Just answer in chat and generate in ~10 minutes.")

    if has_draft:
        saved_exchanges = draft_state.get("exchange_count", len(saved_chat) // 2)
        saved_at = draft_state.get("saved_at", "")
        saved_label = ""
        if saved_at:
            import datetime as _dt
            try:
                saved_label = _dt.datetime.fromisoformat(saved_at).strftime("%d %b, %I:%M %p")
            except Exception:
                pass
        st.info(
            f"In-progress chat found: {saved_exchanges} exchange{'s' if saved_exchanges != 1 else ''}"
            + (f" (last saved: {saved_label})" if saved_label else "")
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Continue Chat", type="primary", use_container_width=True):
                session = ResumeBuilderSession.restore(_get_api_key(), saved_chat, saved_exchanges)
                st.session_state.rb_session  = session
                st.session_state.rb_chat     = [(m["role"], m["content"]) for m in saved_chat]
                st.session_state.rb_exchange = session.exchange_count
                st.session_state.rb_step     = 2
                st.rerun()
        with col_b:
            if st.button("Start Fresh", use_container_width=True):
                store.save("resume_chat.json", [])
                store.save("resume_draft_state.json", {})
                _start_new_session(existing)
    else:
        if st.button("Start Resume Chat", type="primary", use_container_width=True):
            _start_new_session(existing)

    st.markdown('<div class="co-card" style="margin-top:12px;">', unsafe_allow_html=True)
    st.markdown("#### Upload Existing Resume (Optional)")
    st.caption("Upload and skip directly to generated draft.")
    uploaded_new = st.file_uploader(
        "Upload resume",
        type=["pdf", "docx", "jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="rb_upload_step1_chat",
    )
    if uploaded_new is not None:
        with st.spinner("Parsing your resume... (15-30 seconds)"):
            try:
                file_bytes = uploaded_new.read()
                ext = uploaded_new.name.rsplit(".", 1)[-1].lower()
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
                })
                st.session_state.rb_resume = parsed
                st.session_state.rb_step   = 3
                st.rerun()
            except Exception as e:
                log_error(email=email, page="Resume Builder", exc=e, handled=True)
                st.error(f"Could not parse resume: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    if has_vault:
        st.divider()
        st.markdown("#### Resume Vault")
        st.caption(f"{len(vault)} saved resume{'s' if len(vault) > 1 else ''}.")
        for i, saved in enumerate(vault):
            label = saved.get("vault_label", f"Resume {len(vault) - i}")
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{label}**")
            with c2:
                if st.button("Load", key=f"vault_load_chat_{i}", use_container_width=True):
                    resume_data = saved.get("structured_data", saved)
                    st.session_state.rb_resume = resume_data
                    st.session_state.rb_step   = 3
                    st.rerun()

    st.stop()

    col_info, col_how = st.columns([3, 2])
    with col_info:
        st.markdown('<div class="co-card">', unsafe_allow_html=True)
        st.markdown("### How it works")
        st.markdown("""
Quick 3-step flow:

1. Share your role, work history, and achievements in chat
2. CareerOS rewrites it into ATS-friendly resume content
3. Download ready-to-use Word and PDF resumes

**Time needed: ~10 minutes.**
        """)

        if has_draft:
            saved_exchanges = draft_state.get("exchange_count", len(saved_chat) // 2)
            saved_at        = draft_state.get("saved_at", "")
            saved_label     = ""
            if saved_at:
                import datetime as _dt
                try:
                    saved_label = _dt.datetime.fromisoformat(saved_at).strftime("%d %b, %I:%M %p")
                except Exception:
                    pass
            st.info(
                f"**In-progress session found** — {saved_exchanges} exchange{'s' if saved_exchanges != 1 else ''} saved"
                + (f" (last saved: {saved_label})" if saved_label else "")
                + "\n\nContinue from where you left off, or start fresh."
            )
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Continue from where I left off", type="primary", use_container_width=True):
                    session = ResumeBuilderSession.restore(_get_api_key(), saved_chat, saved_exchanges)
                    st.session_state.rb_session  = session
                    st.session_state.rb_chat     = [(m["role"], m["content"]) for m in saved_chat]
                    st.session_state.rb_exchange = session.exchange_count
                    st.session_state.rb_step     = 2
                    st.rerun()
            with col_b:
                if st.button("Start fresh instead", use_container_width=True):
                    store.save("resume_chat.json", [])
                    store.save("resume_draft_state.json", {})
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
                    })
                    st.session_state.rb_resume = parsed
                    st.session_state.rb_step   = 3
                    st.rerun()
                except Exception as e:
                    log_error(email=email, page="Resume Builder", exc=e, handled=True)
                    st.error(f"Could not parse resume: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_how:
        st.markdown('<div class="co-card">', unsafe_allow_html=True)
        st.markdown("### Why this is different")
        st.markdown("• Naukri + ATS focused output")
        st.markdown("• Recruiter-friendly wording")
        st.markdown("• Hindi/English chat support")
        st.markdown("• Role-fit and market-aware suggestions")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Resume Vault — full width below both columns ───────────────────────────
    if has_vault:
        st.divider()
        st.markdown("#### 🗄️ Resume Vault")
        st.caption(f"{len(vault)} saved resume{'s' if len(vault) > 1 else ''} — load any previous version instantly.")
        for i, saved in enumerate(vault):
            label = saved.get("vault_label", f"Resume {len(vault) - i}")
            v_col1, v_col2 = st.columns([5, 1])
            with v_col1:
                st.markdown(f"**{label}**")
            with v_col2:
                if st.button("Load", key=f"vault_load_{i}", use_container_width=True):
                    resume_data = saved.get("structured_data", saved)
                    st.session_state.rb_resume = resume_data
                    st.session_state.rb_step   = 3
                    st.rerun()


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

    # ── Chat history bubble rendering ─────────────────────────────────────────
    for role, text in st.session_state.rb_chat:
        _render_chat_bubble(role, text)

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input(
        "Hindi ya English — jisme comfortable ho usi mein jawab do...",
        key=f"rb_chat_input_{exchanges}",
    )

    if user_input and user_input.strip():
        # Show user message immediately
        _render_chat_bubble("user", user_input.strip())

        # Get AI response
        with st.spinner("CareerOS is thinking..."):
            try:
                reply = session.send(user_input.strip())
            except Exception as e:
                log_error(email=email, page="Resume Builder", exc=e, handled=True)
                st.error(f"API error: {e}")
                st.stop()
        _render_chat_bubble("assistant", reply)

        st.session_state.rb_chat.append(("user", user_input.strip()))
        st.session_state.rb_chat.append(("assistant", reply))
        st.session_state.rb_exchange = session.exchange_count
        store.save_chat_history(session.get_messages_for_storage())
        store.save_draft_state(step=2, exchange_count=session.exchange_count)
        st.rerun()

    st.divider()

    # ── Action buttons ────────────────────────────────────────────────────────
    gen_col, restart_col = st.columns([3, 1])
    with gen_col:
        if can_gen:
            if st.button("Generate My Resume", type="primary", use_container_width=True):
                with st.spinner("CareerOS is building your resume... (30-60 seconds)"):
                    try:
                        resume_data = session.generate_resume()
                    except Exception as e:
                        log_error(email=email, page="Resume Builder", exc=e, handled=True)
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
            st.caption(
                f"Share {MIN_PROBE_ROUNDS - exchanges} more exchange{'s' if MIN_PROBE_ROUNDS - exchanges != 1 else ''} to unlock generation."
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
                    log_error(email=email, page="Resume Builder", exc=e, handled=True)
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
                    log_error(email=email, page="Resume Builder", exc=e, handled=True)
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
    st.info("**Next step:** Go to **Profile Optimizer** → get your Naukri headline, summary, and LinkedIn About — copy-paste ready for recruiter search ranking.")
    st.markdown("<br>", unsafe_allow_html=True)
    st.page_link("pages/2_Profile_Optimizer.py", label="Go to Profile Optimizer →", icon="🔗")
