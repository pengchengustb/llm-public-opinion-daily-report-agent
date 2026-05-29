"""Stable content hashing for deduplication."""

from __future__ import annotations

import hashlib


def build_content_hash(*parts: str | None) -> str:
    normalized = "\n".join((part or "").strip().lower() for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
