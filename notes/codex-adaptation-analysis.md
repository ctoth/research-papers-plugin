# Codex Adaptation Analysis — 2026-03-26

## Goal
Analyze whether research-papers skills can work in Codex CLI despite no nested skill invocation, and evaluate the proposed "helper script that prints full downstream procedure" pattern.

## What I Observed

### Skill Classification
- **8 of 13 skills are pure leaves** — work on Codex today with zero changes
- **3 orchestrators**: paper-process (depth 3), process-new-papers (depth 2), process-leads (depth 4+)
- **2 hybrids**: paper-reader (calls reconcile, depth 1), adjudicate (conditionally calls paper-process)

### Existing Codex Fallback
Every orchestrator SKILL.md already says: "If explicit skill invocation is available, use it. Otherwise, follow the [skill-name] SKILL.md instructions directly." This is the current compatibility layer.

### Path Resolution
Skills install to `~/.agents/skills/<name>/SKILL.md` (via install_skills.py symlinks). Sibling skills are at `../<name>/SKILL.md` relative to the executing skill. The SKILL.md text does NOT currently include explicit paths — it just says "follow the instructions directly" without saying where to find them.

### Context Budget Problem
- paper-process inlines: paper-retriever (~80 lines) + paper-reader (~430 lines) + extract-claims (~300+ lines) = ~800 lines
- process-leads multiplies this by N leads, each needing the full paper-process chain
- paper-reader → reconcile is only ~1 extra read, manageable

### process-leads Is Architecturally Incompatible
Requires both nested skill invocation AND subagent dispatch (parallel paper-process calls + foreman coordination). Cannot be replicated in Codex's single-context model.

## Verdict on Helper Script Pattern
**Not the least-bad design.** A helper script that prints downstream procedures is essentially `cat ../sibling/SKILL.md` — trivial indirection that adds maintenance cost without reducing context consumption or solving the subagent problem.

**Better approach:** Add explicit read paths to the 3-4 orchestrator SKILL.md files (one-line edits per downstream call), and degrade process-leads to "extract leads, output list of `$paper-process` commands for user to run separately."

## What Worked
- Full skill inventory and dependency graph completed
- Clear classification of orchestrators vs leaves
- Identified that existing fallback pattern is 90% of the solution

## What Didn't Apply
- No code changes were requested — this was analysis only
- No Codex runtime was available to test actual behavior

## Next Steps
- If Q wants implementation: add explicit `../paper-retriever/SKILL.md` paths to orchestrator fallback text
- If Q wants process-leads Codex support: build a lead-extraction script that outputs runnable commands (data tool, not procedure-printer)
- No templating/Jinja system needed
