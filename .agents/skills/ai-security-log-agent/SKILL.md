---
name: ai-security-log-agent-conventions
description: Development conventions and patterns for ai-security-log-agent. Python project with mixed commits.
---

# Ai Security Log Agent Conventions

> Generated from [tsmanral/ai-security-log-agent](https://github.com/tsmanral/ai-security-log-agent) on 2026-03-21

## Overview

This skill teaches Claude the development patterns and conventions used in ai-security-log-agent.

## Tech Stack

- **Primary Language**: Python
- **Architecture**: hybrid module organization
- **Test Location**: separate

## When to Use This Skill

Activate this skill when:
- Making changes to this repository
- Adding new features following established patterns
- Writing tests that match project conventions
- Creating commits with proper message format

## Commit Conventions

Follow these commit message conventions based on 2 analyzed commits.

### Commit Style: Mixed Style

### Prefixes Used

- `feat`

### Message Guidelines

- Average message length: ~111 characters
- Keep first line concise and descriptive
- Use imperative mood ("Add feature" not "Added feature")


*Commit message example*

```text
feat: Implement the AI-Sentinel SIEM anomaly detection platform with log processing, ML anomaly detection models, explainability features, and a Streamlit dashboard.
```

*Commit message example*

```text
Implement AI-Sentinel V2 Architecture (Agent-based SIEM)
```

## Architecture

### Project Structure: Single Package

This project uses **hybrid** module organization.

### Guidelines

- This project uses a hybrid organization
- Follow existing patterns when adding new code

## Code Style

### Language: Python

### Naming Conventions

| Element | Convention |
|---------|------------|
| Files | snake_case |
| Functions | camelCase |
| Classes | PascalCase |
| Constants | SCREAMING_SNAKE_CASE |

### Import Style: Relative Imports

### Export Style: Named Exports


*Preferred import style*

```typescript
// Use relative imports
import { Button } from '../components/Button'
import { useAuth } from './hooks/useAuth'
```

*Preferred export style*

```typescript
// Use named exports
export function calculateTotal() { ... }
export const TAX_RATE = 0.1
export interface Order { ... }
```

## Common Workflows

These workflows were detected from analyzing commit patterns.

### Add New Ml Model

Adds a new machine learning anomaly detection model to the platform, including implementation, registration, and integration with detection pipeline.

**Frequency**: ~2 times per month

**Steps**:
1. Create new model file in models/ (e.g., isolation_forest.py, autoencoder_model.py)
2. Update __init__.py in models/ to register the new model
3. Update detection orchestrator or ensemble logic to include the new model
4. Optionally add or update tests/evaluation scripts

**Files typically involved**:
- `ai_sentinel/models/*.py`
- `ai_sentinel/models/__init__.py`
- `ai_sentinel/models/ensemble_model.py`
- `evaluation/evaluate_models.py`

**Example commit sequence**:
```
Create new model file in models/ (e.g., isolation_forest.py, autoencoder_model.py)
Update __init__.py in models/ to register the new model
Update detection orchestrator or ensemble logic to include the new model
Optionally add or update tests/evaluation scripts
```

### Add Feature Extraction Module

Implements new feature extraction logic for behavioral or temporal features, and integrates it into the pipeline.

**Frequency**: ~2 times per month

**Steps**:
1. Create or update feature extraction file in features/ (e.g., behavioral_features.py, temporal_features.py)
2. Update __init__.py in features/ to expose new features
3. Update feature_extractor.py to use the new feature logic

**Files typically involved**:
- `ai_sentinel/features/*.py`
- `ai_sentinel/features/__init__.py`
- `agent/features/*.py`
- `agent/features/__init__.py`

**Example commit sequence**:
```
Create or update feature extraction file in features/ (e.g., behavioral_features.py, temporal_features.py)
Update __init__.py in features/ to expose new features
Update feature_extractor.py to use the new feature logic
```

### Add Explainability Component

Adds or updates explainability modules (e.g., SHAP, narrative builder) to help interpret model decisions.

**Frequency**: ~2 times per month

**Steps**:
1. Create or update explainability file (e.g., shap_explainer.py, narrative_builder.py)
2. Update __init__.py in explainability/ to register new component
3. Integrate with dashboard or detection pipeline

**Files typically involved**:
- `ai_sentinel/explainability/*.py`
- `ai_sentinel/explainability/__init__.py`
- `agent/explainability/*.py`
- `agent/explainability/__init__.py`
- `dashboard/dashboard.py`

**Example commit sequence**:
```
Create or update explainability file (e.g., shap_explainer.py, narrative_builder.py)
Update __init__.py in explainability/ to register new component
Integrate with dashboard or detection pipeline
```

### Add Detection Rule Or Classifier

Implements new detection rules or classifiers for security events.

**Frequency**: ~2 times per month

**Steps**:
1. Create or update rule_engine.py or attack_classifier.py in detection/
2. Update __init__.py in detection/ to register new rule/classifier
3. Integrate with detection orchestrator

**Files typically involved**:
- `ai_sentinel/detection/rule_engine.py`
- `ai_sentinel/detection/attack_classifier.py`
- `ai_sentinel/detection/__init__.py`
- `agent/detection/rule_engine.py`
- `agent/detection/attack_classifier.py`
- `agent/detection/__init__.py`

**Example commit sequence**:
```
Create or update rule_engine.py or attack_classifier.py in detection/
Update __init__.py in detection/ to register new rule/classifier
Integrate with detection orchestrator
```


## Best Practices

Based on analysis of the codebase, follow these practices:

### Do

- Use snake_case for file names
- Prefer named exports

### Don't

- Don't deviate from established patterns without discussion

---

*This skill was auto-generated by [ECC Tools](https://ecc.tools). Review and customize as needed for your team.*
