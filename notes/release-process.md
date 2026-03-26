# Release Process Investigation - 2026-03-24

## GOAL
Document and execute the release process for this plugin.

## OBSERVATIONS
- Version lives in `plugins/research-papers/.claude-plugin/plugin.json` field `"version"`
- Current version: 3.3.3
- `marketplace.json` at repo root does NOT contain a version field — only plugin.json does
- Prior release commit (9a06769 "3.3.3") changed only plugin.json — single file bump
- Tags follow `v{major}.{minor}.{patch}` format (e.g. v3.3.3)
- Commit message for version bumps is just the bare version number (e.g. "3.3.3")
- Tags exist: v3.3.3, v3.3.2, v3.3.1, v3.3.0, v3.2.0, v3.1.1, v3.1.0, v3.0.1, v3.0.0, v2.6.4

## RELEASE PROCESS (derived from git history)
1. Edit `plugins/research-papers/.claude-plugin/plugin.json` — bump `"version"` field
2. Commit with message = bare version number (e.g. "3.3.4")
3. Tag with `v{version}` (e.g. `git tag v3.3.4`)
4. Push commit and tags (`git push && git push --tags`)

## NEXT
- Document in project CLAUDE.md
- Execute patch bump 3.3.3 → 3.3.4
