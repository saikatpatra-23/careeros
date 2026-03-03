# -*- coding: utf-8 -*-
"""
Data schemas for CareerOS persistence layer.
All objects serialize to/from plain dicts for JSON storage.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class WorkExperience:
    company: str
    title: str
    period: str           # "Jan 2020 - Mar 2023"
    raw_description: str  # what user told us in their own words
    repositioned_bullets: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class UserProfile:
    email: str
    name: str
    phone: str = ""
    linkedin_url: str = ""
    location: str = ""
    current_title: str = ""
    current_company: str = ""
    years_experience: int = 0
    current_ctc_lpa: float = 0.0
    expected_ctc_lpa: float = 0.0
    notice_days: int = 60
    target_role: str = ""
    target_role_family: str = ""   # e.g. "analysis_pm"
    domain_family: str = ""        # e.g. "enterprise_IT"
    preferred_locations: List[str] = field(default_factory=list)
    work_history: List[dict] = field(default_factory=list)  # List[WorkExperience.to_dict()]
    education: List[dict] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=lambda: ["English"])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "UserProfile":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class GeneratedResume:
    version: int
    created_at: str
    target_role: str
    domain_family: str
    structured_data: dict          # full resume JSON from Claude
    ats_keywords: List[str]
    role_suggestion: dict          # Claude's role recommendation JSON
    docx_filename: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
