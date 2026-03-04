# -*- coding: utf-8 -*-
"""
ATS Score Checker — CareerOS
Analyses a candidate's resume against a specific JD using Claude.
Returns match score, keyword gaps, Naukri parameter breakdown, and verdict.
"""
from __future__ import annotations
import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

SYSTEM_PROMPT = """You are an expert ATS analyst and senior Indian recruiter with 12+ years of experience.
You understand exactly how Naukri's AI Relevance Score works, how RChilli parses resumes,
and how Indian HRs evaluate candidates in the first 6 seconds.

Your job: given a candidate's resume and a job description, produce an honest, precise analysis.

━━━ NAUKRI AI RELEVANCE SCORE — 6 parameters ━━━
Naukri scores every applicant on these 6 dimensions (shown to recruiters as High/Medium/Low Match):
1. Skills match      — candidate's skills vs. JD required skills
2. Designation match — candidate's title(s) vs. job title
3. Experience match  — candidate's years vs. JD experience band
4. Salary match      — candidate's expected CTC vs. JD budget range
5. Location match    — candidate's city vs. job location
6. Education match   — candidate's degree vs. JD qualification

━━━ HOW INDIAN HRs SCAN ━━━
First 6 seconds: Headline → Designation → Company → Years → Location
If any of these mismatches, they stop reading.
Keywords in headline and skills section outweigh keywords buried in descriptions.

━━━ YOUR OUTPUT FORMAT ━━━
Always output a single valid JSON object. No markdown. No explanation outside JSON."""

CHECKER_PROMPT = """Analyse this resume against the job description and return a detailed ATS analysis.

RESUME DATA:
{resume_json}

JOB DESCRIPTION:
{jd}

Return a JSON object with EXACTLY these keys:

{{
  "overall_score": <integer 0-100>,
  "verdict": "<one of: Strong Apply | Apply with Tweaks | Weak Match — Tailor First | Skip This Job>",
  "verdict_reason": "<one sentence explaining the verdict — be honest, not encouraging>",

  "naukri_parameters": {{
    "skills":       {{"score": <0-100>, "comment": "<specific gap or strength in 10 words>"}},
    "designation":  {{"score": <0-100>, "comment": "<specific gap or strength in 10 words>"}},
    "experience":   {{"score": <0-100>, "comment": "<specific gap or strength in 10 words>"}},
    "salary":       {{"score": <0-100>, "comment": "<specific gap or strength in 10 words>"}},
    "location":     {{"score": <0-100>, "comment": "<specific gap or strength in 10 words>"}},
    "education":    {{"score": <0-100>, "comment": "<specific gap or strength in 10 words>"}}
  }},

  "keywords_found": ["keyword1", "keyword2"],
  "keywords_missing": ["keyword1", "keyword2"],

  "recommendations": [
    {{
      "priority": "High",
      "action": "<specific, actionable change to make — not generic advice>",
      "where": "<Resume headline / Skills section / Experience bullet / Profile summary>"
    }},
    {{
      "priority": "Medium",
      "action": "<specific, actionable change>",
      "where": "<where to make it>"
    }},
    {{
      "priority": "Low",
      "action": "<specific, actionable change>",
      "where": "<where to make it>"
    }}
  ],

  "resume_headline_suggestion": "<optimised Naukri headline for THIS specific job — max 200 chars>",

  "one_liner_gap": "<The single biggest reason this resume might get rejected — max 15 words>"
}}

Scoring guide:
- overall_score 80-100: Strong match, high callback probability
- overall_score 60-79: Decent match, apply with minor tweaks
- overall_score 40-59: Weak match, needs tailoring before applying
- overall_score 0-39: Poor fit, not worth applying without significant changes

Be honest. Indian HRs are brutal — a 65 that feels like 80 helps no one."""


def check_ats(resume_data: dict, jd: str, api_key: str = "") -> dict:
    """Run ATS analysis and return structured result dict."""
    client = anthropic.Anthropic(api_key=api_key or ANTHROPIC_API_KEY)

    prompt = CHECKER_PROMPT.format(
        resume_json=json.dumps(resume_data, indent=2, ensure_ascii=False)[:5000],
        jd=jd[:4000],
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start == -1:
        raise ValueError("No JSON returned from ATS checker")
    return json.loads(cleaned[start:end])
