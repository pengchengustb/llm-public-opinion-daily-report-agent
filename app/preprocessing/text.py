"""Text cleaning helpers."""

from __future__ import annotations

import re

WHITESPACE_RE = re.compile(r"\s+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_text(value: str) -> str:
    without_controls = CONTROL_RE.sub(" ", value)
    return WHITESPACE_RE.sub(" ", without_controls).strip()
