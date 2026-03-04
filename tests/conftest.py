# -*- coding: utf-8 -*-
"""
Shared fixtures for CareerOS test suite.
"""
import json
import pytest
from unittest.mock import MagicMock
from tests.helpers import make_mock_claude_response  # noqa: F401 — re-exported for convenience


@pytest.fixture
def sample_resume_data():
    """Minimal but realistic resume data dict matching the app's structured_data schema."""
    return {
        "name": "Saikat Patra",
        "target_title": "Technical Program Manager",
        "summary": (
            "8+ years delivering cross-functional programs at Tata Technologies. "
            "Led a ₹12 Cr EV platform program, reduced defect leakage by 40%, "
            "and managed 18-member distributed teams across India and Germany."
        ),
        "experience": [
            {
                "company": "Tata Technologies",
                "title": "Technical Program Manager",
                "period": "Jan 2020 - Present",
                "repositioned_bullets": [
                    "Led ₹12 Cr EV platform program delivering 3 modules on time.",
                    "Reduced defect leakage by 40% via structured QA gates.",
                ],
                "tools_used": ["JIRA", "Confluence", "MS Project"],
                "achievements": ["Reduced defect leakage by 40%"],
            },
            {
                "company": "Tata Consultancy Services",
                "title": "Senior Business Analyst",
                "period": "Jun 2016 - Dec 2019",
                "repositioned_bullets": [
                    "Managed requirements for 5 enterprise clients.",
                ],
                "tools_used": ["Visio", "Excel"],
                "achievements": [],
            },
        ],
        "skills": {
            "core": ["Program Management", "Agile", "Scrum", "Stakeholder Management"],
            "tools": ["JIRA", "Confluence", "MS Project", "Visio"],
            "domain": ["Automotive", "EV", "Enterprise IT"],
        },
        "ats_keywords": [
            "Technical Program Manager", "Agile", "Scrum", "JIRA", "Confluence",
            "Stakeholder Management", "Risk Management", "Cross-functional",
        ],
        "education": [
            {"degree": "B.E. Mechanical Engineering", "institution": "Mumbai University", "year": "2015"}
        ],
    }


@pytest.fixture
def sample_jd():
    """Realistic JD for a TPM role at a mid-size Indian tech company."""
    return """
    Technical Program Manager — Enterprise Platform
    Location: Pune | Experience: 6-10 years | CTC: 18-24 LPA

    We are looking for a Technical Program Manager to lead our enterprise platform delivery.

    Responsibilities:
    - Own end-to-end program delivery for our core SaaS platform
    - Drive cross-functional alignment across engineering, product, and client teams
    - Manage risk, dependencies, and escalations across 3 scrum teams
    - Deliver detailed status reports to C-suite stakeholders

    Requirements:
    - 6+ years as a Technical Program Manager or Senior Business Analyst
    - Strong experience with Agile/Scrum frameworks
    - Proficiency in JIRA, Confluence, MS Project
    - Excellent stakeholder management and communication skills
    - Experience in enterprise software or SaaS domain preferred
    """


