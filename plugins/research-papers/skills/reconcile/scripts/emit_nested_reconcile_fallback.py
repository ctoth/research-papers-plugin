#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def main() -> None:
    skill_file = Path(__file__).resolve().parent.parent / "SKILL.md"
    print(skill_file.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
