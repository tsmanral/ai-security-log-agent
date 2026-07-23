---
name: security-fix-with-regression-test
description: Workflow command scaffold for security-fix-with-regression-test in lsadra.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /security-fix-with-regression-test

Use this workflow when working on **security-fix-with-regression-test** in `lsadra`.

## Goal

Implements a security fix or hardening, and adds or updates a regression test to pin the behavior.

## Common Files

- `lsadra/config.py`
- `lsadra/ingestion/api_ingestion.py`
- `lsadra/onboarding/device_registration.py`
- `lsadra/ratelimit.py`
- `tests/security/test_s6_*.py`
- `.env.example`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Edit one or more implementation files to apply the security fix (e.g., config.py, api_ingestion.py, device_registration.py, ratelimit.py).
- Edit or add a dedicated regression test file under tests/security/ (typically test_s6_XX_*.py) to cover the specific issue.
- Optionally update .env.example and/or requirements.txt if configuration or dependencies change.
- Run and verify the regression suite (pytest tests/security/).

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.