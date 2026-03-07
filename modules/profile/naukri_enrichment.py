"""
Helpers for building Naukri profile context from resume data + targeted follow-up answers.
"""
from __future__ import annotations

from copy import deepcopy

CITY_OPTIONS = [
    "Bengaluru", "Pune", "Mumbai", "Navi Mumbai", "Thane", "Hyderabad",
    "Chennai", "Noida", "Gurgaon", "Delhi NCR", "Kolkata", "Ahmedabad",
    "Remote", "Open to relocate",
]

ROLE_OPTIONS = [
    "Technical Program Manager", "Program Manager", "Delivery Manager",
    "IT Project Manager", "Project Manager", "Product Manager",
    "Business Analyst", "Senior Business Analyst", "Implementation Manager",
    "Solution Consultant", "Transformation Manager",
]

INDUSTRY_OPTIONS = [
    "SaaS", "Enterprise IT", "Automotive", "Mobility", "Fintech", "BFSI",
    "Consulting", "Manufacturing", "E-commerce", "Healthcare Tech",
]

NOTICE_PERIOD_OPTIONS = [
    "Immediate", "15 days", "30 days", "45 days", "60 days", "90 days",
    "Serving notice period",
]

WORK_MODE_OPTIONS = ["Any", "Work from office", "Hybrid", "Remote"]


def _first_non_empty(*values, fallback=""):
    for value in values:
        if isinstance(value, list) and value:
            return value
        if value not in (None, "", []):
            return value
    return fallback


def get_naukri_followup_questions(resume_data: dict, profile: dict, prefs: dict, existing: dict | None = None) -> list[dict]:
    existing = existing or {}
    target_title = (resume_data.get("target_title") or "").strip()
    resume_location = (resume_data.get("location") or "").split(",")[0].strip()

    return [
        {
            "id": "target_roles",
            "label": "Target roles",
            "type": "multiselect",
            "options": ROLE_OPTIONS,
            "help": "Pick up to 3 recruiter-searchable titles. The first one becomes the primary Naukri headline anchor.",
            "default": _first_non_empty(existing.get("target_roles"), [target_title] if target_title else [], fallback=[]),
        },
        {
            "id": "preferred_locations",
            "label": "Preferred cities",
            "type": "multiselect",
            "options": CITY_OPTIONS,
            "help": "These cities influence both summary copy and preferred-location targeting for Naukri.",
            "default": _first_non_empty(
                existing.get("preferred_locations"),
                prefs.get("locations"),
                profile.get("preferred_locations"),
                [resume_location] if resume_location else [],
                fallback=[],
            ),
        },
        {
            "id": "notice_period",
            "label": "Notice period",
            "type": "select",
            "options": NOTICE_PERIOD_OPTIONS,
            "help": "Naukri recruiters filter heavily on this. Keep it accurate.",
            "default": _first_non_empty(existing.get("notice_period"), profile.get("notice_period"), fallback="30 days"),
        },
        {
            "id": "current_ctc_lpa",
            "label": "Current CTC (LPA)",
            "type": "number",
            "min": 0.0,
            "max": 100.0,
            "step": 0.5,
            "help": "Optional, but useful for generating realistic recruiter-facing positioning.",
            "default": float(existing.get("current_ctc_lpa") or profile.get("current_ctc_lpa") or 0.0),
        },
        {
            "id": "expected_ctc_lpa",
            "label": "Expected CTC (LPA)",
            "type": "number",
            "min": 0.0,
            "max": 100.0,
            "step": 0.5,
            "help": "Optional. Helps CareerOS tune summary wording and future job matching.",
            "default": float(existing.get("expected_ctc_lpa") or profile.get("expected_ctc_lpa") or 0.0),
        },
        {
            "id": "work_mode",
            "label": "Work mode",
            "type": "select",
            "options": WORK_MODE_OPTIONS,
            "help": "Used in profile recommendations and future Smart Apply targeting.",
            "default": _first_non_empty(existing.get("work_mode"), profile.get("work_mode"), fallback="Any"),
        },
        {
            "id": "target_industries",
            "label": "Target industries",
            "type": "multiselect",
            "options": INDUSTRY_OPTIONS,
            "help": "Choose the industries you want the Naukri profile to lean into.",
            "default": _first_non_empty(existing.get("target_industries"), fallback=[]),
        },
        {
            "id": "must_win_achievements",
            "label": "Missing wins to highlight",
            "type": "textarea",
            "help": "Add metrics, awards, launches, or transformations that are not clearly visible in the resume.",
            "default": _first_non_empty(existing.get("must_win_achievements"), fallback=""),
        },
    ]


def build_naukri_resume_context(resume_data: dict, answers: dict, profile: dict, prefs: dict) -> dict:
    enriched = deepcopy(resume_data or {})

    target_roles = [str(role).strip() for role in answers.get("target_roles", []) if str(role).strip()]
    preferred_locations = [str(city).strip() for city in answers.get("preferred_locations", []) if str(city).strip()]
    target_industries = [str(ind).strip() for ind in answers.get("target_industries", []) if str(ind).strip()]
    achievements = (answers.get("must_win_achievements") or "").strip()

    current_location = (
        prefs.get("current_location")
        or profile.get("current_location")
        or (resume_data.get("location") or "")
    )

    enriched["target_title"] = target_roles[0] if target_roles else enriched.get("target_title", "")
    enriched["target_roles"] = target_roles
    enriched["preferred_locations"] = preferred_locations
    enriched["current_location"] = current_location
    enriched["notice_period"] = answers.get("notice_period", "")
    enriched["current_ctc_lpa"] = answers.get("current_ctc_lpa", 0.0)
    enriched["expected_ctc_lpa"] = answers.get("expected_ctc_lpa", 0.0)
    enriched["work_mode"] = answers.get("work_mode", "Any")
    enriched["target_industries"] = target_industries
    enriched["must_win_achievements"] = achievements
    enriched["naukri_context_notes"] = {
        "role_focus": target_roles,
        "location_focus": preferred_locations,
        "industry_focus": target_industries,
        "notice_period": answers.get("notice_period", ""),
        "work_mode": answers.get("work_mode", "Any"),
        "must_win_achievements": achievements,
    }
    return enriched
