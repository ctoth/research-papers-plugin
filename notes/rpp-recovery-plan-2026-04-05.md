# research-papers-plugin Recovery Plan

Date: 2026-04-05

## Objective

Recover the `research-papers-plugin` repository to a coherent, repository-wide source-oriented workflow. The target state is not "some new files landed." The target state is:

- no mixed legacy/source-branch contract inside the same active workflow
- no stale skill text instructing agents to use superseded file shapes
- no surviving source-oriented files pointing at nonexistent CLI flags
- no silent dependence on destroyed pre-existing edits

This plan is file-by-file and recovery-oriented. It is not a greenfield redesign.

## Ground Truth From The Audit

### Surviving source-oriented slice

These files currently contain substantive source-branch work and must be preserved, then repaired where inconsistent:

- `plugins/research-papers/skills/register-concepts/SKILL.md`
- `plugins/research-papers/skills/extract-claims/SKILL.md`
- `plugins/research-papers/skills/extract-justifications/SKILL.md`
- `plugins/research-papers/skills/extract-stances/SKILL.md`
- `plugins/research-papers/skills/paper-process/SKILL.md`
- `plugins/research-papers/skills/ingest-collection/SKILL.md`
- `plugins/research-papers/scripts/propose_concepts.py`
- `plugins/research-papers/scripts/sync_propstore_source.py`
- `plugins/research-papers/tests/test_propose_concepts.py`
- `plugins/research-papers/tests/test_pks_pipeline_integration.py`
- `plugins/research-papers/tests/test_sync_propstore_source.py`

### Explicitly named losses

Local repo notes state that a blanket checkout destroyed uncommitted work on:

- `plugins/research-papers/skills/adjudicate/SKILL.md`
- `plugins/research-papers/skills/paper-process/SKILL.md`
- `plugins/research-papers/skills/paper-reader/SKILL.md`
- `plugins/research-papers/skills/process-new-papers/SKILL.md`

`paper-process` was later recreated, but the note explicitly says Q's prior version was not recovered.

### Current mixed-state contradictions

These contradictions already exist in the live repo and must be resolved first:

1. `register-concepts/SKILL.md` calls `propose_concepts.py pks-batch` with `--forms-dir` and `--domain`, but `propose_concepts.py` does not accept those flags.
2. `extract-claims/SKILL.md` contains `pks source add-claim`, but also still depends on legacy `knowledge/concepts/*.yaml`, `knowledge/claims/*.yaml`, and sequential `claim1` rules.
3. `extract-stances/SKILL.md` is source-oriented and standalone-file based, while older repo notes and aggregate skill docs still describe embedded stances in `claims.yaml`.
4. `sync_propstore_source.py` still exists as an active bridge even though the collection-level workflow is now `ingest-collection`.
5. `skills.md` and several notes still document the old architecture, which means agents consulting the repo can still be driven into the wrong path.

## Recovery Rules

1. One target surface at a time.
2. Every slice ends with passing targeted tests or a revert.
3. Do not preserve compatibility with legacy contracts if it keeps the active workflow mixed.
4. Preserve the surviving source-oriented slice unless it is internally inconsistent.
5. Rewrite docs and skills to the contract the code actually supports, not the contract we wish existed.

## Recovery Order

### Phase 1: Stabilize The Surviving Source-Oriented Slice

Goal: make the already-landed source-oriented files internally consistent before touching broader repo surfaces.

Files:

- `plugins/research-papers/scripts/propose_concepts.py`
- `plugins/research-papers/skills/register-concepts/SKILL.md`
- `plugins/research-papers/skills/extract-claims/SKILL.md`
- `plugins/research-papers/skills/extract-justifications/SKILL.md`
- `plugins/research-papers/skills/extract-stances/SKILL.md`
- `plugins/research-papers/skills/paper-process/SKILL.md`
- `plugins/research-papers/scripts/sync_propstore_source.py`
- `plugins/research-papers/tests/test_propose_concepts.py`
- `plugins/research-papers/tests/test_pks_pipeline_integration.py`
- `plugins/research-papers/tests/test_sync_propstore_source.py`

Required outcomes:

- `register-concepts` only documents CLI flags that `propose_concepts.py` actually supports.
- `extract-claims` documents one claim-ID policy and one concept-resolution path.
- `extract-stances` remains standalone `stances.yaml`.
- `paper-process` matches the real per-paper source workflow.
- `sync_propstore_source.py` is either explicitly deprecated in favor of `ingest-collection` or kept as a narrow transition script with honest docs.
- tests cover the exact file shapes the skills now describe.

### Phase 2: Recover The Explicitly Lost Or Overwritten Skills

Goal: remove the highest-risk "destroyed before landing" gaps.

Files:

- `plugins/research-papers/skills/paper-reader/SKILL.md`
- `plugins/research-papers/skills/process-new-papers/SKILL.md`
- `plugins/research-papers/skills/adjudicate/SKILL.md`
- `plugins/research-papers/skills/paper-process/SKILL.md` (second pass, after Phase 1 stabilization)

Required outcomes:

- `paper-reader` is reconciled with the source-oriented pipeline but remains a paper-reading skill, not a propstore ingestion skill.
- `process-new-papers` orchestrates the current `paper-reader` contract and does not embed stale assumptions about downstream files.
- `adjudicate` is reviewed against current collection workflow and any lost edits are consciously recreated or consciously dropped.
- `paper-process` is checked for lost Q-specific intent and aligned with the recovered adjacent skills.

Evidence sources for reconstruction:

- surviving local notes under `notes/`
- current skill body structure
- current source-oriented plan/proposal documents in `propstore`

### Phase 3: Convert Adjacent Legacy Skills And Docs

Goal: remove stale repo-level instructions that can still push agents into the wrong architecture.

Files:

- `plugins/research-papers/skills/reconcile-vocabulary/SKILL.md`
- `plugins/research-papers/skills/reconcile/SKILL.md`
- `plugins/research-papers/skills/enrich-claims/SKILL.md`
- `plugins/research-papers/skills.md`
- repo notes that still describe embedded stances or direct `knowledge/` mutation as the active path

Required outcomes:

- `reconcile-vocabulary` stops pretending the canonical path is direct `claims.yaml` rewriting without source-branch alignment.
- `reconcile` is left domain-specific if appropriate, but its surrounding text must not contradict the active workflow.
- `enrich-claims` either becomes source-aware or is explicitly scoped as legacy and removed from active orchestration.
- `skills.md` is regenerated or rewritten so it no longer contradicts the per-skill files.

### Phase 4: Repo-Wide Consistency Pass

Goal: one active architecture across skills, scripts, tests, and repo notes.

Checks:

- no active skill instructs agents to use embedded stance format
- no active orchestrator skips required source-branch steps
- no active skill references nonexistent script flags
- no aggregate doc contradicts the current skill contract
- no surviving test encodes a superseded file shape

## File Classification

### Keep, then repair

- `plugins/research-papers/scripts/propose_concepts.py`
- `plugins/research-papers/scripts/sync_propstore_source.py`
- `plugins/research-papers/skills/register-concepts/SKILL.md`
- `plugins/research-papers/skills/extract-claims/SKILL.md`
- `plugins/research-papers/skills/extract-justifications/SKILL.md`
- `plugins/research-papers/skills/extract-stances/SKILL.md`
- `plugins/research-papers/skills/paper-process/SKILL.md`
- `plugins/research-papers/skills/ingest-collection/SKILL.md`
- `plugins/research-papers/tests/test_propose_concepts.py`
- `plugins/research-papers/tests/test_pks_pipeline_integration.py`
- `plugins/research-papers/tests/test_sync_propstore_source.py`

### Reconstruct from surviving intent

- `plugins/research-papers/skills/paper-reader/SKILL.md`
- `plugins/research-papers/skills/process-new-papers/SKILL.md`
- `plugins/research-papers/skills/adjudicate/SKILL.md`

### Review and likely rewrite

- `plugins/research-papers/skills/reconcile-vocabulary/SKILL.md`
- `plugins/research-papers/skills/reconcile/SKILL.md`
- `plugins/research-papers/skills/enrich-claims/SKILL.md`
- `plugins/research-papers/skills.md`

## Test Strategy

All recovery work is test-driven where code exists.

### Existing tests to preserve and extend

- `plugins/research-papers/tests/test_propose_concepts.py`
- `plugins/research-papers/tests/test_pks_pipeline_integration.py`
- `plugins/research-papers/tests/test_sync_propstore_source.py`

### New tests to add during recovery

1. A contract test that `register-concepts/SKILL.md`'s documented command shape matches `propose_concepts.py` CLI.
2. A contract test that `extract-stances/SKILL.md` example shape matches `sync_propstore_source.py` expectations.
3. A contract test that `paper-process` ordering is consistent with the current per-paper source workflow.
4. A repo-consistency grep test for forbidden active patterns:
   - embedded stance examples in active skills
   - direct `pks concept add` in active source-oriented paths
   - nonexistent `propose_concepts.py` flags in active skills

## Definition Of Recovered

The repo is considered recovered only when:

- all active workflow skills agree on the same source-oriented artifact shapes
- all code-backed command examples correspond to real script/CLI capabilities
- the explicitly lost high-risk skills have been consciously reconstructed or consciously retired
- no aggregate repo doc can send an agent down the wrong path without immediately contradicting active files

## Immediate Next Slice

Phase 1 only:

1. repair `register-concepts` vs `propose_concepts.py`
2. repair `extract-claims` mixed legacy/source wording
3. decide the status of `sync_propstore_source.py` and make the file/docs honest
4. re-run the existing targeted tests
