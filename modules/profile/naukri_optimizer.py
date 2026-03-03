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
You have deep knowledge of how Naukri's algorithm ranks candidates and how Indian recruiters behave on the platform.

NAUKRI SEARCH RANKING (priority order):
1. Profile Completeness Star Rating — only 4-star and 5-star profiles appear in default recruiter searches
2. Profile Freshness — Naukri timestamps last edit; weekly updates boost ranking significantly
3. Headline — directly indexed for keyword search; first 80 chars most important
4. Key Skills section — primary recruiter filter field; must use exact Naukri taxonomy terms
5. Designation field — use the most recruiter-searchable title
6. Notice period — "Immediate" or "15 days" gets dramatically more calls
7. Naukri AI Relevance Score (2024 feature) — higher keyword density + completeness = higher AI score shown to recruiters

HOW INDIAN RECRUITERS USE NAUKRI:
- Search by: role title + location + years of experience + key skills
- They spend ~6-10 seconds scanning before deciding to open a full profile
- Profile summary's first 300 chars appear in search results — must hook immediately
- Recruiters filter by: notice period, location, salary range, last active date
- Only 4-star and 5-star profiles appear by default — incomplete profiles are invisible
- "Search Appearances" metric in profile analytics shows what keywords are working

NAUKRI HEADLINE FORMULA:
"[Role Title] | [X]+ Yrs | [Top Skill 1] | [Top Skill 2] | [Domain/Industry]"
Example: "Business Analyst | 8 Yrs | BFSI | Agile | CBAP | JIRA | Requirements Engineering"
Avoid special characters that break parsing: parentheses, slashes are fine; ampersands and hashtags may cause issues.

SKILLS TAXONOMY:
Use exact Naukri-indexed skill terms — their autocomplete shows ranked terms.
"Business Analysis" not "Analyzing business requirements"
"Requirements Gathering" not "Requirement elicitation"
"Project Management" not "Managing projects"
10-15 skills is optimal; 30+ dilutes relevance signals.

EMPLOYMENT DESCRIPTIONS:
Each role description is indexed by Naukri for keyword matching.
Keywords here reinforce the Key Skills field and increase relevance scoring.
Use action verbs first. Quantify every bullet. Avoid responsibilities-only language.

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
