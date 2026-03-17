# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Bootstrap concept definitions from claims.yaml files.

Extracts concept names, groups similar ones, and produces a concepts list.

Usage:
    uv run bootstrap_concepts.py <claims-dir> [--output concepts.yaml]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


def extract_concept_names(claims_dir: Path) -> set[str]:
    """Walk claims.yaml files under claims_dir, collect all concept names.

    Looks for 'concept', 'target_concept', and 'concepts' fields in claims.
    """
    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required.", file=sys.stderr)
        sys.exit(1)

    names: set[str] = set()

    for dirpath, _dirnames, filenames in os.walk(claims_dir):
        for fname in filenames:
            if fname != "claims.yaml":
                continue
            fpath = Path(dirpath) / fname
            with open(fpath, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or "claims" not in data:
                continue
            for claim in data["claims"]:
                if not isinstance(claim, dict):
                    continue
                # 'concept' field
                c = claim.get("concept")
                if c and isinstance(c, str):
                    names.add(c)
                # 'target_concept' field
                tc = claim.get("target_concept")
                if tc and isinstance(tc, str):
                    names.add(tc)
                # 'concepts' field (list)
                cs = claim.get("concepts")
                if isinstance(cs, list):
                    for item in cs:
                        if isinstance(item, str):
                            names.add(item)

    return names


def _tokenize(name: str) -> list[str]:
    """Split a concept name into tokens by underscore."""
    return name.split("_")


def _common_prefix_length(a: list[str], b: list[str]) -> int:
    """Count how many leading tokens match."""
    n = 0
    for x, y in zip(a, b):
        if x == y:
            n += 1
        else:
            break
    return n


# Known abbreviation pairs for concept names
_ABBREVIATIONS: dict[str, str] = {
    "freq": "frequency",
    "f0": "fundamental",
    "oq": "open_quotient",
    "vq": "voice_quality",
    "vol": "volume",
    "amp": "amplitude",
    "temp": "temperature",
    "dur": "duration",
    "dist": "distance",
    "vel": "velocity",
    "accel": "acceleration",
    "coeff": "coefficient",
    "param": "parameter",
    "spec": "spectral",
    "harm": "harmonic",
    "fund": "fundamental",
}


def _expand_abbreviations(name: str) -> str:
    """Expand known abbreviations in a concept name for comparison."""
    tokens = _tokenize(name)
    expanded = []
    for t in tokens:
        expanded.append(_ABBREVIATIONS.get(t, t))
    return "_".join(expanded)


def _similarity(a: str, b: str) -> float:
    """Compute a similarity score between two concept names.

    Returns a float between 0 and 1. Higher means more similar.
    Uses token-based comparison with abbreviation expansion.
    """
    if a == b:
        return 1.0

    # Expand abbreviations and compare
    ea = _expand_abbreviations(a)
    eb = _expand_abbreviations(b)
    if ea == eb:
        return 0.95

    tokens_a = _tokenize(ea)
    tokens_b = _tokenize(eb)

    # Common prefix in expanded form
    prefix_len = _common_prefix_length(tokens_a, tokens_b)
    max_len = max(len(tokens_a), len(tokens_b))
    if max_len == 0:
        return 0.0

    prefix_score = prefix_len / max_len

    # Token overlap (Jaccard-like)
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if set_a and set_b:
        overlap = len(set_a & set_b) / len(set_a | set_b)
    else:
        overlap = 0.0

    # Weighted combination
    score = max(prefix_score, overlap)

    # Boost if one is a substring of the other (expanded)
    if ea in eb or eb in ea:
        score = max(score, 0.7)

    return score


# Threshold for grouping
_SIMILARITY_THRESHOLD = 0.6


def group_similar_concepts(names: set[str] | list[str]) -> list[dict[str, Any]]:
    """Group similar concept names using string similarity heuristics.

    Args:
        names: Set or list of concept name strings.

    Returns:
        List of dicts, each with 'canonical_name' (str) and 'members' (list[str]).
        The canonical_name is the longest member of the group.
    """
    name_list = sorted(set(names))  # deterministic order
    if not name_list:
        return []

    # Union-find approach
    parent: dict[str, str] = {n: n for n in name_list}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Compare all pairs
    for i in range(len(name_list)):
        for j in range(i + 1, len(name_list)):
            if _similarity(name_list[i], name_list[j]) >= _SIMILARITY_THRESHOLD:
                union(name_list[i], name_list[j])

    # Build groups
    groups_map: dict[str, list[str]] = {}
    for n in name_list:
        root = find(n)
        groups_map.setdefault(root, []).append(n)

    # Build result with canonical = longest name in group
    result: list[dict[str, Any]] = []
    for members in groups_map.values():
        canonical = max(members, key=lambda n: (len(n), n))
        result.append({
            "canonical_name": canonical,
            "members": sorted(members),
        })

    return sorted(result, key=lambda g: g["canonical_name"])


def bootstrap(claims_dir: Path) -> list[dict[str, Any]]:
    """Full pipeline: extract concept names from claims, group similar ones.

    Args:
        claims_dir: Root directory containing paper subdirs with claims.yaml files.

    Returns:
        List of group dicts with 'canonical_name' and 'members'.
    """
    names = extract_concept_names(claims_dir)
    return group_similar_concepts(names)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bootstrap concept definitions from claims.yaml files"
    )
    parser.add_argument("claims_dir", type=Path, help="Directory containing paper subdirs with claims.yaml")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output YAML file path (default: stdout)")
    args = parser.parse_args()

    claims_dir = Path(args.claims_dir).resolve()
    if not claims_dir.is_dir():
        print(f"Error: {claims_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required.", file=sys.stderr)
        sys.exit(1)

    groups = bootstrap(claims_dir)

    output_text = yaml.dump(groups, default_flow_style=False, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"Wrote {len(groups)} concept groups to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
