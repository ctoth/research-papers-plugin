# Enforce plugin tests in CI

## Goal
Add the missing ordinary test workflow as a separate draft PR from current
default master. Stop for parent review and merge; do not merge this PR or #49.

## Evidence and state
- Base: 00ca9ce21d3330bef4b88d3f18803621a0b7725d.
- GitHub Actions is enabled, allowed_actions=all. Workflow defaults are read
  and cannot approve PR reviews. No settings or permissions are changed.
- Actions API returned zero registered workflows and zero workflow runs.
- Default and PR #49 trees contain no .github/workflows files. Therefore the
  missing checks are absent wiring, not filtered/disabled/failed workflows.
- README describes a locked non-package uv project, but pyproject.toml and
  uv.lock exist only as untracked files in the original working checkout.
  That checkout and all its dirty files remain untouched.
- Tests import pytest and yaml; network-client dependencies are stubbed in
  their unit tests. test_render_pages.py uses importorskip("fitz") for a real
  generated-PDF page-count test. Include PyMuPDF so that coverage runs.

## Smallest implementation
One Linux/Python 3.13 job, about 38 workflow lines, a small non-package test
manifest and generated lockfile, plus corrected development commands.
No runtime code, tests, guards outside CI, type-checker adoption, version
matrix, credentials, secrets, paid services or security settings are added.
The workflow runs the full existing suite, with an explicit fitz import to
prevent the known missing-dependency skip.
The test dependency keeps PyMuPDF on its compatible 1.x rendering API. Resolving
unbounded 2.0 pulled layout/LLM/ONNX dependencies that are unnecessary for the
existing generated-PDF page-count test; no test was removed or skipped.

## Decisions and next step
Use repository-ci conventions: contents: read, immutable official action SHAs,
no persisted checkout credential, bounded time and superseded-run cancellation.
Validate YAML/security, then publish this separate draft and verify an actual
pull_request Actions run. Only after the parent merges it should PR #49 merge
current master normally and obtain its own fresh CI result. Do not rewrite
published authoring history or bundle CI into #49.

Workflow audits: actionlint v1.7.12 passed; zizmor v1.31.1 completed its offline
audit with no findings. Tools used task-local caches and existing runtimes.
The uv 0.13.3-generated lockfile pins pytest 9.1.1, PyYAML 6.0.3 and
PyMuPDF 1.28.2. It was copied unchanged via the editing tool; SHA-256:
A996A9740CF04C7F01A9554666E37EC2BD863F5D94901F8F711DF8EEFB22BF97.
Review stop: after actual Actions execution is verified, leave the CI PR draft
and unmerged for the parent. Its live check is the execution evidence.
