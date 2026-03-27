# Scout: Argumentation Ontology from Propstore Papers

## Objective

Read the notes.md files from key papers in the propstore collection and report what the argumentation literature says about:

1. **Inference pattern types / argumentation schemes** — What taxonomy of inference patterns exists? How many schemes did Walton identify? What are the major categories? How do they compare to our current 7 rule_kinds (empirical_support, causal_explanation, methodological_inference, statistical_inference, definition_application, scope_limitation, comparison_based_inference)?

2. **Knowledge entities beyond claims** — Does the literature distinguish entity types beyond "claims" and "stances"? E.g., strict rules vs defeasible rules, norms vs descriptions, procedures vs assertions. What does ASPIC+ define as its core entity types?

3. **How schemes formalize in ASPIC+** — Prakken 2013 specifically formalizes Walton's schemes in ASPIC+. What does that formalization look like? What entity types does it require?

4. **Gaps** — Based on what you read, what is propstore likely missing? What categories of knowledge or reasoning can't be represented with: 9 claim types, 6 stance types, and CanonicalJustification (conclusion + premises + rule_kind)?

## Papers to read (in priority order)

All live in `C:/Users/Q/code/propstore/papers/`. Read the `notes.md` in each directory.

**Priority 1 (must read):**
- `Walton_2015_ClassificationSystemArgumentationSchemes/notes.md`
- `Prakken_2013_FormalisationArgumentationSchemesLegalCaseBasedReasoningASPICPlus/notes.md`
- `Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md`

**Priority 2 (read if priority 1 leaves gaps):**
- `Modgil_2018_GeneralAccountArgumentationPreferences/notes.md`
- `Wei_2012_DefiningStructureArgumentsAIModelsArgumentation/notes.md`
- `Dauphin_2018_ASPICENDStructuredArgumentationExplanationsNaturalDeduction/notes.md`
- `Prakken_2010_AbstractFrameworkArgumentationStructured/notes.md`

**Priority 3 (skim for relevant insights):**
- `Dung_1995_AcceptabilityArguments/notes.md` (also has claims.yaml)
- `Rahwan_2009_ArgumentationArtificialIntelligence/notes.md` (if it exists)
- `Pollock_1987_DefeasibleReasoning/notes.md`
- `Prakken_2019_ModellingAccrualArgumentsASPIC/notes.md`
- `Wallner_2024_ValueBasedReasoningInASPIC/notes.md`

## Output

Write your report to `reports/scout-argumentation-ontology.md` with these sections:

1. **Walton's Argumentation Schemes** — What are they, how many, what are the major categories, how do they map (or not) to our 7 rule_kinds?
2. **ASPIC+ Entity Types** — What entities does the framework define? (rules, literals, arguments, etc.) What's the distinction between strict and defeasible rules?
3. **Prakken's Formalization of Schemes** — How do argumentation schemes become ASPIC+ rules? What does this require?
4. **Knowledge Entity Gaps** — What the literature defines that propstore doesn't have as entities.
5. **Rule Kind Gaps** — Specific argumentation schemes or inference patterns that our 7 rule_kinds can't represent.
6. **Recommendations** — What should propstore add or change, grounded in what you read?

Be specific. Quote the papers. Cite page numbers. Do not theorize beyond what the notes contain.
