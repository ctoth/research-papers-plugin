---
name: research
description: Research a topic using web search and create structured findings. Use when you need to investigate approaches, find papers, compare implementations, or gather knowledge on a topic. Creates structured notes in reports/ directory.
argument-hint: [topic]
context: fork
agent: general-purpose
---

# Research: $ARGUMENTS

Research a topic and create comprehensive implementation-focused findings.

## Objective

Conduct web-based research on **$ARGUMENTS** to answer:
1. What approaches/systems exist?
2. What papers describe them?
3. What are the tradeoffs (complexity vs quality)?
4. What implementations exist?
5. What's the recommended approach for this project?

## Research Methods

Search the web to find:
- Academic papers and key authors
- Documentation and specifications
- Open-source implementations
- Comparison studies

Fetch and read these pages to:
- Read paper abstracts/summaries
- Extract key information from documentation
- Check implementation details

## Output Format

Write findings to `./reports/research-$ARGUMENTS.md`:

```markdown
# Research: $ARGUMENTS

## Summary
[One paragraph overview of findings]

## Approaches Found

### [Approach 1 Name]
**Source:** [URL]
**Description:** [What it is]
**Pros:** [Advantages]
**Cons:** [Disadvantages]
**Complexity:** [Low/Medium/High]

[Repeat for each major approach]

## Key Papers
- [Author (Year)](URL) - [What it contributes]
- [Author (Year)](URL) - [What it contributes]

## Existing Implementations
- **[Name]** ([URL]): [Description, language, license]

## Complexity vs Quality Tradeoffs
[Analysis of what level of complexity gets what level of quality]

## Recommendations
[Specific recommendations for this project's research area]

## Estimated Implementation Effort
- **Minimal approach:** [What you get]
- **Full approach:** [What you get]

## Open Questions
- [ ] [Unresolved question]
- [ ] [Area needing more investigation]

## References
- [Full citation with URL]
```

---

## CRITICAL: File Modified Error Workaround

If Edit/Write fails with "file unexpectedly modified":
1. Read the file again
2. Retry the Edit
3. Try path formats: `./relative`, `C:/forward/slashes`, `C:\back\slashes`
4. NEVER use cat, sed, echo - always Read/Edit/Write
5. If all formats fail, STOP and report

## CRITICAL: Parallel Swarm Awareness

You may be running alongside other agents. NEVER use git restore/checkout/reset/clean.

---

## Completion

When done, reply ONLY:
```
Done - see reports/research-$ARGUMENTS.md
```

Do NOT:
- Output findings to conversation
- Read project source files (unless topic requires it)
- Modify any other files
