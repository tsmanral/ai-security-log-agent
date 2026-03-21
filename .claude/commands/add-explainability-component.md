---
name: add-explainability-component
description: Workflow command scaffold for add-explainability-component in ai-security-log-agent.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-explainability-component

Use this workflow when working on **add-explainability-component** in `ai-security-log-agent`.

## Goal

Adds or updates explainability modules (e.g., SHAP, narrative builder) to help interpret model decisions.

## Common Files

- `ai_sentinel/explainability/*.py`
- `ai_sentinel/explainability/__init__.py`
- `agent/explainability/*.py`
- `agent/explainability/__init__.py`
- `dashboard/dashboard.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or update explainability file (e.g., shap_explainer.py, narrative_builder.py)
- Update __init__.py in explainability/ to register new component
- Integrate with dashboard or detection pipeline

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.