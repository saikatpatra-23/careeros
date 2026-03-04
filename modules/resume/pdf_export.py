# -*- coding: utf-8 -*-
"""
ATS-friendly PDF resume exporter using reportlab.
Mirrors word_export.py layout: single column, Helvetica, no images.
"""
from __future__ import annotations

import io
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


# Colours
DARK  = colors.HexColor("#1F273A")
BLUE  = colors.HexColor("#1B4F9C")
GREY  = colors.HexColor("#555555")


def _styles() -> dict:
    return {
        "name": ParagraphStyle(
            "name",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=DARK,
            alignment=1,  # centre
            spaceAfter=4,
        ),
        "target": ParagraphStyle(
            "target",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=BLUE,
            alignment=1,
            spaceAfter=4,
        ),
        "contact": ParagraphStyle(
            "contact",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=GREY,
            alignment=1,
            spaceAfter=6,
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=DARK,
            spaceAfter=4,
        ),
        "bold_body": ParagraphStyle(
            "bold_body",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=DARK,
            spaceAfter=2,
        ),
        "blue_body": ParagraphStyle(
            "blue_body",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=BLUE,
            spaceAfter=2,
        ),
        "grey_small": ParagraphStyle(
            "grey_small",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=GREY,
            spaceAfter=3,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=DARK,
            leftIndent=14,
            firstLineIndent=0,
            spaceAfter=2,
            bulletIndent=0,
        ),
    }


def _hr() -> HRFlowable:
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.HexColor("#CCCCCC"),
        spaceAfter=4,
        spaceBefore=2,
    )


def export_to_pdf(resume_data: dict) -> bytes:
    """
    Build an ATS-friendly PDF from CareerOS resume JSON.
    Returns bytes suitable for st.download_button().
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    S = _styles()
    story = []

    # == HEADER ================================================================
    story.append(Paragraph(resume_data.get("name", "").upper(), S["name"]))
    story.append(Paragraph(resume_data.get("target_title", ""), S["target"]))

    contact_parts = []
    for field in ("phone", "email", "location", "linkedin"):
        val = resume_data.get(field, "")
        if val:
            contact_parts.append(val)
    story.append(Paragraph("  |  ".join(contact_parts), S["contact"]))
    story.append(_hr())

    # == PROFESSIONAL SUMMARY ==================================================
    summary = resume_data.get("summary", "")
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", S["section"]))
        story.append(_hr())
        story.append(Paragraph(summary, S["body"]))

    # == KEY SKILLS ============================================================
    skills = resume_data.get("skills", {})
    if skills:
        all_skills = []
        for skill_list in skills.values():
            if skill_list:
                all_skills.extend(skill_list)
        if all_skills:
            story.append(Paragraph("KEY SKILLS", S["section"]))
            story.append(_hr())
            mid = (len(all_skills) + 1) // 2
            col1 = all_skills[:mid]
            col2 = all_skills[mid:]
            for i in range(max(len(col1), len(col2))):
                s1 = f"\u2022 {col1[i]}" if i < len(col1) else ""
                s2 = f"\u2022 {col2[i]}" if i < len(col2) else ""
                row = f"{s1:<40}{s2}"
                story.append(Paragraph(row, S["body"]))

    # == WORK EXPERIENCE =======================================================
    experience = resume_data.get("experience", [])
    if experience:
        story.append(Paragraph("WORK EXPERIENCE", S["section"]))
        story.append(_hr())
        for job in experience:
            period   = job.get("period", "")
            location = job.get("location", "")
            right    = f"  |  {period}" + (f"  |  {location}" if location else "")
            company_line = f"<b>{job.get('company', '')}</b><font color='#555555' size='10'>{right}</font>"
            story.append(Paragraph(company_line, S["body"]))
            story.append(Paragraph(job.get("title", ""), S["blue_body"]))
            for bullet in job.get("bullets", []):
                story.append(Paragraph(f"\u2022 {bullet}", S["bullet"]))
            story.append(Spacer(1, 4))

    # == EDUCATION =============================================================
    education = resume_data.get("education", [])
    if education:
        story.append(Paragraph("EDUCATION", S["section"]))
        story.append(_hr())
        for edu in education:
            story.append(Paragraph(edu.get("degree", ""), S["bold_body"]))
            sub_parts = [p for p in [
                edu.get("institution", ""),
                edu.get("year", ""),
                edu.get("grade", ""),
            ] if p]
            story.append(Paragraph("  |  ".join(sub_parts), S["grey_small"]))

    # == CERTIFICATIONS ========================================================
    certs = resume_data.get("certifications", [])
    if certs:
        story.append(Paragraph("CERTIFICATIONS", S["section"]))
        story.append(_hr())
        for cert in certs:
            story.append(Paragraph(f"\u2022 {cert}", S["bullet"]))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def get_pdf_filename(resume_data: dict) -> str:
    name = resume_data.get("name", "Resume").replace(" ", "_")
    role = resume_data.get("target_title", "").replace(" ", "_").replace("/", "-")
    return f"{name}_{role}_Resume.pdf"
