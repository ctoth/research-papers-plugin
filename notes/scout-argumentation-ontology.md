# Scout: Argumentation Ontology

## 2026-03-27 — Checkpoint 1: Priority 1 + Priority 2 papers read

### GOAL
Read propstore paper notes to report on argumentation schemes, ASPIC+ entity types, Prakken's formalization, and gaps in propstore's current ontology.

### DONE
- Read Walton 2015 notes: ~28 schemes in hierarchical taxonomy. 4 top-level categories: source-based, source-independent epistemic, practical reasoning, applying rules to cases. Each scheme has premise-conclusion structure + critical questions.
- Read Prakken 2013 notes: Formalizes 6 CATO-style legal case-based argumentation schemes (CS1-CS4, U1.1, U2.1 etc.) inside ASPIC+. Schemes become defeasible rules. Critical questions become undercutters/rebutters.
- Read Modgil 2014 notes (full): ASPIC+ core entity types: logical language L, strict rules Rs, defeasible rules Rd, naming function n, knowledge base K (Kn axioms + Kp ordinary premises), arguments (recursive from premises+rules), three attack types (undermining, rebutting, undercutting), preference-based defeat, structured argumentation framework. Argument properties: strict/defeasible, firm/plausible. Walton schemes modeled as defeasible rules; critical questions map to 3 attack types.
- Read Modgil 2018 notes (partial): Revised ASPIC+ with attack-based conflict-free, contrariness function, reasonable orderings, proves rationality postulates.
- Read Wei 2012 notes: Distinguishes argument types (unit, linked, multiple) from argument structures (serial, divergent, mixed). Eliminates need for "hybrid" category.
- Read Dauphin 2018 notes: ASPIC-END adds intuitively strict rules (middle tier between strict/defeasible), hypothetical arguments, explanation relations between arguments.
- Read Prakken 2010 notes (partial): Original ASPIC. 4 premise types: axioms Kn, ordinary Kp, assumptions Ka, issues Ki.

### KEY FINDINGS SO FAR

**ASPIC+ entity types (not in propstore):**
1. Strict rules (cannot be attacked)
2. Defeasible rules (can be undercut)
3. Necessary premises / axioms (cannot be attacked)
4. Ordinary premises (can be undermined)
5. Assumptions (Prakken 2010 adds Ka)
6. Issues (Prakken 2010 adds Ki)
7. Arguments (recursive trees of premises + rule applications)
8. Naming function for defeasible rules (enables undercutting)
9. Contrariness function (asymmetric conflict)
10. Preference orderings on rules and premises

**Walton's ~28 schemes vs propstore's 7 rule_kinds:**
- Propstore's 7: empirical_support, causal_explanation, methodological_inference, statistical_inference, definition_application, scope_limitation, comparison_based_inference
- Walton's categories that DON'T map: source-based (expert opinion, witness testimony, position to know), practical reasoning (goal-directed, value-based, sunk cost), ad hominem, argument from ignorance, argument from best explanation (abductive), argument from sign, argument from precedent, argument from analogy

**How schemes formalize in ASPIC+:**
- Schemes = defeasible inference rules
- Critical questions = three attack types (undermining premises, rebutting conclusions, undercutting inference steps)
- Modgil 2014 p.50-53: explicit walkthrough of position-to-know scheme

### NEXT
- Done. Report written to reports/scout-argumentation-ontology.md

### PROPSTORE CURRENT STATE (verified from source)
- 9 claim types: parameter, equation, observation, model, measurement, algorithm, mechanism, comparison, limitation
- 7 stance types: rebuts, undercuts, undermines, supports, explains, supersedes, none
- 7 rule_kinds: empirical_support, causal_explanation, methodological_inference, statistical_inference, definition_application, scope_limitation, comparison_based_inference
- CanonicalJustification: conclusion_claim_id + premise_claim_ids + rule_kind (flat, not recursive)
