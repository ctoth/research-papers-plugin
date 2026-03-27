# Provenance & Justification Extraction Design Notes

## 2026-03-27

### Completed work
- stamp_provenance.py committed (4d4e0ac) — 10/10 tests pass
- Wired into 4 skills: paper-reader, extract-claims, extract-stances, enrich-claims (9236b89)
- extract-justifications skill created (8cdfa55), then simplified to remove prescriptive section guidance (e5a9d32)

### Current state: Research phase under foreman protocol
Q wants to use propstore's existing paper collection (~110 papers on argumentation, KR, reasoning) to inform:
1. Whether propstore's ontology is missing entities (rules? norms? verification criteria?)
2. Whether our 7 rule_kinds are adequate (Walton catalogs ~60 argumentation schemes)
3. How to generalize beyond paper-shaped knowledge (prescriptive rules, decision procedures, etc.)

### Key papers in propstore (have notes.md, no claims yet except Dung):
- **Walton 2015** — Classification system of argumentation schemes (THE taxonomy)
- **Prakken 2013** — Formalizes Walton's schemes in ASPIC+
- **Modgil & Prakken 2014/2018** — ASPIC+ framework
- **Wei 2012** — Defining structure of arguments
- **Dauphin 2018** — ASPIC-END (extends ASPIC+ with explanations)
- **Prakken 2010** — Abstract framework for structured argumentation
- **Dung 1995** — Foundation (has claims)

### 2026-03-27: Scout report received (reports/scout-argumentation-ontology.md)

Read 11 papers. Key findings:

**Walton's ~28 schemes (from 60+ total) vs our 7 rule_kinds:**
- Our 7 are science-shaped only. Entire branches unrepresented: source-based (expert opinion, witness testimony), practical reasoning (goal-directed, value-based), abductive (inference to best explanation), commitment-based.
- Scout recommends adding at minimum: `expert_testimony`, `abductive_inference`.
- Scout recommends NOT adding practical reasoning (wrong domain for now).

**ASPIC+ entity gaps in propstore:**
1. **Strict vs defeasible rules** — most impactful single missing distinction. Definition_application should be strict; empirical_support should be defeasible. Currently all justifications are implicitly defeasible.
2. **Necessary vs ordinary premises** — axioms (can't be attacked) vs ordinary claims (can be undermined). Propstore treats all claims uniformly.
3. **Named justifications** — ASPIC+ naming function lets undercuts target specific inference steps. Currently undercuts target claims, not justifications. If claim C has justifications J1 and J2, can't undercut J1 without affecting J2.
4. **Recursive argument trees** — ASPIC+ arguments are recursive (subarguments). Our CanonicalJustification is flat.
5. **Accrual** — multiple arguments for same conclusion accumulate. No formal treatment.
6. **Preferences/orderings** — explicit rule/premise orderings for comparing argument strength.

**Prakken's recipe for formalizing schemes:**
- Walton schemes → defeasible rules in ASPIC+
- Critical questions → three attack types (undermining, rebutting, undercutting)
- Requires: named rules, explicit predicates (not free text), factor hierarchies

**Scout's top recommendations:**
1. Add strict/defeasible distinction to justifications (highest impact)
2. Add necessary/ordinary distinction to claims
3. Add expert_testimony + abductive_inference rule_kinds
4. Consider named justifications for targeted undercutting
5. Do NOT add practical reasoning yet
6. Do NOT attempt full ASPIC+ implementation

### 2026-03-27: Propstore internals scouted (reports/scout-propstore-justification-internals.md)

Key findings from propstore codebase:
- **No justification table** in SQLite. Justifications are ephemeral, derived in-memory.
- **import_papers reads only claims.yaml** per paper. No stance files, no justification files.
- **Undercuts can't target specific justifications** — resolves by claim_id, hits all inference-rule arguments for a claim.
- **Multi-premise justifications structurally supported** in the builder (Cartesian product over premise groups) but **never created** by existing code.
- **aspic.py is fully implemented** (948 lines, Defs 1-22) but **has no bridge** to propstore's claim/stance data model. Standalone formal engine.
- **LinkML schema has no Justification class.**

### 2026-03-27: Proposal committed to propstore (dec9a0f)

`propstore/proposals/first-class-justifications.md` covers:
- Justification as stored entity (SQLite table + LinkML schema)
- 12 rule_kinds (7 original + reported_claim, support, explanation, expert_testimony, abductive_inference)
- rule_strength: strict vs defeasible (ASPIC+ Rs/Rd)
- Targeted undercutting via justification IDs
- premise_kind on claims: necessary vs ordinary (ASPIC+ Kn/Kp)
- Import pipeline extension to read justifications.yaml
- 7-step implementation order

### Still open
- Update extract-justifications skill to emit rule_strength
- Broader knowledge-shape research (prescriptive/procedural knowledge beyond papers)
- ASPIC+ bridge from stored justifications to aspic.py
