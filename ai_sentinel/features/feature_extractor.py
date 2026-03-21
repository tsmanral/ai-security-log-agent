"""
AI-Sentinel V2 — Feature extraction orchestrator.

Merges temporal and behavioral feature pipelines and returns a clean
feature matrix alongside metadata columns.
"""

import pandas as pd
from typing import Any, Dict, List

from ai_sentinel.features.temporal_features import extract_temporal_features
from ai_sentinel.features.behavioral_features import extract_behavioral_features

# Columns the ML models consume
FEATURE_COLS: List[str] = [
    "hour_sin",
    "hour_cos",
    "is_off_hours",
    "is_weekend",
    "time_since_last_event_ip",
    "unique_users_15m",
    "failures_15m",
    "successes_15m",
    "failure_ratio_15m",
]

# Metadata preserved alongside features for tracing
META_COLS: List[str] = [
    "id",
    "timestamp",
    "device_id",
    "user_id",
    "host",
    "effective_username",
    "source_ip",
    "event_type",
    "raw_message",
    "is_synthetic",
]


def build_features(raw_events: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of normalized event dicts into a feature DataFrame.

    Args:
        raw_events: List of dicts with at least *timestamp*, *source_ip*,
                    *effective_username*, *event_type*.

    Returns:
        DataFrame with metadata columns + feature columns, NaN-filled to 0.
    """
    if not raw_events:
        return pd.DataFrame()

    df = pd.DataFrame(raw_events)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = extract_temporal_features(df)
    df = extract_behavioral_features(df)
    df.fillna(0, inplace=True)

    # Ensure all feature columns exist
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0

    available_meta = [c for c in META_COLS if c in df.columns]
    return df[available_meta + FEATURE_COLS]
