"""
AI-Sentinel V2 — Layer 1: Statistical baseline anomaly detector.

Maintains per-entity (user × device) rolling means and standard deviations
for each feature.  An observation whose z-score exceeds a configurable
threshold sigma is flagged as anomalous.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ai_sentinel.config import STATISTICAL_BASELINE_SIGMA
from ai_sentinel.features.feature_extractor import FEATURE_COLS

logger = logging.getLogger(__name__)


class StatisticalBaselineModel:
    """
    Per-entity rolling z-score baseline (Layer 1).

    For each combination of ``(user_id, device_id)`` the model stores a
    running mean and standard deviation for every feature.  New observations
    are scored against these baselines using the standard z-score:

        z = (x - μ) / σ

    If max |z| across features exceeds ``STATISTICAL_BASELINE_SIGMA`` the
    observation is flagged.
    """

    def __init__(self, sigma: float = STATISTICAL_BASELINE_SIGMA):
        self.sigma = sigma
        # Keyed by (user_id, device_id) → dict of feature → (mean, std, n)
        self._profiles: Dict[Tuple[str, str], Dict[str, Tuple[float, float, int]]] = defaultdict(dict)

    # ── training ──────────────────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> None:
        """
        Build per-entity baselines from historical (normal) data.

        Args:
            df: DataFrame containing feature columns + user_id, device_id.
        """
        if df.empty:
            return

        groups = df.groupby(["user_id", "device_id"])
        for (uid, did), grp in groups:
            profile: Dict[str, Tuple[float, float, int]] = {}
            for feat in FEATURE_COLS:
                if feat in grp.columns:
                    vals = grp[feat].astype(float)
                    profile[feat] = (float(vals.mean()), float(vals.std()) + 1e-9, len(vals))
            self._profiles[(str(uid), str(did))] = profile

        logger.info("Statistical baselines built for %d entities.", len(self._profiles))

    # ── scoring ───────────────────────────────────────────────────────────

    def score(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Score each row against its entity baseline.

        Returns a list of dicts with ``z_max`` (float) and ``is_baseline_anomaly`` (bool).
        """
        results: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            key = (str(row.get("user_id", "")), str(row.get("device_id", "")))
            profile = self._profiles.get(key)

            if profile is None:
                # No baseline yet — cannot flag
                results.append({"z_max": 0.0, "is_baseline_anomaly": False})
                continue

            z_scores = []
            for feat in FEATURE_COLS:
                if feat in profile and feat in row.index:
                    mean, std, _ = profile[feat]
                    z = abs(float(row[feat]) - mean) / std
                    z_scores.append(z)

            z_max = max(z_scores) if z_scores else 0.0
            results.append({
                "z_max": z_max,
                "is_baseline_anomaly": z_max > self.sigma,
            })

        return results

    # ── online update ─────────────────────────────────────────────────────

    def update(self, row: pd.Series) -> None:
        """Incrementally update the baseline for one entity with a new observation."""
        key = (str(row.get("user_id", "")), str(row.get("device_id", "")))
        profile = self._profiles.get(key, {})

        for feat in FEATURE_COLS:
            if feat not in row.index:
                continue
            val = float(row[feat])
            if feat in profile:
                mean, std, n = profile[feat]
                n_new = n + 1
                new_mean = mean + (val - mean) / n_new
                new_std = np.sqrt(((n - 1) * std ** 2 + (val - mean) * (val - new_mean)) / max(n_new - 1, 1)) + 1e-9
                profile[feat] = (new_mean, new_std, n_new)
            else:
                profile[feat] = (val, 1e-9, 1)

        self._profiles[key] = profile
