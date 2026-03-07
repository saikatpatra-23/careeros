"""
Page 2 - Profile Optimizer
Generates optimized Naukri + LinkedIn content from the saved resume.
"""
import io
import json
import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from auth import require_login, get_user_email
from persistence.store import UserStore
from modules.profile.naukri_enrichment import (
    build_naukri_resume_context,
    get_naukri_followup_questions,
)
from modules.profile.naukri_optimizer import generate_naukri_profile
from modules.profile.linkedin_optimizer import generate_linkedin_profile
from modules.resume.parser import (
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_from_image,
    parse_resume_to_json,
)
from modules.ui.styles import inject_global_css
from config import ANTHROPIC_API_KEY


def _build_naukri_updater_zip(email: str, profile: dict, prefs: dict, resume_saved: dict, naukri_data: dict) -> bytes:
    config_data = {
        "user_email": email,
        "naukri_email": profile.get("naukri_email", ""),
        "naukri_pass_enc": profile.get("naukri_pass_enc", ""),
        "fernet_key": st.secrets.get("FERNET_KEY", "") if hasattr(st, "secrets") else "",
        "headless": False,
        "current_location": prefs.get(
            "current_location",
            prefs.get("locations", [profile.get("preferred_locations", ["Mumbai"])[0] if profile.get("preferred_locations") else "Mumbai"])[0]
            if prefs.get("locations")
            else (profile.get("preferred_locations", ["Mumbai"])[0] if profile.get("preferred_locations") else "Mumbai"),
        ),
        "preferred_locations": prefs.get("locations", profile.get("preferred_locations", [])),
        "resume_data": {
            "target_title": resume_saved.get("structured_data", {}).get("target_title", ""),
            "domain_family": resume_saved.get("domain_family", "enterprise_IT"),
            "summary": resume_saved.get("structured_data", {}).get("summary", ""),
            "ats_keywords": resume_saved.get("structured_data", {}).get("ats_keywords", []),
            "experience": resume_saved.get("structured_data", {}).get("experience", []),
            "skills": resume_saved.get("structured_data", {}).get("skills", {}),
        },
        "naukri_profile_data": naukri_data,
    }

    install_txt = """CareerOS Naukri Profile Updater
================================

1. Unzip this folder anywhere on your Windows PC.
2. Ensure Google Chrome is installed.
3. Put the included `config.json` next to `update_profile.py`.
4. Double-click `run_updater.bat` (recommended), OR open PowerShell in this folder.
5. If using PowerShell, run:
   python update_profile.py

What it updates:
- Headline
- Profile Summary
- Key Skills
- Preferred Locations
- Employment Descriptions (best-effort)

Notes:
- Browser opens visibly by default so you can observe the update.
- If Naukri changes selectors, check the latest files under logs/.
"""

    zip_buffer = io.BytesIO()
    job_applier_dir = Path(__file__).parent.parent / "job_applier"
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("config.json", json.dumps(config_data, indent=2, ensure_ascii=False))
        zf.writestr("INSTALL.txt", install_txt)
        zf.writestr(
            "run_updater.bat",
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            "python update_profile.py\r\n"
            "echo.\r\n"
            "echo Updater finished. Press any key to close.\r\n"
            "pause >nul\r\n",
        )
        for fname in ["update_profile.py", "requirements.txt"]:
            fpath = job_applier_dir / fname
            if fpath.exists():
                zf.write(fpath, fname)
        zf.writestr("logs/.gitkeep", "")
    return zip_buffer.getvalue()


def _render_resume_state(resume_data: dict):
    top_skills = []
    for values in (resume_data.get("skills") or {}).values():
        if isinstance(values, list):
            top_skills.extend(values)
    top_skills = [skill for skill in top_skills if skill][:5]
    stats = [
        f"Primary role: <b>{resume_data.get('target_title', 'Not detected')}</b>",
        f"Current city: <b>{resume_data.get('location', 'Unknown')}</b>",
        f"Experience entries: <b>{len(resume_data.get('experience', []))}</b>",
    ]
    st.markdown(
        f"""
        <div class="co-hero">
            <span class="co-hero-badge">Profile Engine</span>
            <div class="co-hero-title">Turn your resume into a recruiter-ready Naukri profile</div>
            <div class="co-hero-copy">
                Upload a resume or use your CareerOS resume, answer a few high-signal questions, then let CareerOS create the headline,
                summary, skills, and experience copy that your updater can push into Naukri.
            </div>
            <div class="co-inline-stats">
                {''.join(f'<span class="co-pill">{item}</span>' for item in stats)}
                {''.join(f'<span class="co-pill">{skill}</span>' for skill in top_skills)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_followup_form(question_specs: list[dict], existing_answers: dict) -> dict:
    answers = {}
    cols = st.columns(2)
    for idx, spec in enumerate(question_specs):
        col = cols[idx % 2] if spec["type"] != "textarea" else st.container()
        with col:
            default = existing_answers.get(spec["id"], spec.get("default"))
            if spec["type"] == "multiselect":
                answers[spec["id"]] = st.multiselect(
                    spec["label"],
                    spec["options"],
                    default=default or [],
                    help=spec.get("help", ""),
                    key=f"naukri_{spec['id']}",
                )
            elif spec["type"] == "select":
                options = spec["options"]
                selected = default if default in options else options[0]
                answers[spec["id"]] = st.selectbox(
                    spec["label"],
                    options,
                    index=options.index(selected),
                    help=spec.get("help", ""),
                    key=f"naukri_{spec['id']}",
                )
            elif spec["type"] == "number":
                answers[spec["id"]] = st.number_input(
                    spec["label"],
                    min_value=float(spec.get("min", 0.0)),
                    max_value=float(spec.get("max", 100.0)),
                    value=float(default or 0.0),
                    step=float(spec.get("step", 1.0)),
                    help=spec.get("help", ""),
                    key=f"naukri_{spec['id']}",
                )
            else:
                answers[spec["id"]] = st.text_area(
                    spec["label"],
                    value=default or "",
                    height=140,
                    help=spec.get("help", ""),
                    key=f"naukri_{spec['id']}",
                )
    return answers


st.set_page_config(page_title="Profile Optimizer - CareerOS", page_icon="P", layout="wide")
require_login()
inject_global_css()

email = get_user_email()
store = UserStore(email)
profile = store.load_profile()
prefs = store.load_apply_prefs()

st.markdown('<div class="pg-title"><span class="pg-icon">PO</span><span class="pg-name">Profile Optimizer</span><span class="pg-sub">Naukri + LinkedIn content engine</span></div>', unsafe_allow_html=True)

resume_saved = store.load_resume()
resume_data = resume_saved.get("structured_data", {})

if not resume_data:
    st.markdown(
        """
        <div class="co-hero">
            <span class="co-hero-badge">Start Here</span>
            <div class="co-hero-title">No CareerOS resume yet</div>
            <div class="co-hero-copy">You can still start from your existing PDF, DOCX, or image resume. CareerOS will parse it, structure it, and use that as the source for profile generation.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Resume_Builder.py", label="Go to Resume Builder")
    st.markdown('<div class="co-upload-shell">', unsafe_allow_html=True)
    st.markdown('<div class="co-section-kicker">Resume Import</div><div class="co-section-title">Upload your current resume</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload resume",
        type=["pdf", "docx", "jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="po_upload",
    )
    st.markdown('</div>', unsafe_allow_html=True)
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
                    text = extract_text_from_image(file_bytes, ANTHROPIC_API_KEY)
                parsed = parse_resume_to_json(text, ANTHROPIC_API_KEY)
                store.save_resume({
                    "version": 1,
                    "structured_data": parsed,
                    "target_role": parsed.get("target_title", ""),
                    "domain_family": parsed.get("domain_family", ""),
                    "ats_keywords": parsed.get("ats_keywords", []),
                    "role_suggestion": parsed.get("role_suggestion", {}),
                    "created_at": __import__("datetime").datetime.now().isoformat(),
                })
                st.success("Resume parsed. Refreshing your optimizer...")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not parse resume: {exc}")
    st.stop()

saved_opt = store.load_profile_optimizer()
naukri_data = saved_opt.get("naukri", {})
linkedin_data = saved_opt.get("linkedin", {})
followup_answers = saved_opt.get("naukri_followup_answers", {})
question_specs = get_naukri_followup_questions(resume_data, profile, prefs, followup_answers)

_render_resume_state(resume_data)

st.markdown('<div class="co-section-kicker">Workflow</div><div class="co-section-title">Give CareerOS the missing signals recruiters filter on</div>', unsafe_allow_html=True)
left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.markdown('<div class="co-card">', unsafe_allow_html=True)
    st.markdown('<span class="co-badge live">Step 1</span><h4 style="margin-top:0;">Answer the missing-info questions</h4><p class="co-muted">These fields usually do not exist cleanly inside resumes, but they materially change how Naukri recruiters find and filter profiles.</p>', unsafe_allow_html=True)
    with st.form("naukri_followup_form"):
        answers = _render_followup_form(question_specs, followup_answers)
        save_answers = st.form_submit_button("Save profile signals", type="secondary", use_container_width=True)
        generate_naukri = st.form_submit_button("Generate Naukri profile draft", type="primary", use_container_width=True)

    if save_answers or generate_naukri:
        saved_opt["naukri_followup_answers"] = answers
        saved_opt["naukri_source_context"] = build_naukri_resume_context(resume_data, answers, profile, prefs)
        store.save_profile_optimizer(saved_opt)
        followup_answers = answers
        st.success("Profile signals saved.")
        if generate_naukri:
            with st.spinner("Generating your Naukri profile draft..."):
                try:
                    enriched_context = build_naukri_resume_context(resume_data, answers, profile, prefs)
                    naukri_data = generate_naukri_profile(enriched_context, ANTHROPIC_API_KEY)
                    saved_opt["naukri_followup_answers"] = answers
                    saved_opt["naukri_source_context"] = enriched_context
                    saved_opt["naukri"] = naukri_data
                    store.save_profile_optimizer(saved_opt)
                    st.success("Naukri draft generated.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not generate Naukri profile content: {exc}")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    context_preview = build_naukri_resume_context(resume_data, followup_answers, profile, prefs)
    st.markdown('<div class="co-card">', unsafe_allow_html=True)
    st.markdown('<span class="co-badge done">Step 2</span><h4 style="margin-top:0;">Context CareerOS will optimize against</h4>', unsafe_allow_html=True)
    chips = []
    if context_preview.get("target_roles"):
        chips.extend(context_preview.get("target_roles", [])[:3])
    if context_preview.get("preferred_locations"):
        chips.extend(context_preview.get("preferred_locations", [])[:4])
    if context_preview.get("target_industries"):
        chips.extend(context_preview.get("target_industries", [])[:3])
    if chips:
        st.markdown(''.join(f'<span class="co-pill" style="margin:0 8px 8px 0;display:inline-flex;">{chip}</span>' for chip in chips), unsafe_allow_html=True)
    st.markdown('<div class="co-checklist">', unsafe_allow_html=True)
    st.markdown(f'<div class="co-check"><b>Primary role:</b> {context_preview.get("target_title") or resume_data.get("target_title") or "Not set"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="co-check"><b>Notice period:</b> {context_preview.get("notice_period") or "Not set"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="co-check"><b>Work mode:</b> {context_preview.get("work_mode") or "Any"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="co-check"><b>Achievement gap fill:</b> {(context_preview.get("must_win_achievements") or "No extra wins added yet")[:180]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

tab_naukri, tab_linkedin = st.tabs(["Naukri Profile", "LinkedIn Profile"])

with tab_naukri:
    st.markdown('<div class="co-section-kicker">Output</div><div class="co-section-title">Naukri profile draft</div>', unsafe_allow_html=True)

    action_cols = st.columns([1, 1, 1.4])
    with action_cols[0]:
        if st.button("Regenerate Naukri Draft", type="primary", use_container_width=True):
            with st.spinner("Regenerating your Naukri profile draft..."):
                try:
                    enriched_context = build_naukri_resume_context(resume_data, followup_answers, profile, prefs)
                    naukri_data = generate_naukri_profile(enriched_context, ANTHROPIC_API_KEY)
                    saved_opt["naukri_source_context"] = enriched_context
                    saved_opt["naukri"] = naukri_data
                    store.save_profile_optimizer(saved_opt)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")
    with action_cols[1]:
        st.caption("Use this after changing answers or target roles.")
    with action_cols[2]:
        if naukri_data:
            st.markdown('<div class="co-info">Draft ready. Review it below, then download the updater to apply the content on your PC.</div>', unsafe_allow_html=True)

    if not naukri_data:
        st.markdown('<div class="co-card"><p class="co-muted" style="margin:0;">Generate your Naukri draft after saving the missing signals above.</p></div>', unsafe_allow_html=True)
    else:
        top_row = st.columns(2, gap="large")
        with top_row[0]:
            st.markdown('<div class="co-card">', unsafe_allow_html=True)
            st.markdown('<span class="co-badge done">Headline</span>', unsafe_allow_html=True)
            st.text_area("headline", value=naukri_data.get("headline", ""), height=110, disabled=True, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        with top_row[1]:
            st.markdown('<div class="co-card">', unsafe_allow_html=True)
            st.markdown('<span class="co-badge done">Profile Summary</span>', unsafe_allow_html=True)
            st.text_area("profile_summary", value=naukri_data.get("profile_summary", ""), height=160, disabled=True, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        skill_cols = st.columns(2, gap="large")
        with skill_cols[0]:
            st.markdown('<div class="co-card"><span class="co-badge live">Skills To Add</span>', unsafe_allow_html=True)
            for skill in naukri_data.get("skills_add", []):
                st.markdown(f"- {skill}")
            st.markdown('</div>', unsafe_allow_html=True)
        with skill_cols[1]:
            st.markdown('<div class="co-card"><span class="co-badge">Priority Skills</span>', unsafe_allow_html=True)
            for skill in naukri_data.get("top_5_skills", []):
                st.markdown(f"- {skill}")
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<span class="co-badge soon">Skills To Remove</span>', unsafe_allow_html=True)
            for skill in naukri_data.get("skills_remove", []):
                st.markdown(f"- {skill}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="co-card">', unsafe_allow_html=True)
        st.markdown('<span class="co-badge live">Employment Copy</span><p class="co-muted">Use these descriptions inside the corresponding Naukri employment sections.</p>', unsafe_allow_html=True)
        for emp in naukri_data.get("employment_descriptions", []):
            with st.expander(f"{emp.get('designation', '')} @ {emp.get('company', '')}"):
                st.text_area(
                    f"emp_{emp.get('company', '')}",
                    value=emp.get("description", ""),
                    height=220,
                    disabled=True,
                    label_visibility="collapsed",
                )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="co-card">', unsafe_allow_html=True)
        st.markdown('<span class="co-badge done">Completeness Checklist</span>', unsafe_allow_html=True)
        for tip in naukri_data.get("profile_completeness_tips", []):
            st.markdown(f"- {tip}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="co-section-kicker">Updater</div><div class="co-section-title">Push this draft into Naukri</div>', unsafe_allow_html=True)
        if not profile.get("naukri_email") or not profile.get("naukri_pass_enc"):
            st.warning("Save your Naukri credentials on the Setup page first. Then come back here to download the updater.")
            st.page_link("pages/0_Setup.py", label="Go to Setup")
        else:
            updater_zip = _build_naukri_updater_zip(email, profile, prefs, resume_saved, naukri_data)
            st.download_button(
                label="Download Runner (then run locally)",
                data=updater_zip,
                file_name="careeros_naukri_profile_updater.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary",
            )
            st.markdown("#### Beta User Steps (Easy)")
            st.markdown(
                "1. Click **Download Runner (then run locally)**\n"
                "2. Extract the ZIP on your Windows laptop\n"
                "3. Double-click `run_updater.bat`\n"
                "4. Wait while browser updates your Naukri profile\n"
                "5. Check terminal/log files if any step fails"
            )
            st.markdown("**Requirements:** Windows + Chrome + Python installed")
            st.code("python --version", language="bash")
            st.markdown(
                '<div class="co-tip"><b>Important:</b> Streamlit app direct Naukri profile update nahi karta. '
                'Ye ZIP local runner download karta hai. ZIP unzip karo aur <code>run_updater.bat</code> run karo '
                '(ya PowerShell me <code>python update_profile.py</code>). Tabhi profile update hota hai.</div>',
                unsafe_allow_html=True,
            )

with tab_linkedin:
    st.markdown('<div class="co-section-kicker">Output</div><div class="co-section-title">LinkedIn profile draft</div>', unsafe_allow_html=True)
    if not linkedin_data:
        if st.button("Generate LinkedIn Draft", type="primary"):
            with st.spinner("Generating your LinkedIn profile content..."):
                try:
                    linkedin_data = generate_linkedin_profile(resume_data, ANTHROPIC_API_KEY)
                    saved_opt["linkedin"] = linkedin_data
                    store.save_profile_optimizer(saved_opt)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")
    else:
        if st.button("Regenerate LinkedIn Draft"):
            with st.spinner("Regenerating..."):
                try:
                    linkedin_data = generate_linkedin_profile(resume_data, ANTHROPIC_API_KEY)
                    saved_opt["linkedin"] = linkedin_data
                    store.save_profile_optimizer(saved_opt)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")

    if linkedin_data:
        score = linkedin_data.get("estimated_resumeworded_score", "75-80")
        st.markdown(f'<div class="co-card"><span class="co-badge done">Estimated score</span><h4 style="margin:0;">Resumeworded target: {score}</h4></div>', unsafe_allow_html=True)
        st.markdown('<div class="co-card">', unsafe_allow_html=True)
        st.markdown('<span class="co-badge live">Implementation Checklist</span>', unsafe_allow_html=True)
        for item in linkedin_data.get("resumeworked_checklist", []):
            st.markdown(f"- [ ] **{item.get('item', '')}** - _{item.get('action', '')}_")
        st.markdown('</div>', unsafe_allow_html=True)

        for i, headline in enumerate(linkedin_data.get("headline_options", []), 1):
            st.markdown(f"#### Headline Option {i}")
            st.text_area(f"li_headline_{i}", value=headline, height=80, disabled=True, label_visibility="collapsed")

        st.markdown("#### About Section")
        st.text_area("li_about", value=linkedin_data.get("about_section", ""), height=220, disabled=True, label_visibility="collapsed")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Top 5 Skills")
            for skill in linkedin_data.get("top_5_skills", []):
                st.markdown(f"- {skill}")
        with col2:
            st.markdown("#### All 50 Skills")
            all_skills = linkedin_data.get("all_skills_50", [])
            st.caption(f"{len(all_skills)} skills")
            st.write(", ".join(all_skills))

        st.markdown("#### Experience Bullets")
        for exp in linkedin_data.get("experience_bullets", []):
            with st.expander(f"{exp.get('title', '')} @ {exp.get('company', '')}"):
                for bullet in exp.get("bullets", []):
                    st.markdown(f"- {bullet}")
