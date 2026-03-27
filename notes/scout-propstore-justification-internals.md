# Scout: Propstore Justification Internals

## 2026-03-27 — Initial read pass

**GOAL:** Read propstore's justification/argument/import internals, answer 7 questions, write report.

**DONE:**
- Read `propstore/core/justifications.py` — CanonicalJustification is a frozen dataclass with fields: justification_id, conclusion_claim_id, premise_claim_ids, rule_kind, provenance, attributes. Created by `claim_justifications_from_active_graph()` which generates "reported:" justifications for each active claim, plus "supports:"/"explains:" justifications from relations.
- Read `propstore/structured_argument.py` — StructuredArgument built from justifications. `build_structured_projection()` is the main entry. Two-phase: first creates base args from reported_claim justifications, then iteratively builds derived args from justifications with premises (fixpoint loop with `product(*premise_groups)`). Handles chaining via the while-changed loop.
- Read `propstore/argumentation.py` — Claim-graph AF backend. Defines attack/support type sets. `_ATTACK_TYPES = {rebuts, undercuts, undermines, supersedes}`. `undercuts` is in `_UNCONDITIONAL_TYPES`. The `_target_argument_ids` function in structured_argument.py shows undercuts targets arguments where `argument.claim_id == target_claim_id and argument.attackable_kind == "inference_rule"` — so it targets inference-rule arguments by claim_id, NOT by justification_id.
- Read `propstore/core/graph_types.py` — ProvenanceRecord, ClaimNode, RelationEdge, CompiledWorldGraph, ActiveWorldGraph. No justification type here.
- Read `propstore/aspic.py` (first 100 lines) — Implements Literal, ContrarinessFn from Modgil & Prakken 2018 Def 1-2. Leaf module with zero propstore imports.
- Read `propstore/build_sidecar.py` (first 100 lines) — Tables mentioned in docstring: concept, alias, relationship, parameterization, FTS5, claim, conflicts, claim FTS5. No justification table mentioned.
- Found `import_papers` at line 415 of compiler_cmds.py — haven't read it yet.
- Found LinkML schemas: `schema/claim.linkml.yaml`, `schema/concept_registry.linkml.yaml`.

**COMPLETE.** Report written to `reports/scout-propstore-justification-internals.md`.

Key findings: justifications are ephemeral (no table, no file), undercuts can't target specific justifications, ASPIC+ engine is complete but unconnected to claim data model, import_papers reads only claims.yaml per paper dir.
