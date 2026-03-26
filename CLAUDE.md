# research-papers-plugin

## Skill Execution

When a skill is explicitly invoked by name, treat its `SKILL.md` as an executable
procedure, not as general guidance.

Rules:
- Follow the skill literally and in order.
- Do not add unlisted tools, probes, optimizations, or alternate workflows.
- Do not substitute a "better" approach for the documented one.
- If a step tells you to invoke another skill or run a fallback helper, do exactly that.
- If a step says to read full stdout and follow it exactly, do not improvise after reading it.
- If a step is blocked or impossible on the current platform, stop at that exact step and report the blocker.
- Deviation requires explicit user approval first.

## Release Process

Version lives in `plugins/research-papers/.claude-plugin/plugin.json` (`"version"` field).
Tags use `v{version}` format. Commit message is the bare version number.

```
1. Edit plugin.json — bump "version"
2. git add plugins/research-papers/.claude-plugin/plugin.json
3. git commit -m "{version}"
4. git tag v{version}
5. git push && git push --tags
```
