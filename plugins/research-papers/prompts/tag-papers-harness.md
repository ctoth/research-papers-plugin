# Tag Papers Harness Prompt

You are working on the Qlatt paper database at `C:\Users\Q\code\Qlatt\papers`.

Your task is to add `tags:` frontmatter to `description.md` for a provided batch of paper directories that are currently untagged.

Use the existing plugin instructions as policy:
- Source skill: `C:\Users\Q\code\research-papers-plugin\plugins\research-papers\skills\tag-papers\SKILL.md`

Follow this exact workflow:

1. Read `C:\Users\Q\code\Qlatt\papers\index.md` and extract the existing tag vocabulary already in use.
2. For each paper in the provided batch:
   - Read `papers/<PaperDir>/notes.md`
   - Read `papers/<PaperDir>/description.md`
   - Pick 2-5 tags
3. Prefer reusing existing tags when they fit.
4. Tags must be:
   - lowercase
   - hyphenated when multiword
   - topic tags, not venue tags
   - usually 3 tags unless there is a clear reason for 2 or 4
5. Edit only:
   - `papers/<PaperDir>/description.md`
   - `papers/index.md`
6. If `description.md` has no frontmatter, prepend:

```md
---
tags: [tag1, tag2, tag3]
---
```

7. Do not rewrite the description body text.
8. Do not edit `notes.md`.
9. Do not read PDFs; use `notes.md` only.
10. After the batch is done, run:

```bash
python C:\Users\Q\code\research-papers-plugin\plugins\research-papers\scripts\generate-paper-index.py C:\Users\Q\code\Qlatt
```

11. Report:
   - papers tagged
   - tags introduced
   - existing tags reused
   - papers skipped and why

Batch input format:

```text
Abramson_Whalen_2017_VOTat50
Allen_1977_ModularAudioResponse
...
```

If a paper is missing `notes.md` or `description.md`, skip it and report that explicitly.
