"""
AI-Sentinel V3 — Live Alerts page.

Real-time view of recent anomalies with severity badges, auto-refresh,
incident linkage, and clickable KPI drill-downs.
"""

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ai_sentinel.storage.database import get_connection
from ai_sentinel.ui.components.auto_refresh import auto_refresh_toggle
from ai_sentinel.ui.components.chart_theme import apply_soc_theme, get_severity_color, SEVERITY_COLORS
from ai_sentinel.ui.components.kpi_card import kpi_card
from ai_sentinel.ui.components.severity_badge import severity_badge
from ai_sentinel.ui.components.sidebar_filters import severity_filter
from ai_sentinel.ui.data_layer import get_dashboard_kpis, get_dashboard_recent_anomalies


def render():
    """Render the Live Alerts page."""
    st.title("🚨 Live Alerts")

    # Sidebar
    auto_refresh_toggle(default_interval=15, key="alerts_refresh")
    selected_severity = severity_filter(key="alerts_severity")

    # KPIs with drill-down buttons
    kpis = get_dashboard_kpis()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Events (24h)", f"{kpis['total_events_24h']:,}", icon="📨", color="#4A9EFF")
        if st.button("Details", key="la_drill_events", use_container_width=True):
            st.session_state["la_drill"] = "events"
    with c2:
        kpi_card("Anomalies (24h)", f"{kpis['total_anomalies_24h']:,}", icon="⚡", color="#FF8C00")
        if st.button("Details", key="la_drill_anomalies", use_container_width=True):
            st.session_state["la_drill"] = "anomalies"
    with c3:
        kpi_card("Open Incidents", kpis["open_incidents"], icon="📋", color="#FFD700")
        if st.button("Details", key="la_drill_incidents", use_container_width=True):
            st.session_state["la_drill"] = "incidents"
    with c4:
        kpi_card("Critical", kpis["critical_incidents"], icon="🔴", color="#FF4444")

    # ── KPI Drill-Down Panel ──────────────────────────────────────────────
    drill = st.session_state.get("la_drill")
    if drill:
        st.divider()
        _render_drill(drill)
        if st.button("✖ Close", key="la_close_drill"):
            del st.session_state["la_drill"]
            st.rerun()

    st.divider()

    # ── Alert Timeline (mini chart) ───────────────────────────────────────
    anomalies = get_dashboard_recent_anomalies(limit=200)
    if selected_severity:
        anomalies = [a for a in anomalies if a.get("severity_label") in selected_severity]

    if anomalies:
        df = pd.DataFrame(anomalies)
        if "created_at" in df.columns:
            df["hour"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:00")
            hourly = df.groupby(["hour", "severity_label"]).size().reset_index(name="count")

            if not hourly.empty:
                fig = go.Figure()
                for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                    sev_data = hourly[hourly["severity_label"] == sev]
                    if not sev_data.empty:
                        fig.add_trace(go.Bar(
                            x=sev_data["hour"],
                            y=sev_data["count"],
                            name=sev,
                            marker_color=SEVERITY_COLORS.get(sev, "#888"),
                        ))
                fig.update_layout(barmode="stack")
                apply_soc_theme(fig, title="Alert Volume (by severity)")
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Alerts",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    height=280,
                )
                st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Alert Feed ────────────────────────────────────────────────────────
    if not anomalies:
        st.success("No anomalies detected 🎉")
        return

    st.subheader(f"Recent Alerts ({len(anomalies)})")

    for a in anomalies:
        sev = a.get("severity_label", "LOW")
        threat = a.get("threat_type", "Unknown")
        ts = a.get("created_at", "")
        score = a.get("severity_score", 0)

        with st.expander(f"{_sev_icon(sev)} **{threat}** — {sev} ({score:.2f}) — {ts}", expanded=False):
            severity_badge(sev, score)

            narrative = a.get("narrative", "No narrative available.")
            if narrative and narrative != "No narrative available.":
                st.markdown(narrative)
            else:
                st.info("Narrative will be generated when ML models are trained.")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Baseline Z", f"{a.get('layer1_score', 0):.2f}")
            c2.metric("Ensemble", f"{a.get('layer2_score', 0):.2f}")
            c3.metric("AE Error", f"{a.get('layer3_score', 0):.4f}")
            c4.metric("Severity", f"{score:.2f}")

            st.caption(
                f"MITRE: {a.get('mitre_technique', 'N/A')} | "
                f"Device: `{str(a.get('device_id', ''))[:8]}...` | "
                f"IP: {a.get('source_ip', 'N/A')} | "
                f"Incident: #{a.get('incident_id', 'N/A')}"
            )


def _sev_icon(label: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(label, "⚪")


def _render_drill(drill: str):
    """Render KPI drill-down panels."""
    conn = get_connection()

    if drill == "events":
        st.subheader("📨 Recent Events")
        rows = conn.execute(
            """SELECT timestamp, host, effective_username, source_ip, event_type
               FROM normalized_events
               ORDER BY timestamp DESC LIMIT 100"""
        ).fetchall()
        if rows:
            st.dataframe([dict(r) for r in rows], use_container_width=True, hide_index=True)
        else:
            st.info("No events yet.")

    elif drill == "anomalies":
        st.subheader("⚡ Recent Anomalies")
        rows = conn.execute(
            """SELECT created_at, threat_type, severity_label, severity_score,
                      mitre_technique, source_ip
               FROM anomalies WHERE is_anomaly = 1
               ORDER BY created_at DESC LIMIT 50"""
        ).fetchall()
        if rows:
            st.dataframe([dict(r) for r in rows], use_container_width=True, hide_index=True)
        else:
            st.info("No anomalies yet.")

    elif drill == "incidents":
        st.subheader("📋 Open Incidents")
        rows = conn.execute(
            """SELECT id, attack_type, severity_label,
                      status, first_seen, source_ip, anomaly_count
               FROM incidents WHERE status IN ('OPEN', 'INVESTIGATING')
               ORDER BY anomaly_count DESC LIMIT 50"""
        ).fetchall()
        if rows:
            st.dataframe([dict(r) for r in rows], use_container_width=True, hide_index=True)
        else:
            st.success("No open incidents!")

    conn.close()
