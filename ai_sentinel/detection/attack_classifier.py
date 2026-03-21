"""
AI-Sentinel V2 — Attack classifier.

Maps ML-flagged anomalies to specific threat types via the rule engine.
"""

from typing import Any, Dict, Tuple

from ai_sentinel.detection.rule_engine import evaluate_rules


class AttackClassifier:
    """Classify anomalies using heuristic rules when ML flags them."""

    @staticmethod
    def classify(is_anomaly: bool, feature_row: Dict[str, Any]) -> Tuple[str, str]:
        """
        Returns (Threat Name, MITRE Technique ID) or ("None", "N/A")
        if not an anomaly.
        """
        if not is_anomaly:
            return "None", "N/A"
        return evaluate_rules(feature_row)
