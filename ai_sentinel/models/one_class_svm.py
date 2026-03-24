"""
AI-Sentinel V2 — One-Class SVM detector (Layer 2).
"""

from typing import Any, Dict, List

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from ai_sentinel.models.base_model import BaseAnomalyDetector
from ai_sentinel.config import ENSEMBLE_CONTAMINATION


class OneClassSVMModel(BaseAnomalyDetector):
    """One-Class SVM anomaly detector with auto-scaling."""

    def __init__(self, nu: float = ENSEMBLE_CONTAMINATION, kernel: str = "rbf"):
        super().__init__("One_Class_SVM")
        self.model = OneClassSVM(nu=nu, kernel=kernel, gamma="scale")
        self.scaler = StandardScaler()

    def train(self, df: pd.DataFrame) -> None:
        X = self.scaler.fit_transform(df[self.features])
        self.model.fit(X)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.is_fitted:
            raise RuntimeError(f"{self.name} is not fitted.")
        X = self.scaler.transform(df[self.features])
        preds = self.model.predict(X)
        scores = -self.model.score_samples(X)
        return [
            {"is_anomaly": bool(p == -1), "anomaly_score": float(s), "model_name": self.name}
            for p, s in zip(preds, scores)
        ]
