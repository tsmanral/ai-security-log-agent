"""
LSADRA V3 — Auto-refresh component.

Provides an auto-refresh toggle for live dashboard pages using
Streamlit's st.rerun mechanism.
"""

import time
import streamlit as st


def auto_refresh_toggle(
    default_interval: int = 30,
    key: str = "auto_refresh",
) -> None:
    """
    Render an auto-refresh toggle in the sidebar.

    When enabled, the page will automatically rerun after the interval.

    Args:
        default_interval: Default refresh interval in seconds.
        key: Streamlit widget key prefix.
    """
    col1, col2 = st.sidebar.columns([1, 1])

    with col1:
        enabled = st.toggle("Auto-Refresh", value=False, key=f"{key}_toggle")
    with col2:
        interval = st.number_input(
            "Interval (s)",
            min_value=5,
            max_value=300,
            value=default_interval,
            step=5,
            key=f"{key}_interval",
        )

    if enabled:
        st.sidebar.caption(f"🔄 Refreshing every {interval}s")
        time.sleep(interval)
        st.rerun()
