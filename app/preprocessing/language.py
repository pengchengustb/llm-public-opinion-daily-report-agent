"""Lightweight language detection heuristics."""

from __future__ import annotations


def detect_language(text: str) -> str:
    if not text.strip():
        return "unknown"

    chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    alpha_chars = sum(1 for char in text if char.isalpha())
    if chinese_chars >= 2 and chinese_chars >= max(1, alpha_chars // 3):
        return "zh-CN"
    if alpha_chars:
        return "en"
    return "unknown"
