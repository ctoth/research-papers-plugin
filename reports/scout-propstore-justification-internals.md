# Scout Report: Propstore Justification & Argument Internals

**Date:** 2026-03-27
**Codebase:** `C:/Users/Q/code/propstore/`

---

## 1. How are CanonicalJustifications currently created?

**File:** `propstore/core/justifications.py`

The `CanonicalJustification` dataclass (line 24-64):

```python
@dataclass(frozen=True, order=True)
class CanonicalJustification:
    justification_id: str
    conclusion_claim_id: str
    premise_claim_ids: tuple[str, ...] = ()
    rule_kind: str = "reported_claim"
    provenance: ProvenanceRecord | None = None
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
```

Two creation paths exist:

**Path A — from ActiveWorldGraph** (`claim_justifications_from_active_graph`, line 67-105):
1. For each active claim, creates a base justification with `justification_id=f"reported:{claim_id}"`, `rule_kind="reported_claim"`, no premises.
2. For each active `supports` or `explains` relation, creates a derived justification with `justification_id=f"{relation_type}:{source_id}->{target_id}"`, the source as a premise, and the target as conclusion.

**Path B — from ArtifactStore** (`_canonical_justifications` in `propstore/structured_argument.py`, line 215-248):
Identical logic but reads from `stance_rows` (DB rows) instead of graph edges. Used when no `active_graph` is provided.

Both paths produce only single-premise derived justifications. Multi-premise justifications are not created by any existing code.

---

## 2. Are justifications stored in SQLite?

**No.** There is no `justification` table in the SQLite sidecar. The word "justification" does not appear anywhere in `propstore/build_sidecar.py`.

Justifications are created in-memory at query time by `build_structured_projection()` in `structured_argument.py`. They are ephemeral -- derived from claims and stances each time the argumentation framework is constructed.

---

## 3. How does import_papers work?

**File:** `propstore/cli/compiler_cmds.py`, line 415-611

```python
def import_papers(obj: dict, papers_root: Path, output_dir: Path | None, dry_run: bool, strict: bool) -> None:
```

**Per paper directory, it reads exactly one file:** `{paper_dir}/claims.yaml` (line 426-428).

**Pipeline:**
1. Iterates `papers_root` subdirectories, finds `claims.yaml` in each.
2. Builds a concept name-to-ID lookup from the concept registry.
3. For each paper:
   - Reads `claims.yaml` via `yaml.safe_load`.
   - Sets `source.paper` to the directory name.
   - Prefixes claim IDs with a sanitized source prefix for global uniqueness (e.g., `Dung_1995:claim1`).
   - Prefixes inline stance targets that reference local IDs (lines 477-486).
   - Resolves concept name references to concept IDs (`_resolve_concept_refs`).
4. Optional dimensional check via bridgman/sympy for equation claims.
5. Writes resolved data to `{output_dir}/{paper_dir_name}.yaml`.

**What it does NOT read:** standalone stance files, justification files, notes files. Only `claims.yaml`.

**Cross-paper reference resolution:** Limited to prefixing local claim IDs and inline stance targets. Stance targets that already contain `:` are assumed to be already-qualified cross-paper references and are left alone (line 485: `if target and ":" not in target and target in local_ids`).

**What would need to change to also read `justifications.yaml`:** A new loop after claim processing that reads `{paper_dir}/justifications.yaml`, prefixes justification IDs and claim references with the source prefix, and writes them to the output. The build_sidecar would also need a new table and INSERT logic.

---

## 4. How does the undercuts stance currently resolve?

**Two separate systems handle undercuts differently:**

### Claim-graph backend (`propstore/argumentation.py`)
`undercuts` is in `_UNCONDITIONAL_TYPES` (line 24), meaning it always succeeds as a defeat -- no preference check. But this backend treats claims as arguments directly, so undercuts targets a *claim ID*, not a justification.

### Structured argument backend (`propstore/structured_argument.py`)
The `_target_argument_ids` function (line 357-377) handles undercuts:

```python
if stance_type == "undercuts":
    return {
        argument.arg_id
        for argument in arguments
        if argument.claim_id == target_claim_id and argument.attackable_kind == "inference_rule"
    }
```

This targets StructuredArguments where:
- `claim_id == target_claim_id` (the claim being concluded)
- `attackable_kind == "inference_rule"` (only derived arguments, not base reported claims)

**Critical observation:** Undercuts currently targets all inference-rule arguments for a given claim. It cannot target a *specific* justification. If claim X has three different justifications (three different inference paths), an undercut on X attacks all three inference-rule arguments indiscriminately. There is no mechanism to say "this undercut only defeats justification J3 for claim X."

To support targeted undercutting of a specific justification, the stance would need a `target_justification_id` field, and `_target_argument_ids` would need to filter by `argument.justification_id == target_justification_id` instead of just `argument.claim_id`.

### ASPIC+ backend (`propstore/aspic.py`)
The formal ASPIC+ implementation handles undercutting properly per Modgil & Prakken 2018 Def 8c (line 692-696): it targets specific defeasible rules by name `n(r)`. This is the theoretically correct approach but operates on a different type system (Literal/Rule/Argument rather than claim IDs).

---

## 5. What does the StructuredArgument builder assume about justification structure?

**File:** `propstore/structured_argument.py`, `build_structured_projection()` (line 57-172)

**It handles chaining, not just flat structure.** The builder uses a fixpoint loop:

1. **Phase 1** (lines 78-106): Creates base arguments from `reported_claim` justifications. Each active claim gets one base argument with `attackable_kind="base_claim"`, no premises, no subarguments.

2. **Phase 2** (lines 108-151): Iterative fixpoint (`while changed`). For each justification with premises:
   - Looks up existing arguments for each premise claim.
   - Takes the Cartesian product of premise argument sets (`product(*premise_groups)`).
   - For each combination, builds a derived argument with `attackable_kind="inference_rule"`.
   - Checks for cycles: skips if `conclusion_claim_id in dependency_claim_ids`.
   - Tracks transitive dependencies via `_dependency_claim_ids` and `_closure_subargument_ids`.
   - Repeats until no new arguments are produced.

**This means:** If A supports B and B supports C, the builder will create:
- `arg:A` (base), `arg:B` (base), `arg:C` (base)
- `arg:B:supports:A->B:...` (derived, premise A)
- `arg:C:supports:B->C:...` (derived, premise B -- multiple variants using different B arguments)

The chaining works because the `while changed` loop re-runs until fixpoint. New derived arguments for B become available as premises for justifications concluding C.

**Current limitation:** All justifications from existing code have at most one premise (single source claim in a `supports`/`explains` relation). The builder *supports* multi-premise justifications via `product(*premise_groups)`, but nothing currently creates them.

---

## 6. What SQLite tables exist in the sidecar?

**File:** `propstore/build_sidecar.py`

| Table | Key Columns | Line |
|-------|-------------|------|
| `concept` | `id` (PK), `content_hash`, `seq`, `canonical_name`, `status`, `domain`, `definition`, `kind_type`, `form`, `form_parameters` | 347 |
| `alias` | `concept_id` (FK), `alias_name`, `source` | 366 |
| `relationship` | `source_id` (FK), `type`, `target_id` (FK), `conditions_cel`, `note` | 373 |
| `parameterization` | `output_concept_id` (FK), `concept_ids`, `formula`, `sympy`, `exactness`, `conditions_cel` | 383 |
| `parameterization_group` | `concept_id` (FK), `group_id` | 393 |
| `form` | `name` (PK), `kind`, `unit_symbol`, `is_dimensionless`, `dimensions` | 399 |
| `form_algebra` | `id` (PK auto), `output_form` (FK), `input_forms`, `operation`, `source_concept_id`, `source_formula`, `dim_verified` | 407 |
| `context` | `id` (PK), `name`, `description`, `inherits` (FK) | 687 |
| `context_assumption` | `context_id` (FK), `assumption_cel`, `seq` | 695 |
| `context_exclusion` | `context_a` (FK), `context_b` (FK) | 702 |
| `claim` | `id` (PK), `content_hash`, `seq`, `type`, `concept_id`, `value`, `lower_bound`, `upper_bound`, `uncertainty`, `uncertainty_type`, `sample_size`, `unit`, `conditions_cel`, `statement`, `expression`, `sympy_generated`, `sympy_error`, `name`, `target_concept`, `measure`, `listener_population`, `methodology`, `notes`, `description`, `auto_summary`, `stage` | 792 |
| `claim_stance` | `claim_id` (FK), `target_claim_id` (FK), `stance_type`, `strength`, `conditions_differ`, `note`, `resolution_method`, `resolution_model`, `embedding_model`, `embedding_distance`, `pass_number`, `confidence`, `opinion_belief`, `opinion_disbelief`, `opinion_uncertainty`, `opinion_base_rate` | 832 |
| `calibration_counts` | `pass_number`, `category`, `correct_count`, `total_count` (composite PK) | 861 |
| `conflicts` | `concept_id`, `claim_a_id` (FK), `claim_b_id` (FK), `warning_class`, `conditions_a`, `conditions_b`, `value_a`, `value_b`, `derivation_chain` | 869 |

Plus FTS5 virtual tables for concept and claim search (referenced in the module docstring but not quoted here).

**No justification table exists.**

---

## 7. What's in aspic.py?

**File:** `propstore/aspic.py` (948 lines)

This is a **fully implemented** ASPIC+ structured argumentation framework following Modgil & Prakken (2018). It is a leaf module with zero propstore imports (except a TYPE_CHECKING import of `ArgumentationFramework` from `propstore.dung`).

### Data structures (Defs 1-5):
- `Literal` -- atoms with negation, `.contrary` property (Def 1)
- `ContrarinessFn` -- contradictories (symmetric) and contraries (asymmetric) (Def 1)
- `Rule` -- strict or defeasible inference rules with optional name `n(r)` (Def 2)
- `PremiseArg`, `StrictArg`, `DefeasibleArg` -- three argument types (Def 5)
- `Argument = Union[PremiseArg, StrictArg, DefeasibleArg]`
- `Attack` -- attacker, target, target_sub, kind (Def 8)
- `KnowledgeBase` -- axioms K_n and premises K_p (Def 4)
- `PreferenceConfig` -- rule_order, premise_order, comparison, link (Defs 19-22)
- `ArgumentationSystem` -- language, contrariness, strict_rules, defeasible_rules (Def 2)
- `CSAF` -- complete structured argumentation framework bundle (Def 12)

### Core algorithms (all implemented, not stubbed):
- `transposition_closure()` -- strict rule closure with degenerate filtering (Def 12, lines 247-334)
- `strict_closure()` -- literal closure under strict rules (Def 3, lines 337-366)
- `is_c_consistent()` -- consistency check (Def 6, lines 369-385)
- `build_arguments()` -- bottom-up c-consistent argument construction with fixpoint (Def 5, lines 514-616)
- `compute_attacks()` -- undermining, rebutting, undercutting (Def 8, lines 622-718)
- `compute_defeats()` -- preference-filtered defeats (Def 9, lines 860-912)
- `_strictly_weaker()` -- argument preference via last-link or weakest-link (Defs 20-21, lines 783-857)
- `_set_strictly_less()` -- elitist/democratic set comparison (Def 19, lines 724-780)

### Computed properties (cached):
- `conc()`, `prem()`, `sub()`, `top_rule()`, `def_rules()`, `last_def_rules()`, `prem_p()`, `is_firm()`, `is_strict()` -- all per Def 5

### What it does NOT do:
- It does not bridge to propstore's claim/stance data model. There is no code that converts claims and stances into `Literal`s, `Rule`s, and `KnowledgeBase` objects. The module is a standalone formal engine.
- The `CSAF` dataclass at line 918-948 bundles everything but there is no `build_csaf()` factory function visible in this file.

---

## Summary of Key Findings for Spec Work

1. **Justifications are ephemeral.** They exist only in memory during `build_structured_projection()`. No persistence, no table, no file format.

2. **The import pipeline reads only `claims.yaml` per paper.** Adding `justifications.yaml` requires: new file read in `import_papers`, new SQLite table in `build_sidecar`, new `_populate_justifications` function.

3. **Undercuts cannot target specific justifications.** The structured argument builder resolves undercuts by claim_id + attackable_kind, hitting all inference-rule arguments for a claim. Targeted undercutting needs a `target_justification_id` on stances and filtering in `_target_argument_ids`.

4. **The ASPIC+ engine is complete but unconnected.** `aspic.py` implements the full formal framework (Defs 1-22) but has no bridge to propstore's data model. The structured_argument.py builder is the actual runtime system, using a simplified ASPIC+-inspired approach over claims.

5. **Multi-premise justifications are structurally supported but never created.** The builder handles them via Cartesian product, but all existing justification-creation code produces single-premise entries.

6. **The LinkML schema has no Justification class.** `schema/claim.linkml.yaml` defines ClaimFile, Claim, Stance, Provenance, etc. A new Justification class would need to be added.
