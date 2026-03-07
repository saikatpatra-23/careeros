# -*- coding: utf-8 -*-
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
4. Open PowerShell in this folder.
5. Run:
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
        for fname in ["update_profile.py", "requirements.txt"]:
            fpath = job_applier_dir / fname
            if fpath.exists():
                zf.write(fpath, fname)
        zf.writestr("logs/.gitkeep", "")
    return zip_buffer.getvalue()


st.set_page_config(page_title="Profile Optimizer - CareerOS", page_icon="🔗", layout="wide")
require_login()
inject_global_css()

email = get_user_email()
store = UserStore(email)
profile = store.load_profile()
prefs = store.load_apply_prefs()

st.markdown('<div class="pg-title"><span class="pg-icon">🔗</span><span class="pg-name">Profile Optimizer</span><span class="pg-sub">Naukri + LinkedIn content</span></div>', unsafe_allow_html=True)

resume_saved = store.load_resume()
resume_data = resume_saved.get("structured_data", {})

if not resume_data:
    st.warning("No resume found. Build your resume first - or upload one below to get started.")
    st.page_link("pages/1_Resume_Builder.py", label="Go to Resume Builder ->", icon="📄")

    st.markdown("#### Upload your existing resume")
    st.caption("Upload a Word, PDF, or image file and we'll parse it automatically.")
    uploaded = st.file_uploader(
        "Upload resume",
        type=["pdf", "docx", "jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="po_upload",
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
                st.success("Resume parsed! Refreshing...")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not parse resume: {exc}")
    st.stop()

st.success(f"Resume found: **{resume_data.get('target_title', '')}** - {resume_data.get('name', '')}")

saved_opt = store.load_profile_optimizer()

tab_naukri, tab_linkedin = st.tabs(["Naukri Profile", "LinkedIn Profile"])

with tab_naukri:
    st.markdown("### Naukri Profile Optimization")

    naukri_data = saved_opt.get("naukri", {})

    if not naukri_data:
        if st.button("Generate Naukri Profile Content", type="primary"):
            with st.spinner("CareerOS is generating your Naukri profile content..."):
                try:
                    naukri_data = generate_naukri_profile(resume_data, ANTHROPIC_API_KEY)
                    saved_opt["naukri"] = naukri_data
                    store.save_profile_optimizer(saved_opt)
                except Exception as exc:
                    st.error(f"Error: {exc}")
                    st.stop()
            st.rerun()
    else:
        if st.button("Regenerate Naukri Content"):
            with st.spinner("Regenerating..."):
                try:
                    naukri_data = generate_naukri_profile(resume_data, ANTHROPIC_API_KEY)
                    saved_opt["naukri"] = naukri_data
                    store.save_profile_optimizer(saved_opt)
                except Exception as exc:
                    st.error(f"Error: {exc}")
            st.rerun()

    if naukri_data:
        st.divider()

        st.markdown("#### Profile Headline")
        st.info("Copy this into Naukri -> Edit Profile -> Headline (max 250 chars)")
        st.text_area("headline", value=naukri_data.get("headline", ""), height=80, disabled=True, label_visibility="collapsed")

        st.markdown("#### Profile Summary")
        st.info("Copy into Naukri -> Edit Profile -> Profile Summary (max 500 chars)")
        st.text_area("profile_summary", value=naukri_data.get("profile_summary", ""), height=150, disabled=True, label_visibility="collapsed")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Skills to ADD")
            skills_add = naukri_data.get("skills_add", [])
            st.info(f"{len(skills_add)} skills - add these on Naukri profile")
            for skill in skills_add:
                st.markdown(f"- {skill}")

        with col2:
            st.markdown("#### Top 5 Skills (set these first)")
            for skill in naukri_data.get("top_5_skills", []):
                st.markdown(f"- {skill}")
            st.markdown("#### Skills to REMOVE")
            for skill in naukri_data.get("skills_remove", []):
                st.markdown(f"- {skill}")

        st.divider()
        st.markdown("#### Employment Descriptions")
        st.info("Copy each into the respective job's description field on Naukri")
        for emp in naukri_data.get("employment_descriptions", []):
            with st.expander(f"{emp.get('designation', '')} @ {emp.get('company', '')}"):
                st.text_area(
                    f"emp_{emp.get('company', '')}",
                    value=emp.get("description", ""),
                    height=200,
                    disabled=True,
                    label_visibility="collapsed",
                )

        st.divider()
        st.markdown("#### Profile Completeness Checklist")
        for tip in naukri_data.get("profile_completeness_tips", []):
            st.markdown(f"- {tip}")

        st.divider()
        st.markdown("#### Automatic Naukri Update")
        if not profile.get("naukri_email") or not profile.get("naukri_pass_enc"):
            st.warning("Save your Naukri credentials on the Setup page first. Then come back here to download the updater.")
            st.page_link("pages/0_Setup.py", label="Go to Setup ->", icon="⚙️")
        else:
            st.caption("CareerOS can now update the main Naukri profile sections from your PC using the content above.")
            updater_zip = _build_naukri_updater_zip(email, profile, prefs, resume_saved, naukri_data)
            st.download_button(
                label="⬇️ Download Naukri Profile Updater",
                data=updater_zip,
                file_name="careeros_naukri_profile_updater.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary",
            )
            st.info("After download: unzip -> open PowerShell in that folder -> run `python update_profile.py`.")

with tab_linkedin:
    st.markdown("### LinkedIn Profile Optimization")
    st.markdown("*Target: resumeworked.com score **75+***")

    linkedin_data = saved_opt.get("linkedin", {})

    if not linkedin_data:
        if st.button("Generate LinkedIn Profile Content", type="primary"):
            with st.spinner("CareerOS is generating your LinkedIn profile content... (45-60 seconds)"):
                try:
                    linkedin_data = generate_linkedin_profile(resume_data, ANTHROPIC_API_KEY)
                    saved_opt["linkedin"] = linkedin_data
                    store.save_profile_optimizer(saved_opt)
                except Exception as exc:
                    st.error(f"Error: {exc}")
                    st.stop()
            st.rerun()
    else:
        if st.button("Regenerate LinkedIn Content"):
            with st.spinner("Regenerating..."):
                try:
                    linkedin_data = generate_linkedin_profile(resume_data, ANTHROPIC_API_KEY)
                    saved_opt["linkedin"] = linkedin_data
                    store.save_profile_optimizer(saved_opt)
                except Exception as exc:
                    st.error(f"Error: {exc}")
            st.rerun()

    if linkedin_data:
        st.divider()

        score = linkedin_data.get("estimated_resumeworded_score", "75-80")
        st.success(f"Estimated resumeworked.com score after implementing: **{score}**")

        st.markdown("#### Implementation Checklist")
        for item in linkedin_data.get("resumeworked_checklist", []):
            label = item.get("item", "")
            action = item.get("action", "")
            st.markdown(f"- [ ] **{label}** - _{action}_")

        st.divider()
        st.markdown("#### Headline Options (pick one)")
        for i, headline in enumerate(linkedin_data.get("headline_options", []), 1):
            st.markdown(f"**Option {i}:**")
            st.text_area(f"li_headline_{i}", value=headline, height=80, disabled=True, label_visibility="collapsed")

        st.markdown("#### About Section")
        st.info("Copy this into LinkedIn -> Edit Profile -> About (under your name)")
        st.text_area("li_about", value=linkedin_data.get("about_section", ""), height=220, disabled=True, label_visibility="collapsed")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Top 5 Skills (pin these)")
            for skill in linkedin_data.get("top_5_skills", []):
                st.markdown(f"- {skill}")
        with col2:
            st.markdown("#### All 50 Skills to Add")
            all_skills = linkedin_data.get("all_skills_50", [])
            st.caption(f"{len(all_skills)} skills")
            st.write(", ".join(all_skills))

        st.divider()
        st.markdown("#### Experience Bullets")
        for exp in linkedin_data.get("experience_bullets", []):
            with st.expander(f"{exp.get('title', '')} @ {exp.get('company', '')}"):
                for bullet in exp.get("bullets", []):
                    st.markdown(f"- {bullet}")

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("#### Custom URL")
            st.text_area("li_url", value=f"linkedin.com/in/{linkedin_data.get('custom_url_suggestion', '')}", height=70, disabled=True, label_visibility="collapsed")
        with col4:
            st.markdown("#### Featured Section")
            st.write(linkedin_data.get("featured_section_idea", ""))

        st.divider()
        st.markdown("#### Recommendation Request Template")
        st.info("Send this to 2 colleagues or managers on LinkedIn")
        st.text_area("li_rec_req", value=linkedin_data.get("recommendation_request_template", ""), height=200, disabled=True, label_visibility="collapsed")