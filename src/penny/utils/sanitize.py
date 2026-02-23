"""User input sanitization."""

from __future__ import annotations

import re


def sanitize_user_input(text: str) -> str:
    """Strip potentially harmful characters from user text."""
    text = text.strip()
    text = re.sub(r"[<>{}]", "", text)
    # Limit length to prevent prompt-injection-style payloads
    return text[:2000]
