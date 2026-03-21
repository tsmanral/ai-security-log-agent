---
name: add-new-ml-model
description: Workflow command scaffold for add-new-ml-model in ai-security-log-agent.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-new-ml-model

Use this workflow when working on **add-new-ml-model** in `ai-security-log-agent`.

## Goal

Adds a new machine learning anomaly detection model to the platform, including implementation, registration, and integration with detection pipeline.

## Common Files

- `ai_sentinel/models/*.py`
- `ai_sentinel/models/__init__.py`
- `ai_sentinel/models/ensemble_model.py`
- `evaluation/evaluate_models.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create new model file in models/ (e.g., isolation_forest.py, autoencoder_model.py)
- Update __init__.py in models/ to register the new model
- Update detection orchestrator or ensemble logic to include the new model
- Optionally add or update tests/evaluation scripts

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.