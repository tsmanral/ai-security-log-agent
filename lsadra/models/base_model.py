"""
LSADRA V3 — Abstract base class for anomaly detectors.

Adds ``save()`` and ``load()`` methods for model persistence via joblib.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from lsadra.config import MODEL_DIR
from lsadra.features.feature_extractor import FEATURE_COLS

logger = logging.getLogger(__name__)


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

    # ── persistence ───────────────────────────────────────────────────────

    def _model_path(self) -> Path:
        """Return the default file path for this model's persisted state."""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        return MODEL_DIR / f"{self.name}.joblib"

    def save(self, path: Path | None = None) -> Path:
        """
        Persist the model to disk using joblib.

        Args:
            path: Optional custom path. Defaults to ``data/models/<name>.joblib``.

        Returns:
            The path the model was saved to.
        """
        import joblib

        target = path or self._model_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, str(target))
        logger.info("Model '%s' saved to %s", self.name, target)
        return target

    @classmethod
    def load(cls, path: Path) -> "BaseAnomalyDetector":
        """
        Load a persisted model from disk.

        Args:
            path: Path to the .joblib file.

        Returns:
            The deserialized model instance.
        """
        import joblib

        model = joblib.load(str(path))
        logger.info("Model '%s' loaded from %s", model.name, path)
        return model
