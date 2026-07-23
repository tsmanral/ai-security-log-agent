---
name: add-or-update-config-with-env-doc
description: Workflow command scaffold for add-or-update-config-with-env-doc in lsadra.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-or-update-config-with-env-doc

Use this workflow when working on **add-or-update-config-with-env-doc** in `lsadra`.

## Goal

Adds or modifies a configuration option, ensuring it is documented in .env.example and reflected in config.py.

## Common Files

- `lsadra/config.py`
- `.env.example`
- `server.py`
- `lsadra/ingestion/api_ingestion.py`
- `tests/security/test_s6_*.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Edit lsadra/config.py to add or update the config variable.
- Edit .env.example to document the new or changed environment variable.
- Edit relevant code files to use the new config (e.g., server.py, api_ingestion.py).
- Add or update regression tests if needed.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.