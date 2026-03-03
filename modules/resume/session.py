# -*- coding: utf-8 -*-
"""
ResumeBuilderSession — multi-turn Claude conversation for resume building.
Mirrors the ApproachNoteSession pattern from approach_note_generator.
"""
from __future__ import annotations

import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS_PROBE, MAX_TOKENS_GENERATE
from modules.resume.prompts import SYSTEM_PROMPT, GENERATE_PROMPT, READY_MARKER, build_init_prompt

HINDI_CHARS = set(range(0x0900, 0x097F))  # Devanagari Unicode range


def _is_hindi(text: str) -> bool:
    count = sum(1 for ch in text if ord(ch) in HINDI_CHARS)
    return count / max(len(text), 1) > 0.08


class ResumeBuilderSession:
    """Manages the full resume-building conversation for one user."""

    def __init__(self, api_key: str, existing_profile: dict = None):
        self.client           = anthropic.Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
        self.messages: list   = []
        self.exchange_count   = 0
        self.ready_to_generate = False
        self.existing_profile  = existing_profile or {}
        self.user_is_hindi     = False

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self) -> str:
        """Send the welcome + first probe, return CareerOS's opening message."""
        init_text = build_init_prompt(self.existing_profile)
        # The opening message comes from CareerOS, not from a user message
        # We prime the conversation by adding a synthetic first user message
        self.messages.append({
            "role": "user",
            "content": "Start the resume building session with me."
        })
        response = self._call_api(MAX_TOKENS_PROBE)
        # Replace with the actual opening prompt (Claude generates better when we seed it)
        # Overwrite: send the formatted init prompt as assistant's first message
        self.messages.pop()
        self.messages.append({"role": "assistant", "content": init_text})
        return init_text

    def send(self, user_message: str) -> str:
        """Send user message, get CareerOS reply."""
        if _is_hindi(user_message):
            self.user_is_hindi = True

        self.messages.append({"role": "user", "content": user_message})
        response = self._call_api(MAX_TOKENS_PROBE)
        self.messages.append({"role": "assistant", "content": response})
        self.exchange_count += 1
        self._check_ready(response)
        return self._strip_marker(response)

    def generate_resume(self) -> dict:
        """
        Send generation request, parse and return the resume JSON.
        Raises ValueError on malformed JSON.
        """
        self.messages.append({"role": "user", "content": GENERATE_PROMPT})
        raw = self._call_api(MAX_TOKENS_GENERATE)
        self.messages.append({"role": "assistant", "content": raw})
        return self._parse_json(raw)

    def get_messages_for_storage(self) -> list:
        """Return conversation history suitable for JSON storage."""
        return self.messages.copy()

    @classmethod
    def restore(cls, api_key: str, messages: list, exchange_count: int) -> "ResumeBuilderSession":
        """Restore a session from saved conversation history."""
        session = cls(api_key=api_key)
        session.messages       = messages
        session.exchange_count = exchange_count
        return session

    # ── Private ────────────────────────────────────────────────────────────────

    def _call_api(self, max_tokens: int) -> str:
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=self.messages,
        )
        return response.content[0].text

    def _check_ready(self, text: str) -> None:
        if READY_MARKER in text:
            self.ready_to_generate = True

    def _strip_marker(self, text: str) -> str:
        return text.replace(READY_MARKER, "").strip()

    def _parse_json(self, raw: str) -> dict:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
        start = cleaned.find("{")
        end   = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in Claude response.")
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON from Claude: {exc}") from exc
