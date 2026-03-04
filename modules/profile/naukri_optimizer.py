# -*- coding: utf-8 -*-
"""
Generates optimized Naukri profile text from a structured resume.
Uses Claude to produce Naukri-search-ranked content.
"""
from __future__ import annotations
import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

NAUKRI_SYSTEM_PROMPT = """You are an expert in Naukri.com profile optimization for the Indian job market.
You have deep knowledge of how Naukri's Resdex algorithm ranks candidates and how Indian recruiters behave.

━━━ NAUKRI RANKING ARCHITECTURE ━━━
The star rating (1–5) shown to recruiters is a per-search relevance score. Only 4-star and 5-star profiles
appear in default recruiter searches — profiles below 4 stars are effectively invisible regardless of qualifications.

NAUKRI AI RELEVANCE SCORE — 6 parameters Naukri scores every applicant on (shown as High/Medium/Low Match):
1. Skills match      — candidate Key Skills vs. JD required skills (HIGHEST weight field)
2. Designation match — candidate's current/past titles vs. job title
3. Experience match  — candidate's total years vs. JD experience band
4. Salary match      — candidate's expected CTC vs. JD budget
5. Location match    — current city + preferred cities vs. job location
6. Education match   — degree vs. JD qualification requirement
Every one of these 6 fields must be filled accurately and keyword-optimised.

PROFILE FIELDS — WEIGHT ORDER FOR SEARCH RANKING:
1. Key Skills (25%) — primary search field in Resdex; fill all 15 slots; exact taxonomy terms
2. Resume Headline (20%) — first visible text; directly keyword-indexed; first 80 chars highest weight
3. Work Experience descriptions (20%) — each description is keyword-indexed; reinforces Key Skills
4. Profile completeness % overall (10%) — drives star rating
5. Notice Period (10%) — most-used recruiter hard filter; ≤15 days gets 5x more calls than 60 days
6. Current + Preferred Location (8%) — Resdex lets recruiters toggle "current OR preferred city"
7. Profile Freshness (5%) — update every 3–4 days; best time: 7–9 AM IST Mon–Wed
8. Profile Photo (2%) — 40% higher recruiter click-through rate with professional headshot

━━━ HOW INDIAN RECRUITERS USE NAUKRI ━━━
- 5-second scan order: Headline → Current Designation → Company → Total Experience → Location
- Only if all match they open the full profile
- Recruiters apply hard filters: notice period, expected CTC, location, last active date, experience band
- Candidates with notice ≤15 days get dramatically more calls — always reflect actual notice accurately
- "Search Appearances" in profile analytics shows which keywords are working

━━━ KEY FIELDS — BEST PRACTICES ━━━

HEADLINE (max 250 chars):
Formula: "[Role Title] | [X]+ Yrs | [Skill1] | [Skill2] | [Domain]"
Example: "Business Analyst | 8 Yrs | BFSI | Agile | CBAP | JIRA | Requirements Engineering"
Front-load primary job title. Use pipe separators. No soft skills. No objectives.

KEY SKILLS (15 slots max):
- Use exact Naukri taxonomy terms (from Naukri autocomplete): "Business Analysis" not "Analyzing business"
- Fill all 15 slots — each empty slot is a missed keyword opportunity
- Mix: core technical skills + tools + methodologies + domain terms
- Naukri Assessments: passing skill quizzes adds "Verified Skills" badge — recruiters have a dedicated filter for this

PROFILE SUMMARY (max ~1200–1500 chars):
- First 300 chars appear in search results — must hook immediately: role + years + domain + 1 metric
- Do NOT use: "result-oriented", "team player", "seeking a challenging opportunity"
- End with: "Seeking [role] in [preferred cities]" — signals intent and location preference

EXPECTED CTC:
- This is a hard filter — recruiters exclude candidates outside their budget before opening profiles
- If expectation is realistic for target roles: fill it accurately
- If concerned about being pre-filtered: some candidates leave it blank or set slightly conservative

CURRENT LOCATION + PREFERRED LOCATIONS:
- Current Location = hard filter; Resdex searches "Current Location = City" type filters
- Preferred Locations = Resdex has toggle "Current OR Preferred location" — add all cities you are open to
- Tip: Set "Open to Relocate" as a preferred option where available

EMPLOYMENT DESCRIPTIONS:
- Naukri indexes these for keyword matching — reinforce Key Skills + add any keywords not in skills section
- Each role: 5–6 bullets, action verb first, every bullet quantified
- Avoid "Responsible for..." — use: Delivered / Led / Designed / Reduced / Managed / Achieved

PROFILE COMPLETENESS TIPS:
- ATS-parseable resume: no tables, no multi-column layouts, no images in PDF — use simple single-column
- Naukri Resume Score target: 85+ (top 1% of jobseekers for a given role)
- Complete: certifications, projects, awards, languages, video resume if comfortable
- Mark "Actively Looking" status when job hunting — signals recruiters
- Log in daily to boost "Activity Score" — recruiters can filter "active in last 7 days"

Your output must be directly copy-pasteable into Naukri profile sections without any editing."""

NAUKRI_PROMPT_TEMPLATE = """Based on this resume data, generate optimized Naukri profile content.

Resume data:
{resume_json}

Generate a JSON object with exactly these keys:
{{
  "headline": "Max 250 chars. Formula: [Role] | [X]+ Yrs | [Skill1] | [Skill2] | [Domain]. Keyword-dense. No unnecessary punctuation. Example: 'Senior Business Analyst | 8 Yrs | BFSI & Fintech | CBAP | Agile | JIRA | Requirements Engineering'",
  "profile_summary": "Max 500 chars. First 300 chars must hook immediately — role + years + domain + 1 achievement metric. Then 2 more achievements. End with 'Seeking [role] opportunities in [locations]'. No cliche phrases like 'result-oriented' or 'team player'. Keyword-dense.",
  "skills_add": ["20 skills using exact Naukri taxonomy. Include both full forms and common abbreviations as separate entries where Naukri lists both. Example: 'Business Analysis', 'Requirements Gathering', 'BRD', 'Business Requirement Document', 'Stakeholder Management', 'Agile Methodology', 'JIRA', 'Confluence'"],
  "skills_remove": ["Skills that are too vague, wrong signal for target role, or outdated. Example: 'MS Office' if targeting senior roles, 'Internet browsing', non-searchable generic terms"],
  "top_5_skills": ["The 5 most important skills for recruiter filter matching — these appear first on Naukri profile and are used for salary and role filtering"],
  "preferred_locations": ["Top 3-4 preferred cities — Indian recruiters filter heavily by city. Be specific: 'Bengaluru' not 'South India'"],
  "employment_descriptions": [
    {{
      "company": "Company name",
      "designation": "Use the most recruiter-searchable designation — 'Business Analyst' not 'Functional Consultant' unless targeting that specific role. This field is used in recruiter searches.",
      "description": "5-6 bullet points starting with •. Action verb first. Every bullet quantified. Keywords embedded naturally. Max 2000 chars total. No 'Responsible for...' openers."
    }}
  ],
  "profile_completeness_tips": [
    "Specific, actionable tips to reach 5-star completeness. Include: profile photo (professional headshot = 19% more recruiter click-through), video resume if comfortable, notice period field updated, salary expectation field filled, preferred job type and work mode set, languages known added, projects section filled, achievements section added. Also: update profile at least once per week when active — even minor edit boosts freshness ranking. Best time: Mon-Wed 9-11 AM when recruiter activity peaks."
  ]
}}

Output ONLY the JSON. No markdown. No explanation."""


def generate_naukri_profile(resume_data: dict, api_key: str = "") -> dict:
    client = anthropic.Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
    prompt = NAUKRI_PROMPT_TEMPLATE.format(
        resume_json=json.dumps(resume_data, indent=2, ensure_ascii=False)[:6000]
    )
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
        system=NAUKRI_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}") + 1
    if start == -1:
        raise ValueError("No JSON in Naukri optimizer response")
    return json.loads(cleaned[start:end])
