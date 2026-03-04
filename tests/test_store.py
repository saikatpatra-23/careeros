# -*- coding: utf-8 -*-
"""
Tests for persistence/store.py — UserStore
Uses real temp directories (tmp_path) so file I/O is exercised without touching prod data.
"""
import json
import pytest
from unittest.mock import patch
from pathlib import Path


def make_store(tmp_path, email="test@example.com"):
    """Create a UserStore that writes to a temp directory."""
    with patch("persistence.store.DATA_DIR", str(tmp_path)):
        from persistence.store import UserStore
        return UserStore(email)


# ── Initialisation ────────────────────────────────────────────────────────────

class TestUserStoreInit:
    def test_user_id_is_deterministic(self, tmp_path):
        """Same email always produces the same user_id hash."""
        store1 = make_store(tmp_path, "alice@example.com")
        store2 = make_store(tmp_path, "alice@example.com")
        assert store1.user_id == store2.user_id

    def test_different_emails_get_different_ids(self, tmp_path):
        store_a = make_store(tmp_path, "alice@example.com")
        store_b = make_store(tmp_path, "bob@example.com")
        assert store_a.user_id != store_b.user_id

    def test_user_id_is_12_chars(self, tmp_path):
        store = make_store(tmp_path)
        assert len(store.user_id) == 12

    def test_user_dir_created_on_init(self, tmp_path):
        store = make_store(tmp_path)
        assert store.user_dir.exists()
        assert store.user_dir.is_dir()

    def test_email_case_insensitive(self, tmp_path):
        """MD5 is computed on lowercased email."""
        store_lower = make_store(tmp_path, "Alice@Example.COM")
        store_upper = make_store(tmp_path, "alice@example.com")
        assert store_lower.user_id == store_upper.user_id


# ── Core save / load / exists ─────────────────────────────────────────────────

class TestCoreIO:
    def test_save_and_load_round_trip(self, tmp_path):
        store = make_store(tmp_path)
        data = {"key": "value", "number": 42, "nested": {"a": [1, 2, 3]}}
        store.save("test.json", data)
        loaded = store.load("test.json")
        assert loaded == data

    def test_load_missing_file_returns_default(self, tmp_path):
        store = make_store(tmp_path)
        result = store.load("nonexistent.json", default={"fallback": True})
        assert result == {"fallback": True}

    def test_load_missing_file_returns_none_when_no_default(self, tmp_path):
        store = make_store(tmp_path)
        assert store.load("nonexistent.json") is None

    def test_load_corrupted_json_returns_default(self, tmp_path):
        store = make_store(tmp_path)
        # Write invalid JSON directly
        (store.user_dir / "corrupt.json").write_text("{ not valid json !!!",
                                                      encoding="utf-8")
        result = store.load("corrupt.json", default={"safe": True})
        assert result == {"safe": True}

    def test_exists_returns_false_before_save(self, tmp_path):
        store = make_store(tmp_path)
        assert store.exists("phantom.json") is False

    def test_exists_returns_true_after_save(self, tmp_path):
        store = make_store(tmp_path)
        store.save("real.json", {"x": 1})
        assert store.exists("real.json") is True

    def test_save_overwrites_existing(self, tmp_path):
        store = make_store(tmp_path)
        store.save("file.json", {"v": 1})
        store.save("file.json", {"v": 2})
        assert store.load("file.json")["v"] == 2


# ── Profile ───────────────────────────────────────────────────────────────────

class TestProfile:
    def test_profile_round_trip(self, tmp_path):
        store = make_store(tmp_path)
        profile = {"current_title": "TPM", "salary_min": 18}
        store.save_profile(profile)
        assert store.load_profile() == profile

    def test_load_profile_empty_returns_empty_dict(self, tmp_path):
        store = make_store(tmp_path)
        assert store.load_profile() == {}


# ── Resume (history + current) ────────────────────────────────────────────────

class TestResume:
    def test_save_resume_writes_current(self, tmp_path):
        store = make_store(tmp_path)
        resume = {"structured_data": {"target_title": "TPM"}, "version": 1}
        store.save_resume(resume)
        assert store.load_resume() == resume

    def test_save_resume_caps_history_at_5(self, tmp_path):
        store = make_store(tmp_path)
        for i in range(7):
            store.save_resume({"version": i})
        history = store.load("resume_history.json", [])
        assert len(history) == 5

    def test_save_resume_keeps_latest_in_history(self, tmp_path):
        store = make_store(tmp_path)
        for i in range(7):
            store.save_resume({"version": i})
        history = store.load("resume_history.json", [])
        # Most recent (version 6) must be present
        assert any(h["version"] == 6 for h in history)

    def test_load_resume_empty_returns_empty_dict(self, tmp_path):
        store = make_store(tmp_path)
        assert store.load_resume() == {}


# ── Apply prefs ───────────────────────────────────────────────────────────────

class TestApplyPrefs:
    def test_prefs_round_trip(self, tmp_path):
        store = make_store(tmp_path)
        prefs = {"target_title": "BA", "locations": ["Pune"], "salary_min": 12}
        store.save_apply_prefs(prefs)
        assert store.load_apply_prefs() == prefs

    def test_load_prefs_empty_returns_empty_dict(self, tmp_path):
        store = make_store(tmp_path)
        assert store.load_apply_prefs() == {}


# ── Apply history (capped at 30, newest first) ────────────────────────────────

class TestApplyHistory:
    def test_apply_run_saves_and_loads(self, tmp_path):
        store = make_store(tmp_path)
        run = {"date": "2026-03-04 09:00", "jobs_applied": 3}
        store.save_apply_run(run)
        history = store.load_apply_history()
        assert len(history) == 1
        assert history[0] == run

    def test_apply_history_newest_first(self, tmp_path):
        store = make_store(tmp_path)
        store.save_apply_run({"date": "first"})
        store.save_apply_run({"date": "second"})
        history = store.load_apply_history()
        assert history[0]["date"] == "second"

    def test_apply_history_capped_at_30(self, tmp_path):
        store = make_store(tmp_path)
        for i in range(35):
            store.save_apply_run({"run": i})
        assert len(store.load_apply_history()) == 30

    def test_apply_history_empty_returns_empty_list(self, tmp_path):
        store = make_store(tmp_path)
        assert store.load_apply_history() == []


# ── Cover letters (capped at 10, newest first) ────────────────────────────────

class TestCoverLetters:
    def test_cover_letter_saves_and_loads(self, tmp_path):
        store = make_store(tmp_path)
        letter = {"date": "2026-03-04", "cover_letter": "Dear...", "tone": "Professional"}
        store.save_cover_letter(letter)
        history = store.load_cover_letters()
        assert len(history) == 1
        assert history[0] == letter

    def test_cover_letters_newest_first(self, tmp_path):
        store = make_store(tmp_path)
        store.save_cover_letter({"tone": "first"})
        store.save_cover_letter({"tone": "second"})
        assert store.load_cover_letters()[0]["tone"] == "second"

    def test_cover_letters_capped_at_10(self, tmp_path):
        store = make_store(tmp_path)
        for i in range(13):
            store.save_cover_letter({"n": i})
        assert len(store.load_cover_letters()) == 10

    def test_cover_letters_empty_returns_empty_list(self, tmp_path):
        store = make_store(tmp_path)
        assert store.load_cover_letters() == []


# ── Summary ───────────────────────────────────────────────────────────────────

class TestSummary:
    def test_summary_with_no_data(self, tmp_path):
        store = make_store(tmp_path)
        s = store.summary()
        assert s["has_resume"] is False
        assert s["target_role"] == ""

    def test_summary_with_resume(self, tmp_path):
        store = make_store(tmp_path)
        store.save_resume({
            "structured_data": {"target_title": "Senior BA"},
            "domain_family": "enterprise_IT",
            "version": 2,
        })
        s = store.summary()
        assert s["has_resume"] is True
        assert s["target_role"] == "Senior BA"
        assert s["domain"] == "enterprise_IT"
        assert s["resume_version"] == 2
