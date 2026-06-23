---
name: configure-bookshare
description: Configure Bookshare access. Asks the user for their Bookshare username (email) and password, stores them in the gitignored .secrets/bookshare.json credential store, and selects the browser backend (the default — works without a developer api_key). Run this once before using bookshare-retriever.
argument-hint: ""
disable-model-invocation: false
compatibility: "Claude Code, Codex CLI, and Gemini CLI. Requires shell access. Credentials are stored locally in .secrets/ (gitignored) and never committed."
---

# Configure Bookshare

Set up Bookshare so `bookshare-retriever` can download books. This stores the user's
Bookshare credentials locally and selects the **browser** backend, which logs into
the user's account with a username/password — no developer api_key required.

Secrets are written only to the gitignored `.secrets/bookshare.json`. **Never print,
echo, or repeat the password** in your output, logs, or summaries.

## Script Paths

The `scripts/...` paths below are relative to this skill's directory. Resolve them
against the installed skill location, not the user's project root.

## Step 1: Ask for the credentials

Ask the user, in the chat, for:

1. their **Bookshare username** (the email or username they log in with), and
2. their **Bookshare password**.

Tell them the values are stored locally in `.secrets/bookshare.json` (gitignored,
never committed) and can be changed any time by re-running this skill. Do not echo
the password back.

## Step 2: Store the username

Pipe the value via stdin so it isn't passed as a visible argument:

```bash
printf '%s' "<username the user gave>" | uv run scripts/credential_store.py set bookshare username --from-stdin --root .
```

## Step 3: Store the password

```bash
printf '%s' "<password the user gave>" | uv run scripts/credential_store.py set bookshare password --from-stdin --root .
```

Do not print the password in any surrounding text. The command stores it directly in
`.secrets/bookshare.json`.

## Step 4: Select the browser backend (default)

```bash
uv run scripts/credential_store.py auth-method bookshare browser --root .
```

This makes the browser login the default experience for Bookshare.

## Step 5: Confirm (presence only)

```bash
uv run scripts/credential_store.py show bookshare --root .
```

This prints presence only — e.g. `username: set`, `password: set`, `auth_method:
browser` — never the values. Confirm both are `set`, then tell the user Bookshare is
configured and they can run `/research-papers:bookshare-retriever "<title>"`.

## Optional: official API instead of the browser

If the user has a developer api_key (from partner-support@bookshare.org), also store
it and switch the backend:

```bash
printf '%s' "<api_key>" | uv run scripts/credential_store.py set bookshare api_key --from-stdin --root .
uv run scripts/credential_store.py auth-method bookshare api --root .
```

## Execution Discipline

Follow the steps in order. Never reveal stored secret values. If the user declines to
provide credentials, stop and explain that Bookshare retrieval needs them (or an
api_key for the API backend).
