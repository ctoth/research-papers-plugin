---
name: make-skill
description: Create new skills from existing prompts or workflow patterns. Analyzes prompt files to extract reusable structure, determines appropriate frontmatter settings, and generates properly formatted SKILL.md files.
argument-hint: [prompt-path(s)] [--name name] [--global]
allowed-tools: Read, Write, Bash(mkdir:*), Bash(ls:*), Glob
---

# Make Skill: $ARGUMENTS

Create a new skill from existing prompt file(s).

## Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- **paths**: Prompt file paths or glob patterns (e.g., `./prompts/research-*.md`, `./prompts/paper-reader.md`)
- **--name NAME**: Optional explicit skill name (otherwise derived from content)
- **--global**: If present, install to `~/.claude/skills/` instead of `./.claude/skills/`

## Step 2: Read Source Prompts

```bash
# If glob pattern, expand it first
ls $PATHS 2>/dev/null || echo "No matches"
```

Read all matching prompt files.

## Step 3: Analyze Patterns

For each prompt, identify:

### Fixed Elements (Boilerplate)
- Output format templates
- Section headers
- Standard instructions
- Safety boilerplate (file error workarounds, parallel swarm awareness)

### Variable Elements
- Topic/subject (what `$ARGUMENTS` would replace)
- Input file paths
- Output file paths/names
- Domain-specific content

### Workflow Characteristics
- **Research/reading**: Searches web, reads many files, investigates
- **Implementation**: Modifies code, creates/edits files
- **Audit/review**: Reads code, produces reports
- **Commit/deploy**: Git operations, side effects

## Step 4: Determine Frontmatter

Based on analysis, select appropriate settings:

### Context & Agent
```yaml
# If the skill reads many files or does web research:
context: fork
agent: general-purpose

# If the skill is simple/linear with few file reads:
# (omit context - defaults to inline)
```

### Model Invocation
```yaml
# If skill has side effects (commits, edits code, deploys):
disable-model-invocation: true

# If skill is read-only or research:
# (omit - allows external model calls)
```

### Tool Restrictions
```yaml
# Read-only research/analysis:
allowed-tools: Read, WebSearch, WebFetch, Glob, Grep

# File creation without code modification:
allowed-tools: Read, Write, Bash(mkdir:*), Bash(mv:*), Bash(rm:*), Bash(ls:*)

# Full implementation work:
# (omit - allows all tools)
```

### Name & Description
```yaml
name: [derived-from-content-or-explicit]
description: [One sentence describing what skill does and when to use it]
argument-hint: [what arguments look like]
```

## Step 5: Generate Skill Content

Create the SKILL.md with:

1. **YAML frontmatter** (determined above)

2. **Title**: `# [Skill Name]: $ARGUMENTS`

3. **Objective section**: What the skill accomplishes

4. **Steps**: Numbered steps extracted from prompts, generalized:
   - Replace hardcoded values with `$ARGUMENTS` or parameters
   - Keep structural instructions
   - Include decision trees where appropriate

5. **Output format**: Template for results

6. **Safety boilerplate** (ALWAYS include):
```markdown
---

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents. NEVER use git restore/checkout/reset/clean.

---
```

7. **Completion instructions**:
```markdown
## Completion

When done, reply ONLY:
\`\`\`
Done - [brief description of output location]
\`\`\`

Do NOT:
- Output findings to conversation
- Modify files outside scope
- Leave temporary files behind
```

## Step 6: Determine Location

```bash
# Project-specific (default)
mkdir -p "./.claude/skills/[skill-name]"
# Output: ./.claude/skills/[skill-name]/SKILL.md

# Global (if --global flag)
mkdir -p "~/.claude/skills/[skill-name]"
# Output: ~/.claude/skills/[skill-name]/SKILL.md
```

## Step 7: Write Skill File

Write the generated SKILL.md to the appropriate location.

## Step 8: Show Summary

Present to user:

```markdown
## Skill Created

**Name:** [skill-name]
**Location:** [path to SKILL.md]
**Description:** [description]

### Frontmatter Settings
- context: [value or "default (inline)"]
- agent: [value or "default"]
- disable-model-invocation: [true/false]
- allowed-tools: [list or "all"]

### Pattern Analysis
**Fixed elements:** [what stays constant]
**Variable elements:** [what $ARGUMENTS replaces]
**Source prompts:** [list of files analyzed]

### Usage
```
/[skill-name] [example-arguments]
```

**Confirm creation? [Y/n]**
```

Wait for user confirmation before finalizing. If user says no or requests changes, iterate.

---

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. Prefer your file editing tools over shell text manipulation (cat, sed, echo)
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents. NEVER use git restore/checkout/reset/clean.

---

## Completion

When user confirms, reply:
```
Done - created [path to SKILL.md]
```

Do NOT:
- Create skills without showing summary first
- Overwrite existing skills without warning
- Create documentation files beyond SKILL.md
