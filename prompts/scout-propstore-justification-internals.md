# Scout: Propstore Justification & Argument Internals

## Objective

Read propstore's current implementation of justifications, structured arguments, and the import pipeline. Report what exists so we can write a concrete spec for making justifications a first-class stored entity type.

## What to Read

All files live in `C:/Users/Q/code/propstore/`.

**Core justification/argument code:**
- `propstore/core/justifications.py` — CanonicalJustification definition and derivation
- `propstore/structured_argument.py` — StructuredArgument, how arguments are built from justifications
- `propstore/argumentation.py` — how stances become defeats, the argumentation framework

**Import pipeline:**
- `propstore/cli/compiler_cmds.py` — `import_papers()` function specifically
- `propstore/build_sidecar.py` — SQLite compilation, what tables exist

**Schema:**
- `schema/claim.linkml.yaml` or any LinkML schema files — what's formally defined
- Any migration files or table definitions

**ASPIC+ bridge:**
- `propstore/aspic.py` — current ASPIC+ implementation

**Also check:**
- `propstore/core/graph_types.py` — ProvenanceRecord, other core types
- Any existing `justification` table in the SQLite schema
- How `undercuts` stance type is currently resolved — does it target claims or justifications?

## Questions to Answer

1. **How are CanonicalJustifications currently created?** What code derives them from claims+stances? What fields do they carry?

2. **Are justifications stored in SQLite?** Is there a justification table, or are they only in-memory at query time?

3. **How does import_papers work?** What files does it read per paper directory? How does it resolve cross-paper references? What would need to change to also read `justifications.yaml`?

4. **How does the undercuts stance currently resolve?** Does it target a claim or a justification? How would targeted undercutting of a specific justification work?

5. **What does the StructuredArgument builder assume about justification structure?** Is it flat (one level) or does it handle chaining?

6. **What SQLite tables exist in the sidecar?** List them with their key columns.

7. **What's in aspic.py?** How much of ASPIC+ is actually implemented vs stubbed?

## Output

Write your report to `C:/Users/Q/code/research-papers-plugin/reports/scout-propstore-justification-internals.md`.

Be specific. Quote function signatures, class definitions, SQL schemas. Include file paths and line numbers. This report will be the basis for a concrete proposal — vague descriptions are useless.
