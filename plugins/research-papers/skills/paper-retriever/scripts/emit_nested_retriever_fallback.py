#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def p(path: Path) -> str:
    return path.resolve().as_posix()


def main() -> None:
    skill_dir = Path(__file__).resolve().parent.parent
    search_script = skill_dir / "scripts" / "search_papers.py"
    fetch_script = skill_dir / "scripts" / "fetch_paper.py"

    print(
        dedent(
            f"""\
            # Nested Paper Retriever Procedure

            Use this when another skill needs paper retrieval but your platform cannot
            reliably invoke nested skills.

            1. Parse the current paper identifier. It can be an arXiv URL/ID, DOI, ACL URL,
               AAAI URL, or a paper title.
            2. If the input is a title rather than a direct identifier, run this exact command:
               `uv run "{p(search_script)}" "PAPER TITLE" --source all --max-results 5 --json`
               Pick the clearest match. If the results are ambiguous, stop and ask the user.
            3. Download and create the canonical paper directory with this exact command:
               `uv run "{p(fetch_script)}" "<identifier>" --papers-dir papers/`
            4. Capture the resulting paper directory and PDF path. The expected success shape is
               `papers/<Author_Year_Title>/paper.pdf` plus `metadata.json`. If the script reports
               `fallback_needed: true`, treat `dirname`/`directory` as planned output paths only:
               no paper directory or `metadata.json` has been created yet.
            5. If the fetch script reports `fallback_needed: true`, try browser automation for
               sci-hub. If browser automation succeeds, create `./papers/<dirname>/paper.pdf`,
               then run `uv run "{p(fetch_script)}" "<identifier>" --papers-dir papers/ --output-dir "<dirname>" --metadata-only`
               so `metadata.json` is written only after the PDF exists. If browser automation is
               unavailable, stop and ask the user for a manual PDF.
            6. Verify success:
               `file "./papers/<dirname>/paper.pdf"`
               `ls -la "./papers/<dirname>/"`
               Confirm a real PDF and `metadata.json` both exist.
            7. Report the retrieved PDF path and source, then hand that paper directory/PDF path
               back to the calling workflow.

            Do not open `paper-retriever/SKILL.md` piecemeal after running this helper. Follow this
            procedure directly.
            """
        )
    )


if __name__ == "__main__":
    main()
