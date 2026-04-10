"""
AI-Sentinel V3 — Analytics page.

Overview analytics with event trends, severity breakdown, top threat
types, incident statistics, and clickable KPI drill-downs.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ai_sentinel.storage.database import get_connection
from ai_sentinel.ui.components.chart_theme import (
    PALETTE,
    SEVERITY_COLORS,
    apply_soc_theme,
)
from ai_sentinel.ui.components.kpi_card import kpi_card
from ai_sentinel.ui.components.sidebar_filters import time_range_filter
from ai_sentinel.ui.data_layer import get_dashboard_kpis


def render():
    """Render the Analytics page."""
    st.title("📊 Analytics")

    start, end = time_range_filter(key="analytics_time")

    # KPIs — clickable via session state
    kpis = get_dashboard_kpis()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Events (24h)", f"{kpis['total_events_24h']:,}", icon="📨", color="#4A9EFF")
        if st.button("View Details", key="drill_events", use_container_width=True):
            st.session_state["analytics_drill"] = "events"
    with c2:
        kpi_card("Anomalies (24h)", f"{kpis['total_anomalies_24h']:,}", icon="⚡", color="#FF8C00")
        if st.button("View Details", key="drill_anomalies", use_container_width=True):
            st.session_state["analytics_drill"] = "anomalies"
    with c3:
        kpi_card("Open Incidents", kpis["open_incidents"], icon="📋", color="#FFD700")
        if st.button("View Details", key="drill_incidents", use_container_width=True):
            st.session_state["analytics_drill"] = "incidents"
    with c4:
        kpi_card("Critical", kpis["critical_incidents"], icon="🔴", color="#FF4444")
        if st.button("View Details", key="drill_critical", use_container_width=True):
            st.session_state["analytics_drill"] = "critical"

    # ── KPI Drill-Down ────────────────────────────────────────────────────
    drill = st.session_state.get("analytics_drill")
    if drill:
        st.divider()
        _render_drill_down(drill, start, end)
        if st.button("✖ Close Drill-Down"):
            del st.session_state["analytics_drill"]
            st.rerun()

    st.divider()

    # ── Event & Anomaly Timeline ──────────────────────────────────────────
    st.subheader("Event & Anomaly Timeline")

    conn = get_connection()
    timeline_rows = conn.execute(
        """SELECT
               strftime('%Y-%m-%dT%H:00:00', timestamp) as hour,
               COUNT(*) as events,
               SUM(CASE WHEN id IN (SELECT event_id FROM anomalies WHERE is_anomaly = 1) THEN 1 ELSE 0 END) as anomalies
           FROM normalized_events
           WHERE timestamp BETWEEN ? AND ?
           GROUP BY hour
           ORDER BY hour ASC""",
        (start, end),
    ).fetchall()

    if timeline_rows:
        df_tl = pd.DataFrame([dict(r) for r in timeline_rows])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_tl["hour"], y=df_tl["events"],
            mode="lines+markers",
            name="Events",
            line=dict(color="#4A9EFF", width=2),
            fill="tozeroy",
            fillcolor="rgba(74,158,255,0.1)",
            marker=dict(size=4),
        ))
        fig.add_trace(go.Scatter(
            x=df_tl["hour"], y=df_tl["anomalies"],
            mode="lines+markers",
            name="Anomalies",
            line=dict(color="#FF4444", width=2),
            fill="tozeroy",
            fillcolor="rgba(255,68,68,0.1)",
            marker=dict(size=6, symbol="diamond"),
        ))
        apply_soc_theme(fig, title="Hourly Event & Anomaly Volume")
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Count",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data for the selected period.")

    st.divider()

    # ── Severity & Threat Type (side by side) ─────────────────────────────
    sev_rows = conn.execute(
        """SELECT severity_label, COUNT(*) as cnt
           FROM anomalies
           WHERE is_anomaly = 1 AND created_at BETWEEN ? AND ?
           GROUP BY severity_label""",
        (start, end),
    ).fetchall()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Severity Distribution")
        if sev_rows:
            labels = [r[0] for r in sev_rows]
            values = [r[1] for r in sev_rows]
            colors = [SEVERITY_COLORS.get(l, "#888") for l in labels]

            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                marker=dict(colors=colors),
                hole=0.5,
                textfont_size=12,
                textinfo="label+value+percent",
            )])
            apply_soc_theme(fig, title="Anomalies by Severity")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No anomaly data for the selected period.")

    with col_right:
        st.subheader("Top Threat Types")
        threat_rows = conn.execute(
            """SELECT threat_type, COUNT(*) as cnt
               FROM anomalies
               WHERE is_anomaly = 1 AND created_at BETWEEN ? AND ?
               GROUP BY threat_type ORDER BY cnt DESC LIMIT 10""",
            (start, end),
        ).fetchall()

        if threat_rows:
            fig = go.Figure(data=[go.Bar(
                x=[r[1] for r in threat_rows],
                y=[r[0] for r in threat_rows],
                orientation="h",
                marker_color=PALETTE[:len(threat_rows)],
                text=[r[1] for r in threat_rows],
                textposition="outside",
            )])
            apply_soc_theme(fig, title="Top Threat Types")
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No threat data for the selected period.")

    st.divider()

    # ── Incident Timeline (interactive scatter timeline) ──────────────────
    st.subheader("Incident Timeline")
    incident_rows = conn.execute(
        """SELECT id, attack_type, severity_label,
                  status, first_seen, last_seen, anomaly_count,
                  source_ip, device_id
           FROM incidents
           WHERE first_seen BETWEEN ? AND ?
           ORDER BY first_seen ASC""",
        (start, end),
    ).fetchall()

    if incident_rows:
        df_inc = pd.DataFrame([dict(r) for r in incident_rows])

        size_map = df_inc["anomaly_count"].clip(lower=1)

        # Map severity labels to numeric values for Y-axis
        sev_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        df_inc["severity_num"] = df_inc["severity_label"].map(sev_order).fillna(0)

        fig = px.scatter(
            df_inc,
            x="first_seen",
            y="severity_num",
            size=size_map,
            color="severity_label",
            color_discrete_map=SEVERITY_COLORS,
            hover_data=["id", "attack_type", "status", "source_ip", "anomaly_count"],
            labels={
                "first_seen": "Time",
                "severity_num": "Severity Level",
                "severity_label": "Severity",
            },
        )
        apply_soc_theme(fig, title="Incidents Over Time (size = anomaly count)")
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Severity Level",
            yaxis=dict(range=[0, 5], tickvals=[1,2,3,4], ticktext=["LOW","MEDIUM","HIGH","CRITICAL"]),
            hovermode="closest",
        )
        fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="#0E1117")))
        st.plotly_chart(fig, use_container_width=True)

        # Incident table
        display_cols = [c for c in ["id", "attack_type", "severity_label", "status", "first_seen", "source_ip", "anomaly_count"] if c in df_inc.columns]
        st.dataframe(
            df_inc[display_cols].rename(
                columns={"id": "ID", "attack_type": "Attack", "severity_label": "Severity",
                         "status": "Status", "first_seen": "First Seen", "source_ip": "Source IP",
                         "anomaly_count": "Anomalies"}
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No incidents in the selected period.")

    conn.close()


def _render_drill_down(drill: str, start: str, end: str):
    """Render KPI drill-down detail panels."""
    conn = get_connection()

    if drill == "events":
        st.subheader("📨 Event Details (Last 24h)")
        rows = conn.execute(
            """SELECT timestamp, host, effective_username, source_ip, event_type
               FROM normalized_events
               WHERE timestamp BETWEEN ? AND ?
               ORDER BY timestamp DESC LIMIT 200""",
            (start, end),
        ).fetchall()
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Event type breakdown
            type_counts = df["event_type"].value_counts()
            fig = px.pie(values=type_counts.values, names=type_counts.index, hole=0.4)
            apply_soc_theme(fig, title="Event Type Breakdown")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No events found.")

    elif drill == "anomalies":
        st.subheader("⚡ Anomaly Details (Last 24h)")
        rows = conn.execute(
            """SELECT created_at, threat_type, severity_label, severity_score,
                      mitre_technique, source_ip, device_id
               FROM anomalies
               WHERE is_anomaly = 1 AND created_at BETWEEN ? AND ?
               ORDER BY created_at DESC LIMIT 100""",
            (start, end),
        ).fetchall()
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No anomalies found.")

    elif drill == "incidents":
        st.subheader("📋 Open Incidents")
        rows = conn.execute(
            """SELECT id, attack_type, severity_label,
                      status, first_seen, source_ip, anomaly_count
               FROM incidents
               WHERE status IN ('OPEN', 'INVESTIGATING')
               ORDER BY anomaly_count DESC LIMIT 50"""
        ).fetchall()
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No open incidents.")

    elif drill == "critical":
        st.subheader("🔴 Critical Incidents")
        rows = conn.execute(
            """SELECT id, attack_type, severity_label, status,
                      first_seen, source_ip, anomaly_count
               FROM incidents
               WHERE severity_label = 'CRITICAL' AND status IN ('OPEN', 'INVESTIGATING')
               ORDER BY anomaly_count DESC"""
        ).fetchall()
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.success("No critical incidents! 🎉")

    conn.close()
