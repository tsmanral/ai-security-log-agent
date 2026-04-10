"""
AI-Sentinel V3 — Dashboard data layer.

Centralized data access for the Streamlit dashboard. Provides cached
query functions so multiple components don't issue duplicate DB hits.
All functions use Streamlit's TTL cache for performance.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from ai_sentinel.storage.database import (
    get_all_devices,
    get_all_incidents,
    get_anomalies_for_device,
    get_anomalies_for_incident,
    get_anomalies_for_user,
    get_connection,
    get_devices_for_user,
    get_drift_records,
    get_events_for_user,
    get_latest_model,
    get_metrics_timeseries,
    get_open_incidents,
    get_recent_anomalies,
    get_threat_intel,
)

logger = logging.getLogger(__name__)


@st.cache_data(ttl=30)
def get_dashboard_metrics(device_id: Optional[str], start: str, end: str) -> List[Dict]:
    """Query metrics_5min for a device within a time range."""
    if not device_id:
        # Aggregate across all devices
        conn = get_connection()
        rows = conn.execute(
            """SELECT window_start,
                      SUM(event_count) as event_count,
                      SUM(anomaly_count) as anomaly_count,
                      AVG(avg_severity) as avg_severity,
                      MAX(max_severity) as max_severity,
                      SUM(unique_ips) as unique_ips,
                      SUM(unique_users) as unique_users
               FROM metrics_5min
               WHERE window_start BETWEEN ? AND ?
               GROUP BY window_start
               ORDER BY window_start ASC""",
            (start, end),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    return get_metrics_timeseries(device_id, start, end)


@st.cache_data(ttl=15)
def get_dashboard_incidents(status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Get incidents for the dashboard, optionally filtered."""
    if status:
        return get_all_incidents(status=status, limit=limit)
    return get_all_incidents(limit=limit)


@st.cache_data(ttl=15)
def get_dashboard_open_incidents() -> List[Dict]:
    """Get currently open incidents."""
    return get_open_incidents(limit=200)


@st.cache_data(ttl=30)
def get_incident_anomalies(incident_id: int) -> List[Dict]:
    """Get anomalies for a specific incident with event details."""
    return get_anomalies_for_incident(incident_id)


@st.cache_data(ttl=15)
def get_dashboard_recent_anomalies(limit: int = 50) -> List[Dict]:
    """Get recent anomalies across all devices."""
    return get_recent_anomalies(limit=limit)


@st.cache_data(ttl=30)
def get_shap_for_anomaly(anomaly_id: int) -> Dict[str, float]:
    """Read SHAP values from the anomalies table for a specific anomaly."""
    conn = get_connection()
    row = conn.execute(
        "SELECT shap_values FROM anomalies WHERE id = ?", (anomaly_id,)
    ).fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


@st.cache_data(ttl=60)
def get_dashboard_devices() -> List[Dict]:
    """Get all registered devices."""
    return get_all_devices()


@st.cache_data(ttl=60)
def get_dashboard_model_info(model_name: str) -> Optional[Dict]:
    """Get the latest model registry entry."""
    return get_latest_model(model_name)


@st.cache_data(ttl=60)
def get_dashboard_drift(model_name: str, limit: int = 50) -> List[Dict]:
    """Get recent drift measurements for a model."""
    return get_drift_records(model_name, limit)


@st.cache_data(ttl=30)
def get_dashboard_kpis() -> Dict[str, Any]:
    """Compute high-level KPIs for the dashboard overview."""
    conn = get_connection()
    try:
        # Total events (last 24h)
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        event_row = conn.execute(
            "SELECT COUNT(*) FROM normalized_events WHERE timestamp > ?", (cutoff,)
        ).fetchone()
        total_events_24h = event_row[0] if event_row else 0

        # Total anomalies (last 24h)
        anomaly_row = conn.execute(
            "SELECT COUNT(*) FROM anomalies WHERE created_at > ? AND is_anomaly = 1",
            (cutoff,),
        ).fetchone()
        total_anomalies_24h = anomaly_row[0] if anomaly_row else 0

        # Open incidents
        incident_row = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE status IN ('OPEN', 'INVESTIGATING')"
        ).fetchone()
        open_incidents = incident_row[0] if incident_row else 0

        # Critical incidents
        critical_row = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE severity_label = 'CRITICAL' AND status IN ('OPEN', 'INVESTIGATING')"
        ).fetchone()
        critical_incidents = critical_row[0] if critical_row else 0

        # Active devices
        threshold = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        device_row = conn.execute(
            "SELECT COUNT(*) FROM devices WHERE last_seen_at > ?", (threshold,)
        ).fetchone()
        active_devices = device_row[0] if device_row else 0

        # Total devices
        total_row = conn.execute("SELECT COUNT(*) FROM devices").fetchone()
        total_devices = total_row[0] if total_row else 0

        return {
            "total_events_24h": total_events_24h,
            "total_anomalies_24h": total_anomalies_24h,
            "open_incidents": open_incidents,
            "critical_incidents": critical_incidents,
            "active_devices": active_devices,
            "total_devices": total_devices,
        }
    finally:
        conn.close()
