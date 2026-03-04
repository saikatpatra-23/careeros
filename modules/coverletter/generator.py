# -*- coding: utf-8 -*-
"""
Cover Letter Generator — CareerOS
Generates tailored cover letters optimised for Indian job market email applications.
"""
from __future__ import annotations
import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

SYSTEM_PROMPT = """You are an expert career coach with 15 years of experience helping Indian
professionals land jobs at top companies. You write cover letters that actually get read.

WHAT WORKS IN INDIA:
- Recruiters at Indian companies get 200-500 applications per role. Most cover letters are skipped.
- A cover letter that gets read is SHORT (250-350 words), has a strong opening hook, and leads
  with relevant achievements — not your life story.
- Never start with "I am writing to apply for..." — it gets ignored immediately.
- The subject line is as important as the letter itself for email applications.
- Show you understand the company's world, not just that you want a job.
- Quantified achievements > generic claims (always).

FORMAT:
Subject line → Greeting → Hook (2 sentences) → Your value (2-3 bullets with numbers) →
Why this company/role (1 para, specific) → Ask + close

OUTPUT: Single valid JSON object only. No markdown. No explanation outside JSON."""

GENERATOR_PROMPT = """Write a cover letter for this application.

CANDIDATE PROFILE:
{resume_json}

JOB DESCRIPTION:
{jd}

TONE: {tone}
(Professional = formal but warm | Confident = assertive, achievement-led | Concise = ultra-short, punchy)

Return a JSON object with EXACTLY these keys:
{{
  "subject_line": "<email subject — format: Role Name — X yrs Domain experience | Ref: Company>",
  "cover_letter": "<full cover letter text — plain text, no markdown, use newlines for paragraphs>",
  "word_count": <integer>,
  "opening_hook": "<restate just the first 2 sentences — so user can see the hook clearly>",
  "tailoring_notes": "<1-2 sentences: what specific JD signals you used to tailor this — helps user understand the logic>"
}}

Rules for the cover letter:
- 250-350 words max
- DO NOT start with "I am writing to apply"
- Open with a specific insight about the company/role challenge or a strong achievement statement
- Include 2-3 concrete achievements with numbers from the candidate's experience (pick the most relevant to this JD)
- Name the company specifically at least twice
- Close with a specific ask: "I'd welcome a 20-minute call to discuss how I can contribute to [specific thing]."
- If no JD is provided, write a strong general letter for the candidate's target role
- Tone must match the "{tone}" instruction
- Use plain text only (no bullet symbols, no bold, no markdown)"""


def generate_cover_letter(
    resume_data: dict,
    jd: str = "",
    tone: str = "Professional",
    api_key: str = "",
) -> dict:
    """Generate a tailored cover letter. Returns structured dict."""
    client = anthropic.Anthropic(api_key=api_key or ANTHROPIC_API_KEY)

    # Trim resume to most useful fields
    resume_slim = {
        "name":          resume_data.get("name", ""),
        "target_title":  resume_data.get("target_title", ""),
        "summary":       resume_data.get("summary", ""),
        "experience":    resume_data.get("experience", [])[:4],
        "skills":        resume_data.get("skills", {}),
        "ats_keywords":  resume_data.get("ats_keywords", [])[:15],
        "education":     resume_data.get("education", []),
    }

    prompt = GENERATOR_PROMPT.format(
        resume_json=json.dumps(resume_slim, indent=2, ensure_ascii=False)[:4000],
        jd=jd[:3000] if jd.strip() else "No specific JD provided — write for target role.",
        tone=tone,
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw     = response.content[0].text
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start   = cleaned.find("{")
    end     = cleaned.rfind("}") + 1
    if start == -1:
        raise ValueError("No JSON returned from cover letter generator")
    return json.loads(cleaned[start:end])
