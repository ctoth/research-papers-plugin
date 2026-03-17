# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Batch-generate claims.yaml for all papers in a directory.

Usage:
    uv run batch_generate_claims.py <papers-dir> [--skip-existing]
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_generate_claims():
    """Import generate_claims from the sibling script using importlib."""
    script_path = Path(__file__).resolve().parent / "generate_claims.py"
    spec = importlib.util.spec_from_file_location("generate_claims", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_gc_module = _load_generate_claims()


def batch_generate(papers_dir: Path, skip_existing: bool = False) -> dict[str, int]:
    """Iterate paper subdirs, run generate_claims on each with notes.md.

    Args:
        papers_dir: Root directory containing paper subdirectories.
        skip_existing: If True, skip papers that already have claims.yaml.

    Returns:
        Dict with keys "processed", "skipped", "errors".
    """
    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    processed = 0
    skipped = 0
    errors = 0

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue

        notes_path = paper_dir / "notes.md"
        if not notes_path.exists():
            continue

        claims_path = paper_dir / "claims.yaml"
        if skip_existing and claims_path.exists():
            skipped += 1
            continue

        try:
            result = _gc_module.generate_claims(paper_dir)
            with open(claims_path, "w", encoding="utf-8") as f:
                yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            processed += 1
        except Exception as exc:
            print(f"Error processing {paper_dir.name}: {exc}", file=sys.stderr)
            errors += 1

    return {"processed": processed, "skipped": skipped, "errors": errors}


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch-generate claims.yaml for all papers in a directory"
    )
    parser.add_argument("papers_dir", type=Path, help="Root directory containing paper subdirectories")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip papers that already have claims.yaml")
    args = parser.parse_args()

    papers_dir = Path(args.papers_dir).resolve()
    if not papers_dir.is_dir():
        print(f"Error: {papers_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    result = batch_generate(papers_dir, skip_existing=args.skip_existing)
    print(f"Processed: {result['processed']}, Skipped: {result['skipped']}, Errors: {result['errors']}")


if __name__ == "__main__":
    main()
