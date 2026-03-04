# -*- coding: utf-8 -*-
"""
Generates optimized LinkedIn profile content targeting resumeworded.com score 75+.
"""
from __future__ import annotations
import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

LINKEDIN_SYSTEM_PROMPT = """You are an expert in LinkedIn profile optimization for the Indian job market.
You understand how LinkedIn Recruiter search works, how LinkedIn's algorithm ranks candidates,
and how resumeworked.com scores profiles.

━━━ LINKEDIN ALL-STAR STATUS (required for recruiter visibility) ━━━
All-Star profiles are 40x more likely to appear in recruiter search results.
Exact requirements — ALL 8 must be met:
1. Profile photo (professional headshot — 21x more profile views vs. no photo)
2. Headline (custom — not just default job title)
3. Location + Industry (both must be set)
4. Current position with description (non-blank)
5. At least 2 past positions with descriptions
6. Education (at least 1 entry)
7. At least 5 skills listed
8. At least 50 connections

━━━ HOW LINKEDIN RECRUITER SEARCHES IN INDIA ━━━
LinkedIn Recruiter has 40+ advanced filters. Most-used by Indian tech/management recruiters:
Primary: Keywords (Boolean: AND/OR/NOT), Current job title, Current company, Location, Years of experience, Industry
Secondary: Past company, School, Skills, Open to Work spotlight, Certifications

SPOTLIGHTS LinkedIn surfaces to recruiters:
- "Open to Work" candidates (must enable this feature fully)
- "Likely to respond" — candidates with high engagement rate
- "Engaged with your company's content"

KEY INSIGHT: Every profile field maps directly to a recruiter filter. Unfilled field = invisible in that filter dimension.

━━━ FIELD-BY-FIELD OPTIMIZATION ━━━

HEADLINE (max 220 chars desktop; first 60 chars carry highest algorithmic weight):
Formula: "[Target Role] | [Core Skill] | [Skill2] | [Domain/Industry] | [Years or Level]"
Front-load primary job title in first 60 chars — this is highest-weight keyword field.
Example: "Product Manager | FinTech | B2B SaaS | 6 Years | Ex-Razorpay"
Add "Open to Work" or "Actively Looking" if comfortable — signals availability to human readers.

ABOUT SECTION (max 2,600 chars; first 300 chars visible before "See more"):
- Open with a hook in first 300 chars — NOT "I am a..." Try:
  "Across [X] years of [domain]..." / "[Metric1], [Metric2], [Metric3] — these numbers define my career..."
- Embed 8–12 keywords naturally in the body (LinkedIn NLP maps semantic variants)
- End with explicit CTA: "Currently seeking [role type] in [cities]. DM or email: [email]"
- Target 1,800–2,200 chars (meaningful content, not padding)

SKILLS SECTION (max 50 skills):
*** CRITICAL: TOP 3 PINNED SKILLS get 10x more algorithmic visibility than all other skills ***
- Pin the 3 skills that most exactly match your target role's core requirement
- List 30–50 total skills for maximum keyword coverage
- LinkedIn Skill Assessments: pass these to earn "Verified" badge — recruiters have a dedicated filter for verified skills
- Skills with 5+ endorsements rank higher in search for that skill — request endorsements strategically
- Use LinkedIn's taxonomy (from their skill autocomplete) — exact match scores higher than synonyms

EXPERIENCE SECTION:
- Title field per entry = high-weight keyword field — use canonical industry title, not internal company title
- Description: 3–5 bullets per role, action verb + metric + scale
  Example: "Reduced customer onboarding time by 40% by redesigning 3-step verification flow"
- SKILLS TAG per experience entry — explicitly link skill to role ("Skills: JIRA, Agile, Stakeholder Management")
  This tells LinkedIn's algorithm you used that skill at that company — strongest skill-role association signal
- Most recent 2 positions receive higher ranking weight — make these descriptions richest

OPEN TO WORK (enable "Recruiters only" — not the public green banner):
Fill ALL preference fields — these directly control which recruiter searches you appear in:
- Job titles: add 3–5 specific target titles (not just 1)
- Job types: Full-time, Contract (if open)
- Locations: add all target cities + "Remote" if applicable
- Start date: "Immediately" or "Within a month" gets priority

━━━ LINKEDIN RANKING FACTORS ━━━
- Connection count: 50 minimum for All-Star; 500+ for social proof signal and expanded 2nd-degree network
- SSI Score 70+ correlates with 2–3x more recruiter contacts
- Activity signals: commenting on 10 posts/week → ~40% more profile views
- Certifications section: PMP, CSM, CBAP, AWS, etc. are explicitly filtered by Indian recruiters

━━━ RESUMEWORKED.COM SCORING (target 75+) ━━━
- Headline keyword-rich, 220 chars, front-loaded: +15 pts
- About section 1,800+ chars, strong hook, 3–5 keywords in first 300 chars: +20 pts
- All experience: 3+ bullets with action verbs and metrics: +20 pts
- Top 5 skills pinned matching target role: +15 pts
- 50 total skills added: +10 pts
- Education fully complete: +5 pts
- Featured section (1+ items): +5 pts
- Custom LinkedIn URL: +5 pts
- Profile photo + banner: +5 pts
- 2+ recommendations received: +10 pts

Your output must be directly copy-pasteable into LinkedIn sections without editing."""

LINKEDIN_PROMPT = """Based on this resume data, generate a complete LinkedIn profile optimization package.

Resume data:
{resume_json}

Generate a JSON object with these exact keys:
{{
  "headline_options": [
    "Option 1 — keyword focused (220 chars max)",
    "Option 2 — achievement focused (220 chars max)",
    "Option 3 — role + domain focused (220 chars max)"
  ],
  "about_section": "Full About text. 1800-2000 chars. Start with a strong hook — NOT 'I am a...' Try: 'Across 5 years of...' or 'If there is one thing I have learned...' First person. Keywords in first 200 chars. End with what you are looking for.",
  "experience_bullets": [
    {{
      "company": "Company name",
      "title": "Job title",
      "bullets": ["Repositioned bullet 1", "Repositioned bullet 2", "Repositioned bullet 3"]
    }}
  ],
  "top_5_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
  "all_skills_50": ["Full list of 50 skills to add — mix of hard and soft skills relevant to target role"],
  "custom_url_suggestion": "firstname-lastname-role or similar clean URL",
  "featured_section_idea": "Suggest what to put in Featured — a post, article, project, or portfolio link",
  "recommendation_request_template": "Ready-to-send LinkedIn message asking a colleague/manager for a recommendation. Personalized, specific, not generic.",
  "resumeworded_checklist": [
    {{"item": "Headline keyword-rich (220 chars)", "done": false, "action": "Copy headline_options[0] above"}},
    {{"item": "About section 1800+ chars with hook", "done": false, "action": "Copy about_section above"}},
    {{"item": "All experience has 3+ bullets with metrics", "done": false, "action": "Copy experience_bullets above"}},
    {{"item": "Top 5 skills set", "done": false, "action": "Set top_5_skills in Skills section"}},
    {{"item": "50 total skills added", "done": false, "action": "Add all_skills_50 above"}},
    {{"item": "Custom LinkedIn URL set", "done": false, "action": "Set URL to: " }},
    {{"item": "Featured section has 1+ items", "done": false, "action": "Add featured_section_idea above"}},
    {{"item": "Education fully complete", "done": false, "action": "Check education section — add grade, activities"}},
    {{"item": "2+ recommendations received", "done": false, "action": "Send recommendation_request_template to 2 people"}},
    {{"item": "Profile photo + banner added", "done": false, "action": "Use professional headshot. Banner: use Canva, search LinkedIn banner templates."}}
  ],
  "estimated_resumeworded_score": "Estimated score after implementing all above (should be 75-85)"
}}

Output ONLY the JSON. No markdown. No explanation."""


def generate_linkedin_profile(resume_data: dict, api_key: str = "") -> dict:
    client = anthropic.Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
    prompt = LINKEDIN_PROMPT.format(
        resume_json=json.dumps(resume_data, indent=2, ensure_ascii=False)[:6000]
    )
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        system=LINKEDIN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}") + 1
    if start == -1:
        raise ValueError("No JSON in LinkedIn optimizer response")
    return json.loads(cleaned[start:end])
