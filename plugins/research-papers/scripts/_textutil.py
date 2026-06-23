#!/usr/bin/env python3
"""Text house-style helpers (F4, F8).

Import-only module (no CLI, no launcher needed). Reused by the F4 house-style
lint and the F8 collection verify so the em-dash rule has a single source of
truth.
"""
from __future__ import annotations

EM_DASH = "—"  # —


def find_em_dashes(text: str) -> list[tuple[int, int]]:
    """Return (line, col) of every U+2014 em-dash. Line is 1-based, col 0-based."""
    out: list[tuple[int, int]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for col, ch in enumerate(line):
            if ch == EM_DASH:
                out.append((lineno, col))
    return out
