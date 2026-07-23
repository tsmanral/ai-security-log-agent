---
name: rate-limiter-implementation-and-hardening
description: Workflow command scaffold for rate-limiter-implementation-and-hardening in lsadra.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /rate-limiter-implementation-and-hardening

Use this workflow when working on **rate-limiter-implementation-and-hardening** in `lsadra`.

## Goal

Implements or hardens a rate limiter, and adds/updates regression tests for edge cases and bypasses.

## Common Files

- `lsadra/ratelimit.py`
- `lsadra/ingestion/api_ingestion.py`
- `lsadra/onboarding/device_registration.py`
- `lsadra/config.py`
- `tests/security/test_s6_05_ratelimit_lru.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or edit lsadra/ratelimit.py to implement or update the rate limiter logic.
- Edit code that uses the rate limiter (e.g., api_ingestion.py, device_registration.py).
- Edit lsadra/config.py to add or update rate limit config variables.
- Add or update regression tests in tests/security/test_s6_05_ratelimit_lru.py.
- Verify that bypasses and DoS vectors are covered by tests.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.