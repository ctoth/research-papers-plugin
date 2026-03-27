---
name: register-concepts
description: Register concepts needed by a paper into the propstore concept registry. Reads notes.md, identifies concepts, checks the registry for existing matches, and registers missing ones via pks. Also identifies and creates the paper's context if needed.
argument-hint: "<papers/Author_Year_Title>"
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI."
---

# Register Concepts: $ARGUMENTS

Register all concepts needed by a paper into the propstore concept registry, and identify the paper's context. This must run before extract-claims or enrich-claims.

## Step 0: Validate

```bash
paper_dir="$ARGUMENTS"
ls "$paper_dir"/notes.md 2>/dev/null || echo "MISSING: notes.md"
```

If `notes.md` is missing, STOP. Run paper-reader first.

## Step 1: Check for Propstore

```bash
ls concepts/*.yaml 2>/dev/null || ls knowledge/concepts/*.yaml 2>/dev/null
```

If no concepts directory exists → STOP. Report: "No propstore found. Run `pks init` first, or skip concept registration — claims can use descriptive lowercase_underscore names without a registry."

## Step 2: Read the Registry

```bash
ls knowledge/concepts/*.yaml 2>/dev/null | head -100
```

Read several concept files to understand what's already registered — their names, aliases, definitions, and forms. Build a mental model of the existing vocabulary before proceeding.

### Step 2a: Read form definitions

```bash
pks form list
```

This shows all forms with their units. For each concept you plan to register, the form must match the physical quantity. Example: if concept22 has form "charge" with unit "C", do NOT reuse it for a position variable "q" which should have form "distance" with unit "m". A symbol match is not a concept match — dimensional consistency is what matters.

### Step 2b: Load category vocabulary

```bash
pks concept categories
```

This lists registered category concepts and their allowed values. When the paper uses a value not in an existing set, register it:

```bash
pks concept add-value <concept_name> --value "<new_value>"
```

If no category concepts exist yet, skip — vocabulary will be free-form.

### Step 2c: Read existing claims for context

```bash
ls knowledge/claims/*.yaml 2>/dev/null | head -100
```

Skim existing claim files to understand what concepts are already in use. This prevents duplicate concept registration and helps reuse existing vocabulary.

## Step 3: Identify Concepts This Paper Needs

Read the paper's `notes.md`. List every distinct concept the paper discusses:
- Methods and algorithms (e.g., "dense video captioning", "MapReduce decomposition")
- Metrics and evaluation criteria (e.g., "CIDEr score", "caption quality")
- Architectures and components (e.g., "temporal tokenizer", "memory bank")
- Phenomena and properties (e.g., "temporal bias", "frame redundancy")
- CEL condition variables (e.g., "dataset", "model", "task") — these need category concepts

For each concept, check: does it already exist in the registry (by canonical_name or alias)?

## Step 4: Register Missing Concepts

For each concept NOT already in the registry:

```bash
pks concept add --name <lowercase_underscore_name> \
  --domain <project-domain> \
  --form structural \
  --definition "<1-2 sentence definition>"
```

**Definition quality is critical.** Definitions are used for concept embeddings and deduplication. Write a definition that:
- Distinguishes this concept from near-neighbors
- Would make sense to someone unfamiliar with this specific paper
- Is specific enough to match against similar concepts in other papers

Good: "The task of generating natural language descriptions for all events in a video, each anchored to a temporal interval"
Bad: "Video captioning method"

**Form selection:**
- `structural` for methods, architectures, phenomena, abstract concepts (most things)
- `category` for condition variables that take enumerated values (dataset, model, task, metric)
- `score` for evaluation metrics with numeric values (CIDEr, BLEU, mAP)
- `count` for discrete quantities (frame counts, segment counts)
- `rate` for rates (fps, words per minute)
- `time` for durations
- `ratio` for dimensionless ratios (hazard ratios, odds ratios, relative risks)

**CEL condition concepts** — commonly needed:
```bash
# Only create if they don't already exist
pks concept add --name dataset --domain general --form category \
  --values "value1,value2" \
  --definition "The benchmark dataset a result was evaluated on"
```

### Concept disambiguation

When a name could match multiple existing concepts, check:
- What are the dimensions/units this concept needs?
- Does the definition match?
- If unsure, register a NEW concept — deduplication happens later via embedding similarity

### Reusing existing concepts

- Search by name AND by reading definitions — a paper might call something "temporally-grounded captioning" but the registry has "dense_video_captioning" with a matching definition
- If you find a match, do NOT create a duplicate
- If unsure, create the new one

## Step 5: Context Identification

Identify which theoretical tradition or framework this paper belongs to.

1. Read the paper's "Arguments Against Prior Work" and "Design Rationale" sections in notes.md
2. Check existing contexts:
   ```bash
   ls knowledge/contexts/*.yaml 2>/dev/null
   ```
3. If the tradition matches an existing context, note it for claim extraction
4. If the tradition is NEW and clearly distinct:
   ```bash
   pks context add --name ctx_<tradition> --description "<1-2 sentence description>"
   ```
   If it refines an existing tradition:
   ```bash
   pks context add --name ctx_<tradition> --description "<description>" --inherits ctx_<parent>
   ```
5. If the paper is cross-cutting or the tradition is unclear: no context. Claims without a context are universal — visible in all contexts. This is the conservative default.

**Context naming:** `ctx_` prefix + lowercase_underscore (e.g., `ctx_atms_tradition`, `ctx_aspirin_primary_prevention`).

**Expected frequency:** ~1 new context per 3-4 papers. Most papers slot into existing traditions.

## Output

```
Concepts registered for: papers/[dirname]
  Existing concepts reused: N
  New concepts registered: N (list names)
  Category values added: N
  Context: [context_id or "universal (no context assigned)"]
```
