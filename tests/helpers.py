# -*- coding: utf-8 -*-
"""Shared test helpers (importable — not pytest fixtures)."""
from unittest.mock import MagicMock


def make_mock_claude_response(text: str) -> MagicMock:
    """Build a fake anthropic.Message response with the given text content."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response
