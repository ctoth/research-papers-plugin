---
name: adjudicate
description: Systematically adjudicate disagreements across a paper collection. Produces ruthless verdicts on who was wrong, what supersedes what, and what the best current understanding is. Organized by topic clusters with actionable replacement values for implementation.
argument-hint: "[topic-scope or --all]"
context: fork
agent: general-purpose
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Adjudicate: $ARGUMENTS

Systematically adjudicate disagreements across the paper collection. Not summaries — *judgments*.

## Step 0: Parse Arguments

- If `$ARGUMENTS` is `--all`: full collection sweep — discover topics, assign papers, produce all verdicts
- If `$ARGUMENTS` is a topic name (e.g., "vowel formants"): produce a single verdict for that topic
- If `$ARGUMENTS` is a list of paper directories: adjudicate only the disagreements among those specific papers

## Step 1: Scope the Collection

```bash
ls -d papers/*/ | grep -v "papers/pngs" | wc -l
ls papers/*/notes.md | wc -l
```

Read `papers/index.md` (if it exists) or sample `papers/*/description.md` files to understand what topics the collection covers.

Check for existing verdicts:
```bash
ls research/verdicts/*.md 2>/dev/null
```

## Step 2: Discover Topic Clusters

For `--all` mode, identify natural topic clusters where papers make overlapping claims. Scan description.md files and notes.md cross-reference sections to find areas of disagreement.

**Standard topic areas** (adapt to collection):
- Source/generation models
- Target values (formants, spectra, durations, etc.)
- Dynamic phenomena (coarticulation, transitions, temporal patterns)
- Higher-level organization (prosody, phrase structure)
- Speaker variation (gender, age, style)
- Perceptual correlates

For single-topic mode, skip this step — use the provided topic.

## Step 3: Assign Papers to Topics

For each topic, identify the specific paper directories whose notes.md must be read. A paper can belong to multiple topics.

```bash
# Example: find papers relevant to "vowel formants"
grep -rl "formant" papers/*/notes.md --include="notes.md" | head -30
```

Write the assignment to `reports/paper-topic-assignment.md`:
```markdown
## Topic: [Name]
Papers to read:
- papers/Author_Year_Title/
- papers/Author_Year_Title/
[...]
Estimated scope: N papers, ~M lines of notes
```

## Step 4: Produce Verdicts

For each topic, read ALL assigned notes.md files and render a verdict.

### Decision Rubric

Apply this hierarchy by default. Override with explicit reasoning only.

**Evidence hierarchy (higher beats lower):**
1. Multiple independent empirical replications > single study
2. Direct acoustic/physiological measurement > derived/computed value
3. Larger sample (N>50) > smaller sample (N<10)
4. Modern measurement technology > older (LPC > spectrograph, EGG > indirect estimation)
5. Controlled lab conditions > naturalistic observation (for baseline values)
6. Naturalistic observation > controlled conditions (for ecological validity)
7. Theory with empirical validation > theory without
8. Original paper with published errata/corrections > uncorrected original

**Override permitted when:**
- The older study controlled for a variable the newer one didn't
- The newer study measured a fundamentally different population/context
- Sample size difference is small and the smaller study had better methodology
- A foundational theoretical framework remains correct despite age because the physics hasn't changed

### Four Categories of "Wrong"

Every finding of error gets one of these labels:

1. **WRONG** — Methodology error, logical flaw, or measurement artifact. The finding was incorrect even for its original scope.
2. **SUPERSEDED** — Correct at the time, better data replaced it. Not the authors' fault.
3. **LIMITED** — Correct for its specific population/context but not generalizable as broadly as applied.
4. **INCOMPARABLE** — Papers appear to disagree but measured different things. Apples-to-oranges.

### Verdict Document Template

Write each verdict to `research/verdicts/NN-topic-name.md`:

```markdown
# Verdict: [Topic]

## Papers Considered
[Exact folder names for traceability]

## Historical Timeline
[Who said what, when — chronological. The story of the field.]

## Findings by Category

### Wrong (methodology error or flawed reasoning)
[Each: paper, claim, what was wrong, evidence. Label: WRONG]

### Superseded (better data replaced it)
[Each: old paper/claim → new paper/claim, why new wins. Label: SUPERSEDED]

### Limited (correct but over-applied)
[Each: paper, claim, valid scope, where it breaks down. Label: LIMITED]

### Incomparable (different questions mistaken for disagreement)
[Each: the two papers, what each actually measured, why comparison is invalid. Label: INCOMPARABLE]

## What Subsumes What
[Broader theories encompassing narrower ones. The intellectual genealogy.]

## Genuinely Uncertain
[Active disagreements with no resolution. The honest "we don't know."]

## Best Current Understanding
[The verdict. For each sub-question: answer, evidence, confidence (high/medium/low).]

## Synthesizer Audit
[What the implementation currently uses vs what it should use.
Each entry: current value (file:line) + source paper → category (correct/WRONG/SUPERSEDED/LIMITED) → replacement value with source paper.
Include actual numbers ready to implement.]

## Open Questions
[What the collection can't answer. Gaps. Papers we'd need to acquire.]
```

### Tone

Ruthless. If the evidence says a paper was wrong, say it plainly. No hedging, no "may have been superseded." Name names, cite evidence, render judgment.

"Peterson & Barney's F3 values for children were WRONG — Hillenbrand 1995 showed they were 174 Hz too high, likely due to spectrograph limitations."

Not: "Later work found somewhat different values."

### Actionability

Every Synthesizer Audit entry that recommends a change must include the actual replacement values. "Replace IY1 F1=270 with F1=342 per Hillenbrand 1995 Table III" — not just "consider updating."

### Gap Filling

If a critical missing paper would change the verdict, use the paper-process skill to acquire it:
```
Use the paper-process skill to retrieve and process: [citation or DOI]
```

If nested skill invocation is unavailable or unreliable on this platform, derive this skill's
installed directory from the injected `<path>`, then run:

```bash
python "<skill-dir>/../paper-process/scripts/emit_nested_process_fallback.py"
```

Read the FULL stdout and follow it exactly instead of opening `paper-process/SKILL.md` piecemeal.

A verdict rendered without key evidence is worse than a slower verdict.

## Step 5: Wave Ordering (for --all mode)

Topics have soft dependencies. Process in waves:

**Wave 1 — Foundations (parallel):** Topics about fundamental models, baseline measurements, and architectural assumptions. No topic depends on another within this wave.

**Wave 2 — Dynamics (parallel):** Topics about time-varying phenomena (coarticulation, duration, prosody). May reference Wave 1 verdicts.

**Wave 3 — Higher-level (parallel):** Topics about speaker variation, emotion, style. May reference Wave 1 and 2 verdicts.

**Wave 4 — Master synthesis (sequential):** One pass reading all verdicts, producing `research/verdicts/00-master-synthesis.md`:
- Cross-topic interactions and contradictions
- Priority-ordered list of implementation changes needed
- Confidence map: what's solid ground, what's quicksand
- Papers the collection still needs

## Step 6: Notes and Progress

Create `research/verdicts/notes-progress.md` and update it after each verdict:
- What was adjudicated
- Surprises and course corrections
- Running tally of WRONG/SUPERSEDED/LIMITED/INCOMPARABLE findings

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

When done, reply ONLY:
```
Done - see research/verdicts/
  Verdicts: [list of verdict files]
  Master synthesis: research/verdicts/00-master-synthesis.md
  Findings: X WRONG, Y SUPERSEDED, Z LIMITED, W INCOMPARABLE
  Gaps: N papers flagged for acquisition
```

Do NOT:
- Output full verdict content to conversation
- Modify paper notes.md files (verdicts are separate documents)
- Skip the Synthesizer Audit section
- Use hedging language ("may", "possibly", "could be") in verdict conclusions
