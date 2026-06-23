# Adding a new source adapter

A **source adapter** retrieves a paper or book from somewhere and drops it into
the `papers/` collection in the same shape the rest of the pipeline expects. There
are two flavors:

- **Unauthenticated** — public artifacts, no login (e.g. an open repository).
  Start from `fetch_source.py.tmpl`. It imports nothing from the credential store.
- **Authenticated** — an account-gated library (e.g. Bookshare). Start from
  `fetch_source_authed.py.tmpl` + `source_auth.py.tmpl`, which obtain and cache a
  token through `scripts/credential_store.py`.

`scripts/fetch_book.py` (the Bookshare adapter) is the reference implementation of
the authenticated flavor — read it alongside these templates.

## The adapter contract

Every fetch script — authed or not — conforms to one contract so the skills and
tests can treat all sources uniformly.

### CLI

- positional `identifier` — what the user supplies (`{{IDENTIFIER_HINT}}`)
- `--papers-dir papers/` — collection directory (default `papers/`)
- `--output-dir NAME` — override the computed directory name
- `--metadata-only` — resolve + write `metadata.json`, skip the artifact download

Authenticated adapters add:

- `--root .` — project root, so `credential_store` can find `.secrets/`
- `--auth-method {api,browser}` — override the configured backend

### Filesystem

Write into `papers/<dirname>/` where
`dirname = generate_dirname(author, year, title)` (reuse
`scripts/_paper_id.py` — do **not** invent your own naming):

- `papers/<dirname>/{{ARTIFACT_NAME}}` — the downloaded artifact
- `papers/<dirname>/metadata.json` — the same shape `fetch_paper.py` writes,
  plus a `"source"` field naming the adapter

Materialize the directory and `metadata.json` **only after** a real artifact lands
(the "materialize on success" discipline — a failed download leaves nothing behind).

### stdout / exit

Print exactly one `json.dumps(result, indent=2)` object and exit `0` on success,
`1` on failure. `result` carries these keys:

| key | meaning |
| --- | --- |
| `success` | `true` if metadata resolved (download may still have failed) |
| `source` | the adapter id, e.g. `{{SOURCE_NAME}}` |
| `directory` | `papers/<dirname>` |
| `dirname` | the computed `Author_Year_ShortTitle` |
| `artifact_path` | path to the downloaded artifact, or `null` |
| `artifact_type` | `"epub"`, `"pdf"`, … — lets a caller decide whether to convert |
| `metadata_path` | path to `metadata.json`, or `null` |
| `downloaded` | `true` if the artifact was written |
| `fallback_needed` | `true` when the artifact could not be retrieved |

## Placeholders

Fill these tokens when you copy a template:

| placeholder | meaning | example |
| --- | --- | --- |
| `{{SOURCE_NAME}}` | lowercase id (skill dir, credential file, config table) | `bookshare` |
| `{{SOURCE_TITLE}}` | human-readable name | `Bookshare` |
| `{{SKILL_NAME}}` | skill directory / slash-command name | `bookshare-retriever` |
| `{{ARTIFACT_NAME}}` | file written into the paper dir | `book.epub` |
| `{{API_BASE}}` | API root for search/download | `https://api.bookshare.org/v2` |
| `{{AUTH_BASE}}` | token endpoint (authed only) | `https://auth.bookshare.org/oauth/token` |
| `{{SECRET_KEYS}}` | secrets `require_secrets` demands (authed only) | `["api_key", "username", "password"]` |
| `{{IDENTIFIER_HINT}}` | what `identifier` accepts | `a title or Bookshare ID` |

## Steps

1. **Copy & rename.** For an authenticated source `{{SOURCE_NAME}}`:
   - `scripts/{{SOURCE_NAME}}_auth.py`  ← `source_auth.py.tmpl`
   - `scripts/fetch_{{SOURCE_NAME}}.py`  ← `fetch_source_authed.py.tmpl`
   - `skills/{{SKILL_NAME}}/SKILL.md`    ← `SKILL.md.tmpl`
   - `tests/test_fetch_{{SOURCE_NAME}}.py` ← `test_source_adapter.py.tmpl`

   For an unauthenticated source, use `fetch_source.py.tmpl` and skip the `_auth`
   helper.
2. **Fill placeholders.** Replace every `{{...}}` token above.
3. **Register the launcher.** Add the canonical scripts to `MANIFEST` in
   `tools/sync_skill_launchers.py`, e.g.
   `"{{SKILL_NAME}}": ["{{SOURCE_NAME}}_auth.py", "fetch_{{SOURCE_NAME}}.py"]`.
   `credential_store.py` is import-only — do **not** list it (like `_paper_id.py`).
4. **Generate launchers.** Run `python tools/sync_skill_launchers.py`.
5. **Configure (optional, non-secret).** Document a `[sources.{{SOURCE_NAME}}]`
   table in `.research-papers.toml.example`. Secrets never go here — they live in
   `.secrets/{{SOURCE_NAME}}.json` via `credential_store.py set`.
6. **Test.** `python -m pytest tests/test_fetch_{{SOURCE_NAME}}.py tests/test_source_adapter_contract.py -q`.

Write the failing test first; this collection ships every source adapter test-first.
