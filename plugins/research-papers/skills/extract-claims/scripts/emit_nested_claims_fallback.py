#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def p(path: Path) -> str:
    return path.resolve().as_posix()


def main() -> None:
    skill_dir = Path(__file__).resolve().parent.parent
    generate_script = skill_dir / "scripts" / "generate_claims.py"

    print(
        dedent(
            f"""\
            # Nested Extract Claims Procedure

            Use this when another skill needs claim extraction but your platform cannot reliably
            invoke nested skills.

            1. Treat the current input as a paper directory. Confirm `notes.md` exists there. If it
               does not, stop and report that claim extraction cannot proceed yet.
            2. If `claims.yaml` does not exist, generate the mechanical baseline first:
               `python "{p(generate_script)}" "<paper_dir>"`
            3. Read `<paper_dir>/claims.yaml` if present and always read `<paper_dir>/notes.md`.
               Also inspect `<paper_dir>/paper.pdf` or page images only when you need provenance.
            4. If a concept registry exists (`concepts/*.yaml` or `knowledge/concepts/*.yaml`),
               resolve concepts against it before writing claims. Register or preserve descriptive
               names conservatively rather than inventing bogus IDs.
            5. Enrich or create claims so the final file has:
               - unique `claimN` ids
               - real provenance where possible
               - valid concept references where possible
               - valid SymPy for equation claims
               - CEL conditions only when the paper supports them
               - notes/stances only when the paper supports them
            6. Write the final `<paper_dir>/claims.yaml`.
            7. Validate it and keep fixing until clean:
               `uv run pks claim validate-file "<paper_dir>/claims.yaml"`
            8. Report mode used (`enrich` or `create`), validation result, and claim count.

            Do not partially open `extract-claims/SKILL.md` after running this helper. Follow this
            procedure directly.
            """
        )
    )


if __name__ == "__main__":
    main()
