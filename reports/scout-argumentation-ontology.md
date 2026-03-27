# Scout Report: Argumentation Ontology from Propstore Papers

Date: 2026-03-27

Papers read: Walton 2015, Prakken 2013, Modgil 2014, Modgil 2018, Wei 2012, Dauphin 2018, Prakken 2010, Dung 1995, Pollock 1987, Prakken 2019, Wallner 2024.

---

## 1. Walton's Argumentation Schemes

Walton & Macagno (2015) present a hierarchical taxonomy of approximately 28 argumentation schemes organized into a tree structure (Table 1 p.22, Figure 4 p.23). The foundational reference (Walton, Reed, & Macagno 2008, cited throughout) catalogs 60+ schemes; this paper classifies a representative subset.

### Top-Level Categories

The taxonomy has four top-level divisions (p.22):

1. **Source-Based Schemes** — argument strength depends on characteristics of the source
   - Arguments from position to know (expert opinion, witness testimony) *(p.10)*
   - Ad hominem arguments (direct, circumstantial, inconsistent commitment) *(p.11-12)*
   - Arguments from popular acceptance (popular opinion, popular practice) *(p.22)*

2. **Source-Independent Epistemic Schemes** — aimed at establishing truth independent of source
   - Discovery arguments (best explanation, ignorance, sign, gradualism) *(p.20-21)*
   - Chained arguments (precedent slippery slope, sorites, verbal classification) *(p.22)*
   - Applying rules to cases (cause to effect, established rule, evidence to hypothesis) *(p.17-19)*

3. **Practical Reasoning Schemes** — aimed at deciding what to do, not what is true
   - Instrumental practical reasoning (goal-directed action) *(p.16)*
   - Value-based practical reasoning (positive/negative consequences) *(p.16)*
   - Arguments from values, fairness, waste/sunk cost, threat *(p.13-14, p.22)*

4. **Applying Rules to Cases** — precedent, analogy, example *(p.17-19)*

### Mapping to Propstore's 7 rule_kinds

| Propstore rule_kind | Walton scheme coverage |
|---------------------|----------------------|
| `empirical_support` | Argument from sign (p.20), argument from evidence to hypothesis (p.22), argument from correlation to cause (p.20) |
| `causal_explanation` | Argument from cause to effect (p.17) |
| `methodological_inference` | No direct Walton equivalent — this is domain-specific to scientific methodology |
| `statistical_inference` | Argument from a random sample to a population (p.22) — partial overlap |
| `definition_application` | Argument from verbal classification (p.22), argument from established rule (p.17) |
| `scope_limitation` | No Walton equivalent — Walton does not have a "limiting" scheme category |
| `comparison_based_inference` | Argument from analogy (p.19), argument from precedent (p.18), argument from example (p.21) |

**Walton schemes with NO propstore rule_kind:**

- All source-based schemes: expert opinion, position to know, witness testimony, ad hominem variants *(p.10-12)*
- All practical reasoning schemes: goal-directed, value-based, sunk cost, threat, consequences *(p.13-16)*
- Abductive reasoning: argument from best explanation *(p.20)*
- Argument from ignorance / lack of evidence *(p.21)*
- Arguments from commitment and inconsistent commitment *(p.11, p.15)*
- Arguments from popular acceptance *(p.22)*

The mismatch is structural: propstore's rule_kinds cover scientific/empirical inference patterns, while Walton's schemes cover the full range of human argumentation including source-dependent, practical, and dialectical reasoning.

---

## 2. ASPIC+ Entity Types

The ASPIC+ framework (Modgil & Prakken 2014, formalized in Modgil & Prakken 2018) defines the following core entity types:

### Argumentation System

An argumentation system is a tuple AS = (L, R, n) where (Modgil 2014 p.35):
- **L** — a logical language closed under negation (or a contrariness function in the general version)
- **R = Rs union Rd** — inference rules partitioned into:
  - **Strict rules (Rs)**: `phi_1, ..., phi_n -> phi` — if antecedents hold, consequent holds without exception *(p.35)*
  - **Defeasible rules (Rd)**: `phi_1, ..., phi_n => phi` — if antecedents hold, consequent presumably holds *(p.35)*
- **n: Rd -> L** — a naming function that assigns each defeasible rule a formula in L, enabling undercutting attacks *(p.35)*

### Knowledge Base

A knowledge base K is partitioned into (Modgil 2014 p.35, Prakken 2010 expands):
- **Kn (necessary premises / axioms)** — cannot be attacked *(p.35)*
- **Kp (ordinary premises)** — can be undermined *(p.35)*
- **Ka (assumptions)** — can be attacked (Prakken 2010 only) *(Prakken 2010 p.55-56)*
- **Ki (issues)** — open questions (Prakken 2010 only) *(Prakken 2010 p.55-56)*

### Arguments

Arguments are recursive inference trees (Modgil 2014 p.36-37):
- Base case: a premise from K
- Inductive case: apply a strict or defeasible rule to conclusions of existing arguments
- Each argument has: Prem(A), Conc(A), Sub(A), DefRules(A), TopRule(A)

Argument properties (p.37):
- **strict** — uses no defeasible rules
- **defeasible** — uses at least one defeasible rule
- **firm** — all premises are axioms
- **plausible** — at least one premise is ordinary

### Attack Relations

Three types (Modgil 2014 p.38):
1. **Undermining** — conclusion of A negates an ordinary premise of B
2. **Rebutting** — conclusion of A negates a defeasibly-derived conclusion of B
3. **Undercutting** — conclusion of A negates the name of a defeasible rule used in B (attacks the inference step itself)

### Defeat

Attacks are filtered through preferences to produce defeats (p.39-40):
- Undermining and rebutting succeed as defeats only when the attacker is not strictly weaker
- **Undercutting always succeeds regardless of preferences** *(p.39-40)*

### Additional Entity Types from Extensions

- **Contrariness function** (Modgil 2018 p.8): allows asymmetric conflict (contraries vs contradictories), generalizing beyond classical negation
- **Intuitively strict rules** (Dauphin 2018 p.5): a middle tier between strict and defeasible — prima facie laws of logic that behave like strict rules but can be attacked
- **Explanation relation** (Dauphin 2018 p.3, p.8): from arguments to arguments or explananda, distinct from defeat
- **Accrual sets** (Prakken 2019 p.4): sets of same-conclusion arguments that together provide cumulative support
- **Value-based frameworks** (Wallner 2024 p.2-3): agent-specific value profiles that filter which premises and rules are available

---

## 3. Prakken's Formalization of Schemes in ASPIC+

### How Schemes Become Rules

Modgil & Prakken (2014 p.50-53) show the general recipe. Walton-style argumentation schemes are formalized as **defeasible inference rules** in ASPIC+:

> "ASPIC+ can model Walton-style argument schemes by: (1) Representing schemes as defeasible inference rules, (2) Representing critical questions as potential undercutters or rebutters, (3) Different types of critical questions map to different attack types" *(p.50-51)*

The position-to-know scheme is formalized with predicates `inPositionToKnow(s, p)`, `asserts(s, p)` as a defeasible rule producing the conclusion `p`. *(p.51)*

Three types of critical questions map to three attack types (p.51):
1. Questions that challenge assumptions/presumptions → **undermining attacks**
2. Questions that challenge the conclusion → **rebutting attacks**
3. Questions about exceptions to the scheme → **undercutting attacks**

### Legal Case-Based Reasoning (Prakken 2013)

Prakken et al. (2013) formalize six CATO-style legal argumentation schemes as ASPIC+ defeasible rules:

- **CS1**: Main plaintiff-side precedent scheme — if shared plaintiff factors preferred over defendant factors and precedent decided for plaintiff, then current case should also be decided for plaintiff *(p.13-14)*
- **CS2**: Derives the preference relation from the precedent itself *(p.15)*
- **CS3, CS4**: Supplementary schemes for unused current-case strengths *(p.16-18)*
- **U1.1, U2.1**: Undercutters capturing defendant distinctions *(p.14)*

The formalization requires (p.7-12):
- Explicit predicates for factors, factor sets, outcomes, and factor hierarchies
- Functions for computing factor partitions between current and precedent cases
- Named defeasible rules that can be undercut through ASPIC+'s naming mechanism
- Substitution and cancellation modeled through abstract-factor ancestry

The resulting argumentation theory satisfies ASPIC+'s rationality postulates (consistency and closure under strict rules) *(p.19-22)*.

### What This Requires as Entity Types

Formalizing schemes in ASPIC+ requires entities that propstore does not currently have:
1. **Named defeasible rules** with explicit antecedent-consequent structure
2. **A naming function** so that undercutting can target specific inference steps
3. **Predicates** (structured terms, not free-text statements)
4. **Strict rules** for definitional/logical relationships
5. **Factor hierarchies** or other domain ontologies that inference rules can reference

---

## 4. Knowledge Entity Gaps

What the literature defines that propstore does not have as entities:

### Strict vs Defeasible Rules

ASPIC+ makes a fundamental distinction between strict rules (cannot be attacked) and defeasible rules (can be undercut). Propstore has `CanonicalJustification` with a `rule_kind` field, but does not distinguish whether the inference is strict (definitional, logical) or defeasible (empirical, presumptive). Every justification in propstore is implicitly defeasible. *(Modgil 2014 p.35)*

### Necessary vs Ordinary Premises

ASPIC+ partitions the knowledge base into necessary premises (axioms, cannot be attacked) and ordinary premises (can be undermined). Propstore treats all claims uniformly — there is no mechanism to mark a claim as axiomatic/necessary vs. merely asserted. *(Modgil 2014 p.35)*

### Named Inference Rules

ASPIC+ assigns each defeasible rule a name via a naming function, enabling undercutting attacks that target specific inference steps. Propstore's `CanonicalJustification` has a `rule_kind` but no unique name for the specific rule instance. Undercutting in the stance vocabulary (`undercuts`) exists but cannot target a specific justification — it targets claims. *(Modgil 2014 p.35, p.38)*

### Arguments as Recursive Trees

ASPIC+ arguments are recursive trees of premises and rule applications, with explicit subargument structure (Sub(A), TopRule(A), DefRules(A)). Propstore's `CanonicalJustification` is flat: one conclusion, a list of premises, one rule_kind. There is no nesting — a justification cannot reference other justifications as subarguments. *(Modgil 2014 p.36-37)*

### Preferences / Orderings

ASPIC+ defines explicit preference orderings over rules and premises, with last-link and weakest-link principles for comparing argument strength. Propstore has no preference mechanism. *(Modgil 2014 p.42-44)*

### Contrariness Function

The general ASPIC+ framework uses a contrariness function that supports asymmetric conflict (A is contrary to B, but B is not contrary to A). Propstore's stance types are symmetric or untyped in this regard. *(Modgil 2018 p.8)*

### Explanation Relations

ASPIC-END (Dauphin 2018) adds an explanation relation distinct from attack/support. Propstore has `explains` as a stance type, which partially covers this, but ASPIC-END's explanations are between arguments (structured inference trees), not between flat claims. *(Dauphin 2018 p.3-4, p.8)*

### Accrual

Prakken (2019) formalizes how multiple arguments for the same conclusion provide cumulative support. Propstore has no accrual mechanism — multiple `supports` stances converge on a claim but there is no formal treatment of how they accumulate. *(Prakken 2019 p.1, p.4-6)*

### Values

Wallner et al. (2024) show how agent-specific values filter which premises and rules are available. Propstore has no value or agent model. *(Wallner 2024 p.2-3)*

---

## 5. Rule Kind Gaps

Specific argumentation schemes or inference patterns that propstore's 7 rule_kinds cannot represent:

### Source-Based Reasoning (Walton's entire source-dependent branch)

- **Argument from expert opinion**: "E is an expert in domain S; E asserts A; therefore A is plausible" *(Walton 2015 p.10)*
- **Argument from position to know**: "a is in a position to know about S; a asserts A; therefore A" *(p.10)*
- **Argument from witness testimony** *(p.22)*
- **Ad hominem** variants *(p.11-12)*

None of propstore's rule_kinds capture source-dependent reasoning. The closest is `empirical_support`, but that is about evidence, not about source credibility.

### Abductive Reasoning

- **Argument from best explanation**: "F is a set of facts; E explains F; no better explanation exists; therefore E is a hypothesis" *(Walton 2015 p.20)*

This is a distinct inference pattern (inference to the best explanation / abduction) not covered by any of the 7 rule_kinds.

### Practical Reasoning (Walton's entire practical branch)

- **Goal-directed practical reasoning**: "I have goal G; action A achieves G; therefore I ought to do A" *(p.16)*
- **Value-based practical reasoning**: "Value V is positive; if X occurs, it supports goal G; therefore V is reason for G" *(p.16)*
- **Argument from consequences** (positive/negative) *(p.16)*
- **Argument from waste / sunk cost** *(p.13-14)*

Propstore's rule_kinds are entirely epistemic — they address what is true, not what should be done. Practical reasoning is absent.

### Dialectical/Commitment-Based Reasoning

- **Argument from commitment**: "a was committed to A in the past; therefore a is still committed to A" *(p.15)*
- **Argument from inconsistent commitment** *(p.11)*

These track agent commitments over time, which propstore has no mechanism for.

### Presumptive Reasoning

- **Argument from ignorance**: "If A were true, A would be known; A is not known; therefore A is not true" *(p.21)*
- **Argument from sign**: "A is true in this situation; therefore B is true" *(p.20)*

These are defeasible presumptions distinct from empirical evidence.

### Case-Based / Precedent Reasoning

- **Argument from precedent**: "Precedent with features A,B,C led to Z; this case matches A,B,C; therefore Z" *(Walton 2015 p.18; Prakken 2013 p.13-14)*
- **Argument from example**: induction from a single case to a rule *(p.21)*

`comparison_based_inference` partially covers analogy but not the full precedent reasoning formalized in Prakken 2013 with factor partitions, substitutions, and cancellations.

### Undercutting as a Distinct Inference Pattern

Pollock (1987 p.485) distinguishes **rebutting defeaters** (reasons for denying the conclusion) from **undercutting defeaters** (reasons for denying the connection between reason and conclusion). ASPIC+ formalizes undercutting as a distinct attack type that always succeeds regardless of preferences (Modgil 2014 p.39-40). Propstore has `undercuts` as a stance type, which is correct, but the 7 rule_kinds do not include a rule_kind for constructing undercutting arguments — only for constructing positive inferences.

---

## 6. Recommendations

### 6.1 Add Strict vs Defeasible Distinction to Justifications

ASPIC+ fundamentally partitions rules into strict (definitional, logical, cannot be attacked) and defeasible (empirical, presumptive, can be undercut). Propstore's `CanonicalJustification` should carry a boolean or enum distinguishing these two categories. Definitional claims (`definition_application`) and mathematical derivations should be strict; empirical and statistical inferences should be defeasible. This is the single most impactful missing distinction per the literature.

**Source**: Modgil 2014 p.35: "The framework is based on two key ideas: (1) conflicts between arguments are often resolved with explicit preferences, and (2) some premises only create a presumption in favour of their conclusion — accordingly the framework distinguishes strict from defeasible rules."

### 6.2 Add Necessary vs Ordinary Premise Distinction to Claims

Claims should be markable as axioms/necessary (cannot be attacked) or ordinary (can be undermined). Mathematical definitions, established terminology, and logical tautologies should be necessary premises. Empirical observations and reported measurements should be ordinary premises.

**Source**: Modgil 2014 p.35, p.38: "an argument can only be attacked on sub-arguments that are ordinary premises or that have a defeasible top rule. A firm and strict argument has no attackers."

### 6.3 Expand rule_kinds for Source-Based and Abductive Reasoning

Add at minimum:
- `expert_testimony` — argument from expert opinion / position to know
- `abductive_inference` — argument from best explanation

These are the two most common inference patterns in scientific literature that the current 7 rule_kinds miss entirely. Scientific papers routinely cite authorities and propose explanatory hypotheses.

**Source**: Walton 2015 p.10 (expert opinion scheme), p.20 (best explanation scheme). The empirical study found argument from expert opinion among the most frequent scheme types in real discourse (p.7).

### 6.4 Consider Recursive/Nested Justifications

ASPIC+ arguments are recursive trees where subarguments can themselves be attacked. Propstore's flat `CanonicalJustification` (one conclusion, flat list of premises, one rule_kind) cannot represent chained reasoning where an intermediate conclusion is itself supported by another justification. This matters when an undercutting attack targets a specific step in a chain.

**Source**: Modgil 2014 p.36-37 (recursive argument construction), p.38 (attacks on subarguments propagate to containing argument).

### 6.5 Add Naming to Justifications for Targeted Undercutting

ASPIC+'s naming function allows undercutting attacks to target specific inference steps. Currently, propstore's `undercuts` stance targets claims, not justifications. If claim C has two independent justifications J1 and J2, an undercutting attack should be able to target J1 without affecting J2.

**Source**: Modgil 2014 p.35 (naming function), p.38 (undercutting attacks conclude the negation of a rule name).

### 6.6 Do NOT Add Practical Reasoning rule_kinds Yet

Walton's practical reasoning schemes (goal-directed, value-based, consequences) are important in legal and political argumentation but are rarely relevant in scientific literature. Propstore's current domain is scientific papers. Adding practical reasoning rule_kinds would expand the ontology without serving the current use case.

### 6.7 Do NOT Attempt Full ASPIC+ Implementation

The literature makes clear that ASPIC+ is a framework for building argumentation systems, not a system itself (Modgil 2014 p.57: "ASPIC+ deliberately leaves open the choice of logical language, inference rules, knowledge base contents, and preference ordering"). Propstore should adopt the useful distinctions (strict/defeasible, necessary/ordinary, named rules) without building a full ASPIC+ evaluator. The computational cost of generating all arguments from a rule set is acknowledged as potentially infinite (Modgil 2014 p.61, Note 2).
