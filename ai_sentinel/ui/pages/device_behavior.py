"""
AI-Sentinel V3 — Device Behavior page.

Per-device analytics: event timeline, anomaly distribution, heartbeat
status, and baselining progress.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ai_sentinel.config import MIN_BASELINE_EVENTS
from ai_sentinel.ui.components.chart_theme import PALETTE, apply_soc_theme
from ai_sentinel.ui.components.kpi_card import kpi_card
from ai_sentinel.ui.components.sidebar_filters import device_filter, time_range_filter
from ai_sentinel.ui.data_layer import get_dashboard_devices, get_dashboard_metrics


def render():
    """Render the Device Behavior page."""
    st.title("🖥️ Device Behavior")

    # Sidebar filters
    device_id = device_filter(key="device_behavior_filter")
    start, end = time_range_filter(key="device_behavior_time")

    # Device overview
    devices = get_dashboard_devices()

    if not devices:
        st.info("No devices registered yet.")
        return

    # Device status cards
    st.subheader("Device Fleet")
    online = sum(1 for d in devices if d.get("status") == "ONLINE")
    offline = sum(1 for d in devices if d.get("status") == "OFFLINE")
    baselining = sum(1 for d in devices if d.get("status") == "BASELINING")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Devices", len(devices), icon="🖥️", color="#4A9EFF")
    with c2:
        kpi_card("Online", online, icon="🟢", color="#10B981")
    with c3:
        kpi_card("Offline", offline, icon="🔴", color="#FF4444")
    with c4:
        kpi_card("Baselining", baselining, icon="⏳", color="#FFD700")

    st.divider()

    # Device table
    device_data = []
    for d in devices:
        status_icon = {"ONLINE": "🟢", "OFFLINE": "🔴", "BASELINING": "⏳"}.get(d.get("status", ""), "❓")
        event_count = d.get("event_count", 0)

        # Baselining progress
        if d.get("status") == "BASELINING":
            progress = f"{event_count}/{MIN_BASELINE_EVENTS} ({100 * event_count / MIN_BASELINE_EVENTS:.0f}%)"
        else:
            progress = "Complete"

        device_data.append({
            "Status": f"{status_icon} {d.get('status', '?')}",
            "Hostname": d.get("display_name") or d.get("hostname", ""),
            "OS": d.get("os_type", ""),
            "Events": event_count,
            "Baseline": progress,
            "Last Seen": d.get("last_seen_at", "Never"),
        })

    st.dataframe(device_data, use_container_width=True)

    st.divider()

    # Metrics timeline (if device selected or all)
    st.subheader("Event & Anomaly Timeline")
    metrics = get_dashboard_metrics(device_id, start, end)

    if metrics:
        import pandas as pd
        df = pd.DataFrame(metrics)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["window_start"], y=df["event_count"],
            name="Events", line=dict(color=PALETTE[0], width=2),
            fill="tozeroy", fillcolor="rgba(74, 158, 255, 0.1)",
        ))
        fig.add_trace(go.Scatter(
            x=df["window_start"], y=df["anomaly_count"],
            name="Anomalies", line=dict(color=PALETTE[3], width=2),
            yaxis="y2",
        ))
        fig.update_layout(
            yaxis2=dict(
                title="Anomalies", overlaying="y", side="right",
                gridcolor="#2A2F3E",
            ),
        )
        apply_soc_theme(fig, title="Events vs. Anomalies Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No metrics data available for the selected time range.")
