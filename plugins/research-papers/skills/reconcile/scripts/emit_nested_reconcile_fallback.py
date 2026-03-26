#!/usr/bin/env python3
from __future__ import annotations

from textwrap import dedent


def main() -> None:
    print(
        dedent(
            """\
            # Nested Reconcile Procedure

            Use this when another skill needs reconciliation but your platform cannot reliably invoke
            nested skills.

            1. Treat the current input as either one paper directory or `--all`.
            2. For each target paper, confirm `notes.md` and `citations.md` both exist. Skip any
               paper that is missing either file.
            3. Forward reconciliation:
               - read `citations.md`
               - match cited papers against `papers/index.md`
               - update `## Collection Cross-References` in `notes.md`
            4. Reverse reconciliation:
               - grep the collection for references to this paper by author/year or directory name
               - update the paper's `### Cited By (in Collection)` section
            5. Conceptual links:
               - find strong or moderate non-citation links to other collection papers
               - write only concrete, specific links
            6. Update citing papers when they listed this paper as a lead and it is now in the
               collection. Avoid duplicate annotations.
            7. Be idempotent. Check for existing content before appending.
            8. Report what was reconciled, what was updated, and any tensions found.

            Do not partially open `reconcile/SKILL.md` after running this helper. Follow this
            procedure directly.
            """
        )
    )


if __name__ == "__main__":
    main()
