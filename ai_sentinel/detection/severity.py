"""
AI-Sentinel V3 — Severity scoring module.

Computes a composite severity score (0.0–1.0) from multiple detection layers
and maps it to a severity label (CRITICAL / HIGH / MEDIUM / LOW).
"""

import logging
from typing import Any, Dict, Tuple

from ai_sentinel.config import SEVERITY_THRESHOLDS

logger = logging.getLogger(__name__)

# Weights for each detection layer in the composite score
_LAYER_WEIGHTS = {
    "layer1_z": 0.25,        # statistical baseline z-score
    "layer2_score": 0.35,    # ensemble anomaly score
    "layer3_error": 0.20,    # autoencoder reconstruction error
    "vote_ratio": 0.20,      # ensemble vote ratio
}

# Normalization bounds (approximate; will be clipped to [0, 1])
_Z_SCORE_MAX = 10.0
_AE_ERROR_MAX = 0.5


def compute_severity_score(
    layer1_z: float = 0.0,
    layer2_score: float = 0.0,
    layer2_votes: int = 0,
    total_models: int = 3,
    layer3_error: float = 0.0,
) -> Tuple[float, str]:
    """
    Compute a composite severity score and label.

    Args:
        layer1_z: Max z-score from statistical baseline (Layer 1).
        layer2_score: Averaged anomaly score from ensemble (Layer 2).
        layer2_votes: Number of ensemble sub-models voting anomaly.
        total_models: Total sub-models in the ensemble.
        layer3_error: Reconstruction error from autoencoder (Layer 3).

    Returns:
        Tuple of (severity_score: float [0–1], severity_label: str).
    """
    # Normalize each signal to [0, 1]
    norm_z = min(abs(layer1_z) / _Z_SCORE_MAX, 1.0)
    norm_ensemble = min(abs(layer2_score), 1.0)
    norm_ae = min(abs(layer3_error) / _AE_ERROR_MAX, 1.0)
    vote_ratio = layer2_votes / max(total_models, 1)

    # Weighted composite
    score = (
        _LAYER_WEIGHTS["layer1_z"] * norm_z
        + _LAYER_WEIGHTS["layer2_score"] * norm_ensemble
        + _LAYER_WEIGHTS["layer3_error"] * norm_ae
        + _LAYER_WEIGHTS["vote_ratio"] * vote_ratio
    )

    # Clamp to [0, 1]
    score = max(0.0, min(score, 1.0))

    # Map to severity label
    label = _score_to_label(score)

    return score, label


def _score_to_label(score: float) -> str:
    """Map a severity score to a label using configured thresholds."""
    if score >= SEVERITY_THRESHOLDS.get("CRITICAL", 0.9):
        return "CRITICAL"
    elif score >= SEVERITY_THRESHOLDS.get("HIGH", 0.7):
        return "HIGH"
    elif score >= SEVERITY_THRESHOLDS.get("MEDIUM", 0.4):
        return "MEDIUM"
    else:
        return "LOW"


def severity_context(score: float, label: str) -> Dict[str, Any]:
    """
    Build a severity context dict for use in narratives and SHAP.

    Returns:
        Dict with severity_score, severity_label, urgency_description.
    """
    urgency_map = {
        "CRITICAL": "Immediate action required — active exploitation likely.",
        "HIGH": "Urgent investigation recommended — strong anomaly detected.",
        "MEDIUM": "Review recommended — moderate anomaly indicators present.",
        "LOW": "Low-priority — minor anomaly detected, possible false positive.",
    }
    return {
        "severity_score": round(score, 4),
        "severity_label": label,
        "urgency": urgency_map.get(label, "Unknown severity level."),
    }
