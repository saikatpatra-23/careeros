# -*- coding: utf-8 -*-
"""
UserStore — JSON-based per-user persistence.
One directory per user, keyed by email hash. No database required.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from config import DATA_DIR


class UserStore:
    """Read/write per-user JSON files under data/users/{email_hash}/"""

    def __init__(self, email: str):
        self.email   = email
        self.user_id = hashlib.md5(email.lower().encode()).hexdigest()[:12]
        self.user_dir = Path(DATA_DIR) / self.user_id
        self.user_dir.mkdir(parents=True, exist_ok=True)

    # ── Core I/O ──────────────────────────────────────────────────────────────

    def save(self, filename: str, data: Any) -> None:
        path = self.user_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, filename: str, default: Any = None) -> Any:
        path = self.user_dir / filename
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default

    def exists(self, filename: str) -> bool:
        return (self.user_dir / filename).exists()

    # ── Named helpers ──────────────────────────────────────────────────────────

    def save_profile(self, profile_dict: dict) -> None:
        self.save("profile.json", profile_dict)

    def load_profile(self) -> dict:
        return self.load("profile.json", {})

    def save_resume(self, resume_dict: dict) -> None:
        # Keep last 5 versions
        history = self.load("resume_history.json", [])
        history.append(resume_dict)
        self.save("resume_history.json", history[-5:])
        self.save("generated_resume.json", resume_dict)

    def load_resume(self) -> dict:
        return self.load("generated_resume.json", {})

    def save_chat_history(self, history: list) -> None:
        self.save("resume_chat.json", history)

    def load_chat_history(self) -> list:
        return self.load("resume_chat.json", [])

    def save_profile_optimizer(self, data: dict) -> None:
        self.save("profile_optimizer.json", data)

    def load_profile_optimizer(self) -> dict:
        return self.load("profile_optimizer.json", {})

    def save_apply_prefs(self, data: dict) -> None:
        self.save("apply_prefs.json", data)

    def load_apply_prefs(self) -> dict:
        return self.load("apply_prefs.json", {})

    def save_apply_run(self, run: dict) -> None:
        history = self.load("apply_history.json", [])
        history.insert(0, run)
        self.save("apply_history.json", history[:30])  # keep last 30 runs

    def load_apply_history(self) -> list:
        return self.load("apply_history.json", [])

    def save_cover_letter(self, data: dict) -> None:
        history = self.load("cover_letters.json", [])
        history.insert(0, data)
        self.save("cover_letters.json", history[:10])  # keep last 10

    def load_cover_letters(self) -> list:
        return self.load("cover_letters.json", [])

    def save_hr_invite(self, invite: dict) -> None:
        history = self.load("hr_invites.json", [])
        history.insert(0, invite)
        self.save("hr_invites.json", history[:50])  # keep last 50

    def load_hr_invites(self) -> list:
        return self.load("hr_invites.json", [])

    # ── Summary for dashboard ─────────────────────────────────────────────────

    def summary(self) -> dict:
        resume = self.load_resume()
        profile = self.load_profile()
        return {
            "has_resume":       bool(resume),
            "target_role":      resume.get("structured_data", {}).get("target_title", ""),
            "domain":           resume.get("domain_family", ""),
            "profile_complete": bool(profile.get("current_title")),
            "resume_version":   resume.get("version", 0),
        }
