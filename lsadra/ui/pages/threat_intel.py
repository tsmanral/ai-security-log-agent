"""
LSADRA V3 — Threat Intelligence page.

Displays cached threat intelligence data, allows manual IP lookups,
and provides inline enrichment for IPs seen in anomalies.
"""

import streamlit as st

from lsadra.storage.database import get_connection, get_threat_intel
from lsadra.ui.components.chart_theme import apply_soc_theme, SEVERITY_COLORS
from lsadra.ui.components.kpi_card import kpi_card


# Simulated threat intel for known bad IPs (used when no AbuseIPDB key is set)
_BUILTIN_INTEL = {
    "185.15.202.13": {
        "abuse_score": 92, "country_code": "RU", "isp": "Rostelecom",
        "domain": "rostelecom.ru", "total_reports": 847, "is_tor": False,
        "last_reported": "2026-04-01T12:00:00",
    },
    "45.33.32.156": {
        "abuse_score": 78, "country_code": "US", "isp": "Linode LLC",
        "domain": "scanme.nmap.org", "total_reports": 1203, "is_tor": False,
        "last_reported": "2026-04-02T08:30:00",
    },
    "103.20.150.2": {
        "abuse_score": 85, "country_code": "CN", "isp": "China Telecom",
        "domain": "chinatelecom.com.cn", "total_reports": 432, "is_tor": False,
        "last_reported": "2026-03-30T18:45:00",
    },
    "89.187.160.10": {
        "abuse_score": 65, "country_code": "NL", "isp": "DataCamp Limited",
        "domain": "datacamp.co.uk", "total_reports": 256, "is_tor": True,
        "last_reported": "2026-04-01T22:15:00",
    },
}


def _ensure_intel_cache():
    """Seed threat intel cache with built-in data for IPs seen in anomalies."""
    conn = get_connection()
    # Find unique external IPs from anomalies that aren't in the cache
    anomaly_ips = conn.execute(
        """SELECT DISTINCT source_ip FROM anomalies
           WHERE is_anomaly = 1 AND source_ip IS NOT NULL
                 AND source_ip NOT LIKE '192.168.%'
                 AND source_ip NOT LIKE '10.%'
                 AND source_ip NOT LIKE '172.%'"""
    ).fetchall()
    anomaly_ips = [r[0] for r in anomaly_ips]

    for ip in anomaly_ips:
        existing = conn.execute(
            "SELECT 1 FROM threat_intel_cache WHERE ip_address = ?", (ip,)
        ).fetchone()
        if not existing and ip in _BUILTIN_INTEL:
            intel = _BUILTIN_INTEL[ip]
            conn.execute(
                """INSERT INTO threat_intel_cache
                   (ip_address, abuse_score, country_code, isp, domain,
                    total_reports, is_tor, last_reported, queried_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now', '+7 days'))""",
                (ip, intel["abuse_score"], intel["country_code"], intel["isp"],
                 intel["domain"], intel["total_reports"], intel["is_tor"],
                 intel["last_reported"]),
            )
    conn.commit()
    conn.close()


def render():
    """Render the Threat Intelligence page."""
    st.title("🔍 Threat Intelligence")

    # Auto-seed cache with built-in intel for known IPs
    _ensure_intel_cache()

    # ── IP Reputation Lookup ──────────────────────────────────────────────
    st.subheader("IP Reputation Lookup")
    col1, col2 = st.columns([3, 1])
    with col1:
        ip_input = st.text_input("Enter IP address", placeholder="e.g. 45.33.32.156")
    with col2:
        st.write("")
        lookup_btn = st.button("🔎 Lookup", use_container_width=True)

    if lookup_btn and ip_input:
        cached = get_threat_intel(ip_input)

        # Fallback to built-in intel
        if not cached and ip_input in _BUILTIN_INTEL:
            cached = _BUILTIN_INTEL[ip_input]

        if cached:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                score = cached.get("abuse_score", 0)
                color = "#FF4444" if score > 50 else "#FFD700" if score > 20 else "#10B981"
                kpi_card("Abuse Score", score, icon="⚠️", color=color)
            with c2:
                kpi_card("Country", cached.get("country_code", "N/A"), icon="🌍", color="#4A9EFF")
            with c3:
                kpi_card("Reports", cached.get("total_reports", 0), icon="📊", color="#7C3AED")
            with c4:
                tor_label = "Yes ⚡" if cached.get("is_tor") else "No"
                tor_color = "#FF4444" if cached.get("is_tor") else "#10B981"
                kpi_card("Tor Exit Node", tor_label, icon="🧅", color=tor_color)

            st.markdown("**Full Intel Report:**")
            st.json({
                "ip": ip_input,
                "isp": cached.get("isp", ""),
                "domain": cached.get("domain", ""),
                "is_tor": cached.get("is_tor", False),
                "abuse_score": cached.get("abuse_score", 0),
                "total_reports": cached.get("total_reports", 0),
                "country_code": cached.get("country_code", ""),
                "last_reported": cached.get("last_reported", ""),
                "queried_at": cached.get("queried_at", ""),
            })
        else:
            st.warning(f"No intelligence available for {ip_input}.")
            st.info("Tip: Try one of the known attacker IPs from the fleet simulator: "
                    "`185.15.202.13`, `45.33.32.156`, `103.20.150.2`, `89.187.160.10`")

    st.divider()

    # ── Cached Threat Intel Table ─────────────────────────────────────────
    st.subheader("Cached Threat Intel")
    conn = get_connection()
    rows = conn.execute(
        """SELECT ip_address, abuse_score, country_code, isp, total_reports, is_tor, queried_at
           FROM threat_intel_cache
           ORDER BY abuse_score DESC LIMIT 100"""
    ).fetchall()
    conn.close()

    if rows:
        data = []
        for r in rows:
            r = dict(r)
            score = r.get("abuse_score", 0)
            risk = "🔴 High" if score > 50 else "🟡 Medium" if score > 20 else "🟢 Low"
            data.append({
                "IP": r.get("ip_address", ""),
                "Risk": risk,
                "Abuse Score": score,
                "Country": r.get("country_code", ""),
                "ISP": r.get("isp", ""),
                "Reports": r.get("total_reports", 0),
                "Tor": "🧅 Yes" if r.get("is_tor") else "No",
                "Queried": r.get("queried_at", ""),
            })
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("No threat intelligence data cached. Data appears after anomalous IPs are detected.")

    st.divider()

    # ── Anomalous IPs Overview ────────────────────────────────────────────
    st.subheader("Anomalous IPs in Your Environment")
    conn = get_connection()
    ip_rows = conn.execute(
        """SELECT source_ip, COUNT(*) as anomaly_count,
                  MAX(severity_score) as max_severity,
                  MAX(created_at) as last_seen
           FROM anomalies
           WHERE is_anomaly = 1 AND source_ip IS NOT NULL
                 AND source_ip NOT LIKE '192.168.%'
                 AND source_ip NOT LIKE '10.%'
           GROUP BY source_ip
           ORDER BY anomaly_count DESC LIMIT 20"""
    ).fetchall()
    conn.close()

    if ip_rows:
        import plotly.graph_objects as go
        df_ips = []
        for r in ip_rows:
            r = dict(r)
            df_ips.append(r)

        fig = go.Figure(data=[go.Bar(
            x=[r["source_ip"] for r in df_ips],
            y=[r["anomaly_count"] for r in df_ips],
            marker_color=["#FF4444" if r["max_severity"] > 0.7 else "#FFD700" if r["max_severity"] > 0.4 else "#4A9EFF"
                          for r in df_ips],
            text=[r["anomaly_count"] for r in df_ips],
            textposition="outside",
        )])
        apply_soc_theme(fig, title="Top Anomalous External IPs")
        fig.update_layout(xaxis_title="Source IP", yaxis_title="Anomaly Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No external anomalous IPs detected yet.")
