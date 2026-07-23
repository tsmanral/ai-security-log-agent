"""
LSADRA V3 — Sidebar filters component.

Provides reusable sidebar filters for the SOC dashboard pages.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from lsadra.storage.database import get_all_devices


def device_filter(key: str = "device_filter") -> Optional[str]:
    """Render a device selector in the sidebar. Returns selected device_id or None."""
    devices = get_all_devices()
    if not devices:
        st.sidebar.info("No devices registered.")
        return None

    options = {"All Devices": None}
    for d in devices:
        label = f"{d.get('display_name') or d['hostname']} ({d['os_type']}) — {d.get('status', '?')}"
        options[label] = d["id"]

    selected = st.sidebar.selectbox("Device", list(options.keys()), key=key)
    return options[selected]


def time_range_filter(key: str = "time_filter") -> Tuple[str, str]:
    """Render a time range selector. Returns (start_iso, end_iso)."""
    preset = st.sidebar.selectbox(
        "Time Range",
        ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
        index=2,
        key=key,
    )

    now = datetime.utcnow()
    delta_map = {
        "Last 1 Hour": timedelta(hours=1),
        "Last 6 Hours": timedelta(hours=6),
        "Last 24 Hours": timedelta(hours=24),
        "Last 7 Days": timedelta(days=7),
        "Last 30 Days": timedelta(days=30),
    }
    start = now - delta_map.get(preset, timedelta(hours=24))
    return start.isoformat(), now.isoformat()


def severity_filter(key: str = "severity_filter") -> List[str]:
    """Render a severity multi-select. Returns list of selected severity labels."""
    options = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    selected = st.sidebar.multiselect(
        "Severity",
        options,
        default=options,
        key=key,
    )
    return selected


def status_filter(key: str = "status_filter") -> Optional[str]:
    """Render an incident status filter. Returns selected status or None."""
    options = ["All", "OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"]
    selected = st.sidebar.selectbox("Status", options, key=key)
    return None if selected == "All" else selected
