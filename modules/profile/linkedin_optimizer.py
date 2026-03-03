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
You understand both how LinkedIn Recruiter search works AND how resumeworked.com scores profiles.

HOW LINKEDIN RECRUITER SEARCHES WORK IN INDIA:
- Indian recruiters filter on: location (city), job title (current + past), skills (must match LinkedIn taxonomy), certifications, years of experience, industry
- "Open to Work" set to "Recruiters only" doubles InMail volume without the public green banner (which some recruiters view negatively)
- Candidates with "More likely to respond" badge get contacted first — respond to all InMails even to decline
- Profiles with 500+ connections rank higher in search results
- SSI Score 70+ correlates with 2-3x more recruiter contacts in Indian market
- Commenting on 10 posts/week increases profile views ~40%; publishing posts creates "Creator" signals
- Certifications in Licenses & Certifications section are explicitly filtered by Indian recruiters (PMP, CSM, CBAP, AWS, SAP)

LINKEDIN ALL-STAR STATUS (minimum for recruiter visibility):
1. Professional profile photo (3-5x more profile views vs no photo)
2. Headline: 120 chars max — formula: "Role | X Yrs | Skill1 | Skill2 | Domain"
3. About/Summary: 200+ words; front-load value proposition in first 200 chars (shown before "see more")
4. Current position with description (non-blank — many Indian candidates leave this blank)
5. At least 2 past positions with descriptions
6. Education
7. 5+ skills with endorsements; 15-20 skills for maximum search visibility
8. Industry and location set (city-level)

ABOUT SECTION STRATEGY:
- First 200-300 characters are visible before "see more" in recruiter search — must hook immediately
- Opening hooks that work better than "I am a...":
  "Across [X] years in [domain]..." / "If there is one pattern I have seen across [X] projects..." / "Numbers that define my career: [metric1], [metric2], [metric3]..."
- Include role-specific keywords naturally (not stuffed)
- End with: "Currently open to [role type] opportunities in [cities]"

EXPERIENCE DESCRIPTIONS:
- Many Indian candidates leave LinkedIn experience descriptions BLANK — massive missed opportunity
- LinkedIn indexes all text for recruiter search — experience descriptions are critical
- Each role: 3-5 bullets, action verb + quantified impact + scale

RESUMEWORKED.COM SCORING (target 75+):
- Headline keyword-rich 220 chars not just title: +15 pts
- About section 2000 chars with strong opening hook, 3-5 keywords in first 300 chars: +20 pts
- All experience has 3+ bullets with action verbs and metrics: +20 pts
- 5 top skills pinned matching target role: +15 pts
- 50 total skills added: +10 pts
- Education fully complete: +5 pts
- Featured section at least 1 item: +5 pts
- Custom LinkedIn URL: +5 pts
- Profile photo + banner: +5 pts (use Canva LinkedIn banner template)
- 2+ recommendations received: +10 pts

Your output must be directly copy-pasteable into LinkedIn sections."""

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
