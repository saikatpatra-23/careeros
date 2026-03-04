# -*- coding: utf-8 -*-
"""
Tests for modules/ats/checker.py::check_ats
Mocks the Anthropic client — no real API calls made.
"""
import json
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.helpers import make_mock_claude_response

VALID_ATS_RESPONSE = {
    "overall_score": 78,
    "verdict": "Apply with Tweaks",
    "verdict_reason": "Strong title and skills match but salary expectation slightly above JD range.",
    "naukri_parameters": {
        "skills":      {"score": 82, "comment": "8/10 required skills present"},
        "designation": {"score": 90, "comment": "Title matches exactly"},
        "experience":  {"score": 85, "comment": "8 yrs fits 6-10 yr band"},
        "salary":      {"score": 60, "comment": "Expected 20 LPA, JD budgets 18-24"},
        "location":    {"score": 95, "comment": "Pune matches job location"},
        "education":   {"score": 75, "comment": "B.E. meets requirement"},
    },
    "keywords_found": ["Agile", "Scrum", "JIRA", "Stakeholder Management"],
    "keywords_missing": ["PMP", "SAFe", "OKRs"],
    "recommendations": [
        {"priority": "High",   "action": "Add PMP to skills section", "where": "Skills section"},
        {"priority": "Medium", "action": "Mention SAFe experience",  "where": "Experience bullet"},
        {"priority": "Low",    "action": "Add OKR tracking example", "where": "Summary"},
    ],
    "resume_headline_suggestion": "Technical Program Manager | 8 Yrs | Agile | JIRA | Automotive",
    "one_liner_gap": "Missing PMP and SAFe certifications explicitly required in JD",
}


def make_client_mock(response_text: str) -> MagicMock:
    """Return a mocked anthropic.Anthropic instance whose messages.create returns response_text."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_claude_response(response_text)
    return mock_client


class TestCheckATS:
    # ── Happy path ────────────────────────────────────────────────────────────

    def test_happy_path_returns_expected_keys(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock(json.dumps(VALID_ATS_RESPONSE))
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            result = check_ats(sample_resume_data, sample_jd, api_key="fake-key")

        assert result["overall_score"] == 78
        assert result["verdict"] == "Apply with Tweaks"
        assert "naukri_parameters" in result
        assert "keywords_found" in result
        assert "keywords_missing" in result
        assert len(result["recommendations"]) == 3

    def test_all_six_naukri_params_present(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock(json.dumps(VALID_ATS_RESPONSE))
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            result = check_ats(sample_resume_data, sample_jd, api_key="fake-key")

        params = result["naukri_parameters"]
        for key in ["skills", "designation", "experience", "salary", "location", "education"]:
            assert key in params, f"Missing naukri_parameter: {key}"

    # ── JSON cleaning (markdown fences) ──────────────────────────────────────

    def test_json_wrapped_in_markdown_fences_is_parsed(self, sample_resume_data, sample_jd):
        fenced = f"```json\n{json.dumps(VALID_ATS_RESPONSE)}\n```"
        mock_client = make_client_mock(fenced)
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            result = check_ats(sample_resume_data, sample_jd, api_key="fake-key")
        assert result["overall_score"] == 78

    def test_json_with_preamble_text_is_parsed(self, sample_resume_data, sample_jd):
        preamble = "Sure, here is the analysis:\n" + json.dumps(VALID_ATS_RESPONSE)
        mock_client = make_client_mock(preamble)
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            result = check_ats(sample_resume_data, sample_jd, api_key="fake-key")
        assert result["overall_score"] == 78

    def test_plain_fences_without_json_label(self, sample_resume_data, sample_jd):
        fenced = f"```\n{json.dumps(VALID_ATS_RESPONSE)}\n```"
        mock_client = make_client_mock(fenced)
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            result = check_ats(sample_resume_data, sample_jd, api_key="fake-key")
        assert result["overall_score"] == 78

    # ── Error cases ───────────────────────────────────────────────────────────

    def test_no_json_in_response_raises_value_error(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock("Sorry, I cannot analyse this.")
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            with pytest.raises(ValueError, match="No JSON"):
                check_ats(sample_resume_data, sample_jd, api_key="fake-key")

    # ── Input handling ────────────────────────────────────────────────────────

    def test_long_jd_is_truncated_before_api_call(self, sample_resume_data):
        """JD > 4000 chars should be truncated — verify API is still called (no crash)."""
        long_jd = "x" * 10_000
        mock_client = make_client_mock(json.dumps(VALID_ATS_RESPONSE))
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            result = check_ats(sample_resume_data, long_jd, api_key="fake-key")
        assert result["overall_score"] == 78

    def test_empty_jd_does_not_crash(self, sample_resume_data):
        mock_client = make_client_mock(json.dumps(VALID_ATS_RESPONSE))
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client):
            from modules.ats.checker import check_ats
            result = check_ats(sample_resume_data, "", api_key="fake-key")
        assert isinstance(result, dict)

    def test_api_key_passed_through(self, sample_resume_data, sample_jd):
        """The api_key parameter should reach the Anthropic constructor."""
        mock_client = make_client_mock(json.dumps(VALID_ATS_RESPONSE))
        with patch("modules.ats.checker.anthropic.Anthropic", return_value=mock_client) as mock_cls:
            from modules.ats.checker import check_ats
            check_ats(sample_resume_data, sample_jd, api_key="my-test-key")
        mock_cls.assert_called_once_with(api_key="my-test-key")
