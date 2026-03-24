"""
AI-Sentinel V2 — Local Outlier Factor detector (Layer 2).
"""

from typing import Any, Dict, List

import pandas as pd
from sklearn.neighbors import LocalOutlierFactor

from ai_sentinel.models.base_model import BaseAnomalyDetector
from ai_sentinel.config import ENSEMBLE_CONTAMINATION


class LOFModel(BaseAnomalyDetector):
    """Local Outlier Factor anomaly detector (novelty mode)."""

    def __init__(self, contamination: float = ENSEMBLE_CONTAMINATION, n_neighbors: int = 25):
        super().__init__("Local_Outlier_Factor")
        self.model = LocalOutlierFactor(
            n_neighbors=n_neighbors, contamination=contamination, novelty=True, n_jobs=-1
        )

    def train(self, df: pd.DataFrame) -> None:
        self.model.fit(df[self.features])
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.is_fitted:
            raise RuntimeError(f"{self.name} is not fitted.")
        X = df[self.features]
        preds = self.model.predict(X)
        scores = -self.model.score_samples(X)
        return [
            {"is_anomaly": bool(p == -1), "anomaly_score": float(s), "model_name": self.name}
            for p, s in zip(preds, scores)
        ]
