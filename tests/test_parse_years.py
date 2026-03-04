# -*- coding: utf-8 -*-
"""
Tests for job_applier/run.py::_parse_years
Pure function — no mocking needed.
"""
import sys
import os
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "job_applier"))

from run import _parse_years

CURRENT_YEAR = datetime.now().year


class TestParseYears:
    # ── Two-year ranges ───────────────────────────────────────────────────────

    def test_two_full_years(self):
        assert _parse_years("2018 - 2022") == 4

    def test_month_year_to_month_year(self):
        assert _parse_years("Jan 2020 - Mar 2023") == 3

    def test_years_adjacent(self):
        assert _parse_years("2021 - 2022") == 1

    def test_same_year(self):
        # Edge: start == end → 0
        assert _parse_years("2021 - 2021") == 0

    def test_large_range(self):
        assert _parse_years("1999 - 2010") == 11

    # ── Single year (treated as start → current year) ─────────────────────────

    def test_single_start_year(self):
        expected = CURRENT_YEAR - 2021
        assert _parse_years("2021 - Present") == expected

    def test_single_year_with_month(self):
        expected = CURRENT_YEAR - 2024
        assert _parse_years("Mar 2024 - Present") == expected

    def test_only_year_in_string(self):
        # A string with just one 4-digit year — treated as start year
        expected = CURRENT_YEAR - 2020
        assert _parse_years("2020") == expected

    # ── No years ──────────────────────────────────────────────────────────────

    def test_empty_string_returns_default(self):
        assert _parse_years("") == 2

    def test_no_years_in_string_returns_default(self):
        assert _parse_years("no years here") == 2

    def test_short_numbers_not_years(self):
        # 4-digit numbers outside 19xx/20xx range should not be matched
        assert _parse_years("1234 - 5678") == 2

    def test_whitespace_only_returns_default(self):
        assert _parse_years("   ") == 2

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_period_with_three_years_uses_first_and_last(self):
        # "2015 - 2018 - 2021" — last minus first = 6
        result = _parse_years("2015 - 2018 - 2021")
        assert result == 6

    def test_current_year_in_period(self):
        # "2022 - 2026" should give 4 (not treated as "Present")
        assert _parse_years(f"2022 - {CURRENT_YEAR}") == CURRENT_YEAR - 2022
