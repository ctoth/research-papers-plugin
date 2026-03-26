#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def p(path: Path) -> str:
    return path.resolve().as_posix()


def main() -> None:
    skill_dir = Path(__file__).resolve().parent.parent
    retriever_helper = (
        skill_dir.parent / "paper-retriever" / "scripts" / "emit_nested_retriever_fallback.py"
    )
    reader_helper = (
        skill_dir.parent / "paper-reader" / "scripts" / "emit_nested_reader_fallback.py"
    )
    claims_helper = (
        skill_dir.parent / "extract-claims" / "scripts" / "emit_nested_claims_fallback.py"
    )

    print(
        dedent(
            f"""\
            # Nested Paper Process Procedure

            Use this when another skill needs paper-process but your platform cannot reliably invoke
            nested skills.

            Treat this as an executable checklist.
            Do not substitute unlisted tools or alternate workflows after reading it.
            If a step is blocked, stop at that step and report the exact blocker.

            1. Run this exact helper for retrieval and read its full stdout:
               `python "{p(retriever_helper)}"`
               Then follow that procedure on the current paper identifier until you have a retrieved
               paper directory and `paper.pdf`.
               A retrieved `paper.pdf` plus `metadata.json` is not success for paper-process.
            2. Run this exact helper for reading and read its full stdout:
               `python "{p(reader_helper)}"`
               Then follow that procedure on the retrieved PDF path or paper directory until
               `notes.md`, `description.md`, `abstract.md`, `citations.md`, and `papers/index.md`
               are all updated.
            3. If the original input was a local root-level PDF and the paper directory now contains
               `paper.pdf`, delete the original root-level PDF.
            4. Run this exact helper for claim extraction and read its full stdout:
               `python "{p(claims_helper)}"`
               Then follow that procedure on the current paper directory until `claims.yaml`
               validates.
            5. Write `./reports/paper-<safe-name>.md` summarizing retrieval, reading, claim
               extraction, and usefulness.
            6. Stop on retrieval failure. If reading fails, report that state and stop before claims.
               If claims fail, report that state without pretending success.

            Do not manually open sibling `SKILL.md` files piecemeal after running this helper.
            Follow these helper-driven procedures directly.
            """
        )
    )


if __name__ == "__main__":
    main()
