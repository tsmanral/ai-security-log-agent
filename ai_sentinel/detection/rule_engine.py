"""
AI-Sentinel V2 — Heuristic rule engine (Layer 4).

Classifies anomalies by mapping feature patterns to threat types and
MITRE ATT&CK technique IDs.
"""

from typing import Any, Dict, Tuple


def evaluate_rules(feature_row: Dict[str, Any]) -> Tuple[str, str]:
    """
    Evaluate heuristic rules to classify an anomaly.

    Args:
        feature_row: Dict containing behavioural and temporal features.

    Returns:
        (Threat Name, MITRE ATT&CK Technique ID).
    """
    failures = float(feature_row.get("failures_15m", 0))
    users = float(feature_row.get("unique_users_15m", 0))
    success = float(feature_row.get("successes_15m", 0))
    off_hours = int(feature_row.get("is_off_hours", 0))
    failure_ratio = float(feature_row.get("failure_ratio_15m", 0))

    # Credential stuffing — many users targeted
    if failures > 15 and users > 5:
        return "Credential Stuffing", "T1110.004"

    # Brute force — high failures, few users
    if failures > 20 and users <= 3:
        return "Brute Force Attack", "T1110.001"

    # Low-and-slow — moderate failures but very high ratio
    if 5 < failures <= 20 and failure_ratio > 0.9:
        return "Low and Slow Attack", "T1110.001"

    # Off-hour access — success during unusual times
    if success > 0 and off_hours == 1 and failures == 0:
        return "Anomalous Off-Hour Access", "T1078"

    return "Unknown Anomalous Activity", "T1190"
