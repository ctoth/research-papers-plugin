#!/usr/bin/env python3
"""Stamp extraction provenance onto pipeline artifacts.

Adds or updates a `produced_by` block recording which agent, skill, and
plugin version produced the file, plus a UTC timestamp.

Supports two file types:
  - .md  — writes into YAML frontmatter
  - .yaml — writes into the top-level `source:` block

Usage:
    uv run stamp_provenance.py FILE --agent claude-opus-4-6 --skill paper-reader

Plugin version is autodetected from the nearest plugin.json.
Timestamp is always generated (UTC ISO-8601).
Safe to run multiple times (idempotent — overwrites previous produced_by).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_plugin_version(start: Path) -> str | None:
    """Walk up from *start* looking for .claude-plugin/plugin.json."""
    current = start if start.is_dir() else start.parent
    for _ in range(20):
        candidate = current / ".claude-plugin" / "plugin.json"
        if candidate.is_file():
            data = json.loads(candidate.read_text(encoding="utf-8"))
            return data.get("version")
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# YAML frontmatter helpers (for .md files)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# Matches a produced_by block: the key line plus all indented continuation lines.
_PRODUCED_BY_BLOCK_RE = re.compile(
    r"^produced_by:\s*\n(?:[ \t]+\S[^\n]*\n?)*", re.MULTILINE
)


def _build_produced_by_yaml(agent: str, skill: str, plugin_version: str | None, timestamp: str) -> str:
    lines = [
        "produced_by:",
        f'  agent: "{agent}"',
        f'  skill: "{skill}"',
    ]
    if plugin_version is not None:
        lines.append(f'  plugin_version: "{plugin_version}"')
    lines.append(f'  timestamp: "{timestamp}"')
    return "\n".join(lines)


def stamp_md(text: str, agent: str, skill: str, plugin_version: str | None, timestamp: str) -> tuple[str, bool]:
    """Add or update produced_by in markdown YAML frontmatter."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return text, False

    frontmatter = match.group(1)
    body = text[match.end():]
    produced_by_block = _build_produced_by_yaml(agent, skill, plugin_version, timestamp)

    if _PRODUCED_BY_BLOCK_RE.search(frontmatter):
        new_frontmatter = _PRODUCED_BY_BLOCK_RE.sub(produced_by_block, frontmatter).rstrip()
    else:
        new_frontmatter = frontmatter.rstrip() + "\n" + produced_by_block

    result = f"---\n{new_frontmatter}\n---\n{body}"
    return result, result != text


# ---------------------------------------------------------------------------
# YAML source-block helpers (for .yaml files)
# ---------------------------------------------------------------------------

# Matches a produced_by block anywhere in the file.
_YAML_PRODUCED_BY_RE = re.compile(
    r"^produced_by:\s*\n(?:[ \t]+\S[^\n]*\n?)*", re.MULTILINE
)

# Matches the source: block header (we insert produced_by after source:).
_SOURCE_BLOCK_RE = re.compile(r"^source:\s*\n(?:[ \t]+\S[^\n]*\n)*", re.MULTILINE)


def stamp_yaml(text: str, agent: str, skill: str, plugin_version: str | None, timestamp: str) -> tuple[str, bool]:
    """Add or update produced_by in a YAML file's top level."""
    produced_by_block = _build_produced_by_yaml(agent, skill, plugin_version, timestamp) + "\n"

    if _YAML_PRODUCED_BY_RE.search(text):
        result = _YAML_PRODUCED_BY_RE.sub(produced_by_block, text, count=1)
        return result, result != text

    # Insert after the source: block if present, otherwise prepend.
    source_match = _SOURCE_BLOCK_RE.search(text)
    if source_match:
        insert_pos = source_match.end()
        # Ensure blank line separation.
        if not text[insert_pos - 1:insert_pos] == "\n":
            produced_by_block = "\n" + produced_by_block
        result = text[:insert_pos] + produced_by_block + text[insert_pos:]
    else:
        result = produced_by_block + text

    return result, result != text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stamp_file(path: Path, agent: str, skill: str, plugin_version: str | None = None, timestamp: str | None = None) -> bool:
    """Stamp provenance onto a file. Returns True if the file was changed."""
    if timestamp is None:
        timestamp = utc_timestamp()
    if plugin_version is None:
        plugin_version = find_plugin_version(path)

    text = path.read_text(encoding="utf-8")

    if path.suffix == ".md":
        result, changed = stamp_md(text, agent, skill, plugin_version, timestamp)
    elif path.suffix in (".yaml", ".yml"):
        result, changed = stamp_yaml(text, agent, skill, plugin_version, timestamp)
    else:
        print(f"Unsupported file type: {path.suffix}", file=sys.stderr)
        return False

    if changed:
        path.write_text(result, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Stamp extraction provenance onto pipeline artifacts.")
    parser.add_argument("file", type=Path, help="File to stamp (.md or .yaml)")
    parser.add_argument("--agent", required=True, help="Model name (e.g. claude-opus-4-6)")
    parser.add_argument("--skill", required=True, help="Skill name (e.g. paper-reader)")
    parser.add_argument("--plugin-version", default=None, help="Override autodetected plugin version")
    args = parser.parse_args()

    path = args.file.resolve()
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    changed = stamp_file(path, args.agent, args.skill, plugin_version=args.plugin_version)
    if changed:
        print(f"Stamped: {path.name}")
    else:
        print(f"No changes: {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
