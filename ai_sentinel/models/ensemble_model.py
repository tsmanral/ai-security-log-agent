"""
AI-Sentinel V2 — Classical unsupervised ensemble (Layer 2).

Combines Isolation Forest, LOF, and One-Class SVM predictions via
majority voting with averaged anomaly scores.
"""

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ai_sentinel.models.base_model import BaseAnomalyDetector
from ai_sentinel.models.isolation_forest import IsolationForestModel
from ai_sentinel.models.local_outlier_factor import LOFModel
from ai_sentinel.models.one_class_svm import OneClassSVMModel

logger = logging.getLogger(__name__)


class EnsembleModel:
    """Majority-vote ensemble over multiple base anomaly detectors."""

    def __init__(self) -> None:
        self.models: List[BaseAnomalyDetector] = [
            IsolationForestModel(),
            LOFModel(),
            OneClassSVMModel(),
        ]

    def train(self, df: pd.DataFrame) -> None:
        """Train every base model."""
        for m in self.models:
            m.train(df)
        logger.info("Ensemble Layer-2 trained (%d models).", len(self.models))

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict with majority voting.

        Returns list of dicts per row with:
            ``is_anomaly``, ``anomaly_score`` (avg), ``votes``, ``details``.
        """
        if df.empty:
            return []

        all_preds = [m.predict(df) for m in self.models]
        n = len(df)
        results: List[Dict[str, Any]] = []

        for i in range(n):
            votes = sum(1 for mp in all_preds if mp[i]["is_anomaly"])
            avg_score = float(np.mean([mp[i]["anomaly_score"] for mp in all_preds]))
            details = [
                {"model": self.models[j].name, "is_anomaly": all_preds[j][i]["is_anomaly"],
                 "score": all_preds[j][i]["anomaly_score"]}
                for j in range(len(self.models))
            ]
            results.append({
                "is_anomaly": votes >= len(self.models) / 2,
                "anomaly_score": avg_score,
                "votes": votes,
                "total_models": len(self.models),
                "details": details,
                "model_name": "Ensemble_Voting",
            })

        return results
