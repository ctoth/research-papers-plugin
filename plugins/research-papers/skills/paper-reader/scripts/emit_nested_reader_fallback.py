#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def p(path: Path) -> str:
    return path.resolve().as_posix()


def main() -> None:
    skill_dir = Path(__file__).resolve().parent.parent
    hash_script = skill_dir / "scripts" / "paper_hash.py"
    reconcile_helper = (
        skill_dir.parent / "reconcile" / "scripts" / "emit_nested_reconcile_fallback.py"
    )

    print(
        dedent(
            f"""\
            # Nested Paper Reader Procedure

            Use this when another skill needs paper-reader but your platform cannot reliably invoke
            nested skills.

            Treat this as an executable checklist.
            Do not substitute unlisted tools or alternate workflows after reading it.
            If a step is blocked, stop at that step and report the exact blocker.
            If you dispatch any subagent for chunk reading, synthesis, abstract extraction, or
            citations extraction, use the strongest available full-size model. Never use a
            mini/small/flash tier model for paper extraction.

            1. Treat the current argument as either a paper directory or a PDF path.
            2. If it is a PDF path, look for an existing paper directory first:
               `python "{p(hash_script)}" --papers-dir papers/ lookup "<pdf-basename-without-.pdf>"`
            3. If a directory already exists and already has `notes.md`, `abstract.md`, and
               `citations.md`, delete only the duplicate root-level PDF if one was supplied from
               `papers/` root, then stop with "Already complete".
            4. Otherwise determine page count:
               `pdfinfo "<pdf-path>" 2>/dev/null | grep Pages || echo "pdfinfo not available"`
            5. Always convert pages. Read page 0 first to recover author, year, and title.
               Determine the canonical directory name `LastName_Year_ShortTitle`.
            6. Create `./papers/<dirname>/pngs`, move the source PDF into
               `./papers/<dirname>/paper.pdf` with `mv` not `cp`, then render all page images with
               `magick`.
            7. If the paper has 50 pages or fewer, read every page image yourself. Do not sample.
               If it has more than 50 pages, split it into 50-page chunks, use subagents only if
               available and only with the strongest full-size model, and synthesize the chunk
               notes into one final `notes.md` without compressing away detail.
            8. Write these files in the paper directory:
               - `notes.md` as a dense paper surrogate with exhaustive implementation details and page citations `*(p.N)*`
               - `description.md`
               - `abstract.md`
               - `citations.md`
            9. After those files exist, run this exact helper command for reconciliation:
               `python "{p(reconcile_helper)}"`
               Read its full stdout and follow it exactly on the current paper directory.
            10. Update `papers/index.md` for the new paper.
            11. Report the paper directory and a short usefulness assessment.

            Do not partially open `paper-reader/SKILL.md` after running this helper. Follow this
            procedure directly.
            """
        )
    )


if __name__ == "__main__":
    main()
