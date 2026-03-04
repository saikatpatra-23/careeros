# -*- coding: utf-8 -*-
"""
Resume file parser — extracts text from DOCX / PDF / image files
and converts it into CareerOS resume JSON via Claude.
"""
from __future__ import annotations

import base64
import io
import json
import re

import anthropic


# == Text extraction ===========================================================

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a Word (.docx) file."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file using pdfplumber."""
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
    return "\n\n".join(text_parts)


def extract_text_from_image(file_bytes: bytes, api_key: str) -> str:
    """Extract text from an image (JPG/PNG) resume using Claude vision."""
    client = anthropic.Anthropic(api_key=api_key)
    b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "This is a resume image. Extract ALL text exactly as it appears, "
                        "preserving the structure (sections, bullet points, dates). "
                        "Output plain text only — no commentary."
                    ),
                },
            ],
        }],
    )
    return response.content[0].text


# == JSON parsing ==============================================================

_PARSE_PROMPT = """You are a resume parser. Given the raw text of a resume, extract the information and return a JSON object matching EXACTLY this schema (no extra keys, no markdown fences):

{
  "name": "Full Name",
  "target_title": "Current or most recent job title",
  "phone": "",
  "email": "",
  "location": "City, State",
  "linkedin": "",
  "summary": "A 3-4 sentence professional summary",
  "skills": {
    "Technical Skills": [],
    "Tools & Platforms": [],
    "Domain Expertise": [],
    "Soft Skills": []
  },
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "period": "Month Year – Month Year",
      "location": "",
      "bullets": ["Achievement 1", "Achievement 2"]
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "College/University",
      "year": "Year",
      "grade": ""
    }
  ],
  "certifications": [],
  "ats_keywords": [],
  "role_suggestion": {},
  "domain_family": ""
}

Rules:
- Fill every field from the resume text. Leave as empty string/list if not found.
- For skills, categorise them sensibly into the 4 buckets.
- For ats_keywords, extract 10-20 strong keywords from the resume.
- For domain_family, infer the broad domain (e.g. "Software Engineering", "Sales", "Finance").
- Return ONLY the JSON object — no explanation, no markdown.

Resume text:
"""


def parse_resume_to_json(text: str, api_key: str) -> dict:
    """
    Send extracted resume text to Claude and return structured CareerOS resume JSON.
    """
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": _PARSE_PROMPT + text,
        }],
    )
    raw = response.content[0].text.strip()
    # Strip accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)
