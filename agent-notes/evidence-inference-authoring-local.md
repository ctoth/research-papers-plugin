# Evidence and inference authoring

## Goal
Correct the plugin instructions that produced unsupported aspirin rule dependencies.
Q authorized the narrow working demo, cause-level plugin fixes and a draft PR
in the existing ctoth/research-papers-plugin repository.

## State
Focused publication branch `fix/evidence-inference-authoring-public`, based on
remote master 00ca9ce21d3330bef4b88d3f18803621a0b7725d.
The original checkout has unrelated dirty work and is untouched.
Five authoring skills and the paper-process orchestrator are corrected locally.
The full plugin suite passed 170 tests and 41 subtests, with one skip.
No release bump or remote mutation.

## Decisions and why
- `author-rules` is the instruction owner. Its setting-only empirical example
  matches the surviving aspirin rules: a result follows from trial existence.
  Delete that example; keep contextual applicability distinct from evidence.
- `extract-stances` must distinguish reported results from transport inferences;
  context differences do not establish rebuttal, and recency alone is not evidence
  for replacing a result.
- Source-local `just1` is legitimate today: Propstore promotion derives canonical
  content IDs. Do not rename local IDs to conceal the historical projection loss.
- Current Propstore issues already cover #21 (reader/mirror), #55 (explicit
  argument targets), #56 (stance evidence), #123 (justification contract),
  #155 (overlay snapshot). No duplicate issues will be filed.

## Smallest change
Replace the misleading examples/instructions in five existing authoring skills
and add focused assertions in the existing workflow-contract file. The lifting
skill is shorter: its old mutation commands do not exist in the current CLI, and
its assertion that conditions rewrite claim conditions contradicts the actual
LiftingSystem gate evaluator. No runtime, release, or schema changes here.

## Surprises
Plugin prompts cannot repair missing Propstore reader APIs or canonical fields.

## Next step
Keep the publication PR as a draft and await review. No release is requested.

## Responsibility established
- Plugin author-rules teaches the exact setting-only empirical rule found in the
  aspirin corpus; this is an instruction cause, now removed.
- Plugin lifting instructions claimed conditions rewrite propositions and
  encouraged changing conflict counts; current evaluator only gates a lift.
  Corrected to preserve unknown applicability and report unavailable authoring.
- Canonical justification reader (#21) and lost specific targets (#55) are
  Propstore defects; plugin cannot repair them by changing extraction wording.
- Accepted-but-lossy attack-target examples now report the runtime limitation
  rather than claiming successful preservation.
- Current author-context also documented removed mutation commands. Its existing
  validation step now checks the real installed surface and reports the owner
  gap; the skill cannot promise a complete paper-process ingestion today.

## Local draft description
Title: Preserve evidence dependencies and applicability scope in authoring

Remove the setting-only empirical rule example that disconnected conclusions
from their evidence. Keep source reports separate from reviewer transport
inferences; do not replace observations for recency alone or manufacture
cross-context conflicts. Report current context-CLI and explicit-target limits
instead of documenting removed commands or accepted-but-lossy success.
Validation: affected workflow contract file, 21 tests passed offline.

## Independent review corrections and full validation
- The first correction retained unsupported rule mutation commands. Verified
  propstore/cli/rule/__init__.py and display.py and executed read-only rule help:
  only list/show are registered. Replaced the obsolete CLI workflow with a
  capability check and explicit stop, including superiority authoring. Removed
  fake version guarantees, command examples and fabricated success output.
- Corrected paper-process's claim that only DeLP rules participate in defeasible
  reasoning: canonical justifications also supply inference licences to ASPIC.
  The orchestrator stops when the nested authoring skill reports its blocker.
- Two regressions were added to the existing workflow-contract test owner.
- Full plugin suite: **170 passed, 1 skipped, 41 subtests passed**, exit 0, 2.12s.
  Log: logs/test-runs/full-plugin-revised-20261019-181751.log.
- The only warning is a denied write to the pre-existing pytest cache, not
  a failed test. Disposable outputs were isolated under ../test-output.

Command, from this worktree with UV_OFFLINE=1, UV_NO_SYNC=1,
PYTHONDONTWRITEBYTECODE=1 and UV_CACHE_DIR under ../test-output:
```powershell
uv run --offline --no-sync --project C:/Users/Q/code/propstore python C:/Users/Q/code/propstore/scripts/run_logged_pytest.py --label full-plugin-revised -- plugins/research-papers/tests --basetemp=C:/Users/Q/Documents/Codex/2026-10-19/task-18/test-output/plugin-revised -n 0 -q
```

## Focused publication branch
The original local branch is preserved. Its base ac52829 contained an unrelated
root-note move; the publication worktree cherry-picks only a9ab901 and bf5c90e
onto verified remote master. A Git directory-rename suggestion moved the new
task note to the repository root; the conflict was resolved by keeping this
one task note under agent-notes as required. No unrelated notes were imported.
The plugin tree matches the independently reviewed local plugin tree exactly.
Fresh full run in this publication worktree: 170 passed, 1 skipped,
41 subtests passed in 3.11s, exit 0.
Log: logs/test-runs/publication-plugin-20261019-190635.log.
No version bump, tag, merge or ready-for-review transition is authorized.
Draft PR: https://github.com/ctoth/research-papers-plugin/pull/49.
