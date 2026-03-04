# -*- coding: utf-8 -*-
"""
Tests for modules/coverletter/generator.py::generate_cover_letter
Mocks the Anthropic client — no real API calls made.
"""
import json
import sys
import os
import pytest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.helpers import make_mock_claude_response

VALID_CL_RESPONSE = {
    "subject_line": "Technical Program Manager — 8 yrs Enterprise IT | Ref: Acme Corp",
    "cover_letter": (
        "Delivering complex programs on time is hard when engineering, product, and client teams "
        "speak different languages — I've spent 8 years at Tata Technologies doing exactly that.\n\n"
        "At Tata Technologies, I led a ₹12 Cr EV platform program that shipped 3 modules on schedule "
        "and reduced defect leakage by 40% through structured QA gates. I managed 18-member teams "
        "across India and Germany, keeping cross-timezone alignment tight enough that we hit 94% "
        "on-time delivery across 11 quarterly releases.\n\n"
        "Acme Corp's focus on enterprise SaaS scalability aligns directly with the cross-functional "
        "program discipline I've built. I'd welcome a 20-minute call to discuss how I can bring that "
        "delivery rigor to your platform team.\n\n"
        "Best regards,\nSaikat Patra"
    ),
    "word_count": 142,
    "opening_hook": (
        "Delivering complex programs on time is hard when engineering, product, and client teams "
        "speak different languages — I've spent 8 years at Tata Technologies doing exactly that."
    ),
    "tailoring_notes": (
        "Used JD's emphasis on cross-functional alignment and enterprise SaaS to select "
        "the EV platform program as the lead achievement."
    ),
}


def make_client_mock(response_text: str) -> MagicMock:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_claude_response(response_text)
    return mock_client


class TestGenerateCoverLetter:
    # ── Happy path ────────────────────────────────────────────────────────────

    def test_happy_path_returns_expected_keys(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock(json.dumps(VALID_CL_RESPONSE))
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            result = generate_cover_letter(sample_resume_data, sample_jd, tone="Professional")

        assert "subject_line" in result
        assert "cover_letter" in result
        assert "word_count" in result
        assert "opening_hook" in result
        assert "tailoring_notes" in result

    def test_correct_values_returned(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock(json.dumps(VALID_CL_RESPONSE))
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            result = generate_cover_letter(sample_resume_data, sample_jd)

        assert result["word_count"] == 142
        assert "Saikat Patra" in result["cover_letter"]

    # ── Tone is passed through ────────────────────────────────────────────────

    def test_tone_included_in_prompt(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock(json.dumps(VALID_CL_RESPONSE))
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            generate_cover_letter(sample_resume_data, sample_jd, tone="Concise")

        call_kwargs = mock_client.messages.create.call_args
        prompt_text = call_kwargs[1]["messages"][0]["content"]
        assert "Concise" in prompt_text

    def test_all_three_tones_accepted(self, sample_resume_data, sample_jd):
        for tone in ["Professional", "Confident", "Concise"]:
            mock_client = make_client_mock(json.dumps(VALID_CL_RESPONSE))
            with patch("modules.coverletter.generator.anthropic.Anthropic",
                       return_value=mock_client):
                from modules.coverletter.generator import generate_cover_letter
                result = generate_cover_letter(sample_resume_data, sample_jd, tone=tone)
            assert isinstance(result, dict)

    # ── JD handling ───────────────────────────────────────────────────────────

    def test_empty_jd_sends_fallback_text(self, sample_resume_data):
        mock_client = make_client_mock(json.dumps(VALID_CL_RESPONSE))
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            generate_cover_letter(sample_resume_data, jd="")

        prompt_text = mock_client.messages.create.call_args[1]["messages"][0]["content"]
        assert "No specific JD provided" in prompt_text

    def test_long_jd_is_truncated(self, sample_resume_data):
        """JD > 3000 chars should be truncated — the full 8500-char string must not appear in prompt."""
        long_jd = "Senior TPM role. " * 500  # ~8500 chars
        mock_client = make_client_mock(json.dumps(VALID_CL_RESPONSE))
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            generate_cover_letter(sample_resume_data, long_jd)

        prompt_text = mock_client.messages.create.call_args[1]["messages"][0]["content"]
        # The verbatim full JD (8500 chars) must NOT appear — confirms truncation happened
        assert long_jd not in prompt_text

    # ── JSON cleaning ─────────────────────────────────────────────────────────

    def test_json_in_markdown_fences_is_parsed(self, sample_resume_data, sample_jd):
        fenced = f"```json\n{json.dumps(VALID_CL_RESPONSE)}\n```"
        mock_client = make_client_mock(fenced)
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            result = generate_cover_letter(sample_resume_data, sample_jd)
        assert result["word_count"] == 142

    def test_json_with_preamble_is_parsed(self, sample_resume_data, sample_jd):
        preamble = "Here is your cover letter:\n" + json.dumps(VALID_CL_RESPONSE)
        mock_client = make_client_mock(preamble)
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            result = generate_cover_letter(sample_resume_data, sample_jd)
        assert result["word_count"] == 142

    # ── Error cases ───────────────────────────────────────────────────────────

    def test_no_json_in_response_raises_value_error(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock("I cannot write a cover letter for this.")
        with patch("modules.coverletter.generator.anthropic.Anthropic", return_value=mock_client):
            from modules.coverletter.generator import generate_cover_letter
            with pytest.raises(ValueError, match="No JSON"):
                generate_cover_letter(sample_resume_data, sample_jd)

    # ── API key ───────────────────────────────────────────────────────────────

    def test_api_key_passed_to_anthropic(self, sample_resume_data, sample_jd):
        mock_client = make_client_mock(json.dumps(VALID_CL_RESPONSE))
        with patch("modules.coverletter.generator.anthropic.Anthropic",
                   return_value=mock_client) as mock_cls:
            from modules.coverletter.generator import generate_cover_letter
            generate_cover_letter(sample_resume_data, sample_jd, api_key="my-key")
        mock_cls.assert_called_once_with(api_key="my-key")
