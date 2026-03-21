---
name: add-feature-extraction-module
description: Workflow command scaffold for add-feature-extraction-module in ai-security-log-agent.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-feature-extraction-module

Use this workflow when working on **add-feature-extraction-module** in `ai-security-log-agent`.

## Goal

Implements new feature extraction logic for behavioral or temporal features, and integrates it into the pipeline.

## Common Files

- `ai_sentinel/features/*.py`
- `ai_sentinel/features/__init__.py`
- `agent/features/*.py`
- `agent/features/__init__.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or update feature extraction file in features/ (e.g., behavioral_features.py, temporal_features.py)
- Update __init__.py in features/ to expose new features
- Update feature_extractor.py to use the new feature logic

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.