"""
AI-Sentinel V2 — Detection orchestrator.

Runs the 4-layer detection stack (statistical baseline → ensemble →
autoencoder → rules + narrative) in both **online** and **batch** modes.
"""

import logging
import time
from typing import Any, Dict, List

import pandas as pd

from ai_sentinel.config import DETECTION_THROTTLE_SECONDS
from ai_sentinel.features.feature_extractor import FEATURE_COLS, build_features
from ai_sentinel.models.autoencoder_model import AutoencoderModel
from ai_sentinel.models.ensemble_model import EnsembleModel
from ai_sentinel.models.statistical_baseline import StatisticalBaselineModel
from ai_sentinel.session.session_builder import SessionBuilder
from ai_sentinel.session.user_profile_store import UserProfileStore
from ai_sentinel.storage.database import (
    get_events_since,
    get_watermark,
    insert_anomaly,
    set_watermark,
)

logger = logging.getLogger(__name__)


class DetectionOrchestrator:
    """
    Central orchestration for all detection layers.

    Maintains in-memory model state; in production this would be
    checkpointed to disk between restarts.
    """

    def __init__(self) -> None:
        self.baseline = StatisticalBaselineModel()
        self.ensemble = EnsembleModel()
        self.autoencoder = AutoencoderModel()
        self.session_builder = SessionBuilder()
        self.profile_store = UserProfileStore()
        self._last_run: Dict[str, float] = {}  # device_id → timestamp of last run
        self._trained = False

    # ── train (batch pre-load) ────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> None:
        """
        Train all model layers on historical baseline data.

        Args:
            df: DataFrame with feature columns (output of ``build_features``).
        """
        self.baseline.train(df)
        self.ensemble.train(df)
        self.autoencoder.train(df)
        self._trained = True
        logger.info("DetectionOrchestrator: all layers trained.")

    # ── online mode ───────────────────────────────────────────────────────

    def run_for_new_events(self, device_id: str) -> None:
        """
        Near-real-time detection for freshly ingested events.

        Throttled to at most once per ``DETECTION_THROTTLE_SECONDS`` per device.
        """
        now = time.time()
        last = self._last_run.get(device_id, 0.0)
        if now - last < DETECTION_THROTTLE_SECONDS:
            return
        self._last_run[device_id] = now

        watermark = get_watermark(device_id)
        new_events = get_events_since(device_id, after_id=watermark)
        if not new_events:
            return

        logger.info("Online detection: %d new events for device %s", len(new_events), device_id)

        # Build features from new events
        df = build_features(new_events)
        if df.empty:
            return

        # Update user profile
        user_id = new_events[0].get("user_id", "")
        self.profile_store.update(user_id, new_events)

        # Run layers (best-effort if models not yet trained — scoring returns 0)
        results = self._run_layers(df)

        # Persist anomalies
        for res in results:
            if res.get("is_anomaly"):
                insert_anomaly(res)

        # Update watermark
        max_id = max(ev.get("id", 0) for ev in new_events)
        set_watermark(device_id, max_id)

    # ── batch mode ────────────────────────────────────────────────────────

    def run_batch(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Full-dataset evaluation for benchmarking.

        Returns a list of detection result dicts (one per row).
        """
        return self._run_layers(df)

    # ── private layer pipeline ────────────────────────────────────────────

    def _run_layers(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Execute all 4 detection layers and merge verdicts."""
        from ai_sentinel.detection.rule_engine import evaluate_rules
        from ai_sentinel.explainability.narrative_builder import NarrativeBuilder

        n = len(df)

        # Layer 1 — statistical baseline
        l1 = self.baseline.score(df)

        # Layer 2 — ensemble
        if self._trained:
            l2 = self.ensemble.predict(df)
        else:
            l2 = [{"is_anomaly": False, "anomaly_score": 0.0, "votes": 0}] * n

        # Layer 3 — autoencoder
        l3 = self.autoencoder.score(df)

        # Merge and apply Layer 4 (rules + narrative)
        merged: List[Dict[str, Any]] = []
        for i in range(n):
            row = df.iloc[i]

            is_anomaly = (
                l1[i].get("is_baseline_anomaly", False)
                or l2[i].get("is_anomaly", False)
                or l3[i].get("is_ae_anomaly", False)
            )

            threat_type, mitre_id = evaluate_rules(row.to_dict()) if is_anomaly else ("None", "N/A")
            narrative = ""
            if is_anomaly:
                narrative = NarrativeBuilder.build(
                    threat_type=threat_type,
                    mitre_id=mitre_id,
                    row_data=row.to_dict(),
                    layer1_z=l1[i].get("z_max", 0.0),
                    layer2_score=l2[i].get("anomaly_score", 0.0),
                    layer3_error=l3[i].get("reconstruction_error", 0.0),
                )

            merged.append({
                "event_id": int(row.get("id", 0)),
                "device_id": str(row.get("device_id", "")),
                "user_id": str(row.get("user_id", "")),
                "layer1_score": l1[i].get("z_max", 0.0),
                "layer2_score": l2[i].get("anomaly_score", 0.0),
                "layer2_votes": l2[i].get("votes", 0),
                "layer3_score": l3[i].get("reconstruction_error", 0.0),
                "is_anomaly": is_anomaly,
                "threat_type": threat_type,
                "mitre_technique": mitre_id,
                "narrative": narrative,
                "is_synthetic": bool(row.get("is_synthetic", False)),
            })

        return merged
