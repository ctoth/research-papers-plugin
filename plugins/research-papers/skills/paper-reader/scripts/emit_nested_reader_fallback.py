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
            Do not declare yourself blocked merely because this procedure does not name a
            platform-specific image-view tool. Use the platform's native local-image inspection
            capability for `pngs/page-*.png`; that is the intended page-image workflow.
            Only report an image-reading blocker after you have actually attempted to inspect a
            local page image such as `page-000.png` and the platform refused or failed.
            If you dispatch any subagent for chunk reading, synthesis, abstract extraction, or
            citations extraction, use the strongest available full-size model. Never use a
            mini/small/flash tier model for paper extraction.

            1. Treat the current argument as either a paper directory or a PDF path.
            2. If it is a PDF path, look for an existing paper directory first:
               `python "{p(hash_script)}" --papers-dir papers/ lookup "<pdf-basename-without-.pdf>"`
            3. If a directory already exists and already has `notes.md`, `abstract.md`, and
               `citations.md`, delete only the duplicate root-level PDF if one was supplied from
               `papers/` root, then stop with "Already complete".
            4. If a directory already exists but `notes.md` is missing, treat this as a
               rerun/regeneration case:
               - if `paper.pdf` and `pngs/page-000.png` already exist, reuse them and do not
                 reconvert;
               - if `paper.pdf` exists but `pngs/` is missing or incomplete, regenerate `pngs/`
                 from the existing `paper.pdf`.
            5. Determine the working PDF path, then determine page count:
               `pdfinfo "<working-pdf>" 2>/dev/null | grep Pages || echo "pdfinfo not available"`
            6. If `pngs/page-000.png` does not already exist, use the exact `magick` rendering
               commands from `paper-reader/SKILL.md`: render page 0 first to recover author,
               year, and title. Once those are known, generate the canonical dirname with:
               `python "{p(hash_script)}" generate --author "<surname>" --year "<year>" --title "<title>"`
               Then render all page images as `pngs/page-*.png`.
            7. Before long extraction, inspect `page-000.png` using the platform's native
               local-image inspection capability. Do not stop just because the exact tool name is
               unspecified. Only stop if the platform actually prevents local image inspection.
            8. If the paper has 50 pages or fewer, read every page image yourself. Do not sample
               and do not dispatch more readers for a small paper.
               If it has more than 50 pages, split it into 50-page chunks, use subagents only if
               available and only with the strongest full-size model, and synthesize the chunk
               notes into one final `notes.md` without compressing away detail.
            9. Write these files in the paper directory:
               - `notes.md` as a dense paper surrogate with exhaustive implementation details and page citations `*(p.N)*`
               - `metadata.json` with at least `title`, `authors` (array), `year`, `doi`, `abstract`, `url`, `pdf_url`, and `arxiv_id` (use `null` when unknown)
               - `description.md`
               - `abstract.md`
               - `citations.md`
            10. After those files exist, run this exact helper command for reconciliation:
               `python "{p(reconcile_helper)}"`
               Read its full stdout and follow it exactly on the current paper directory.
            11. Update `papers/index.md` for the new paper.
            12. Reading is complete only when these artifacts exist:
               `notes.md`, `metadata.json`, `description.md`, `abstract.md`, `citations.md`,
               and the `papers/index.md` entry.
            13. Report the paper directory and a short usefulness assessment.

            Do not partially open `paper-reader/SKILL.md` after running this helper. Follow this
            procedure directly.
            """
        )
    )


if __name__ == "__main__":
    main()
