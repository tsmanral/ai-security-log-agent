"""
AI-Sentinel V2 — Abstract base class for anomaly detectors.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd

from ai_sentinel.features.feature_extractor import FEATURE_COLS


class BaseAnomalyDetector(ABC):
    """Interface that all Layer-2 / Layer-3 detectors must implement."""

    def __init__(self, name: str):
        self.name = name
        self.features: List[str] = list(FEATURE_COLS)
        self.is_fitted: bool = False

    @abstractmethod
    def train(self, df: pd.DataFrame) -> None:
        """Train on feature data (assumed mostly normal)."""
        ...

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Score each row.

        Returns list of dicts with at least:
            ``is_anomaly`` (bool), ``anomaly_score`` (float), ``model_name`` (str).
        """
        ...
