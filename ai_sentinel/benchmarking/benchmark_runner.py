"""
AI-Sentinel V2 — Benchmark runner.

Runs the full detection stack against synthetic scenarios to measure
detection rates and latency.
"""

import logging
import time
from typing import Any, Dict, List

import pandas as pd

from ai_sentinel.benchmarking.synthetic_scenarios import SyntheticScenarioGenerator
from ai_sentinel.detection.detection_orchestrator import DetectionOrchestrator
from ai_sentinel.features.feature_extractor import build_features

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Execute synthetic scenarios against the detection stack."""

    def __init__(self, orchestrator: DetectionOrchestrator):
        self.orchestrator = orchestrator

    def run(self) -> Dict[str, Any]:
        """
        Train on normal traffic then evaluate each attack scenario.

        Returns a dict mapping scenario name → detection stats.
        """
        gen = SyntheticScenarioGenerator()
        results: Dict[str, Any] = {}

        # 1. Generate normal data and train
        logger.info("Benchmark: generating normal traffic for training …")
        normal = gen.normal_traffic(count=800)
        normal_df = build_features(normal)
        self.orchestrator.train(normal_df)

        # 2. Evaluate each attack scenario
        for name, events in [
            ("brute_force", gen.brute_force()),
            ("credential_stuffing", gen.credential_stuffing()),
            ("off_hour_access", gen.off_hour_access()),
        ]:
            logger.info("Benchmark: running scenario '%s' …", name)
            df = build_features(events)
            if df.empty:
                results[name] = {"total": 0, "detected": 0, "rate": 0.0}
                continue

            t0 = time.time()
            detections = self.orchestrator.run_batch(df)
            elapsed = time.time() - t0

            detected = sum(1 for d in detections if d["is_anomaly"])
            results[name] = {
                "total": len(detections),
                "detected": detected,
                "rate": detected / max(len(detections), 1),
                "elapsed_s": round(elapsed, 3),
            }

        logger.info("Benchmark results: %s", results)
        return results
