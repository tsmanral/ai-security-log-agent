"""
AI-Sentinel V2 — SHAP aggregator.

Aggregates SHAP values across multiple ensemble sub-models and groups
features into semantic categories for the narrative builder.
"""

from typing import Any, Dict, List

FEATURE_GROUPS: Dict[str, List[str]] = {
    "Temporal": ["hour_sin", "hour_cos", "is_off_hours", "is_weekend"],
    "Velocity": ["time_since_last_event_ip"],
    "Behavioral": ["failures_15m", "successes_15m", "failure_ratio_15m", "unique_users_15m"],
}


class ShapAggregator:
    """
    Aggregate per-model SHAP explanations into group-level importance
    scores used by the narrative builder.
    """

    @staticmethod
    def aggregate(shap_dicts: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Average SHAP values across models and return per-feature means.
        """
        if not shap_dicts:
            return {}
        all_features = set()
        for d in shap_dicts:
            all_features.update(d.keys())

        agg: Dict[str, float] = {}
        for feat in all_features:
            vals = [d.get(feat, 0.0) for d in shap_dicts]
            agg[feat] = sum(abs(v) for v in vals) / len(vals)

        return dict(sorted(agg.items(), key=lambda kv: kv[1], reverse=True))

    @staticmethod
    def dominant_group(shap_dict: Dict[str, float]) -> str:
        """
        Determine which feature group contributes most to the anomaly.
        """
        group_scores: Dict[str, float] = {}
        for gname, feats in FEATURE_GROUPS.items():
            group_scores[gname] = sum(abs(shap_dict.get(f, 0.0)) for f in feats)

        if not group_scores:
            return "Unknown"

        return max(group_scores, key=group_scores.get)  # type: ignore[arg-type]
