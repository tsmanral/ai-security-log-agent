"""
LSADRA V3 — Severity badge component.

Renders colour-coded severity badges for use in alerts, incidents, and tables.
"""

import streamlit as st


_BADGE_STYLES = {
    "CRITICAL": {"bg": "#3D1111", "border": "#FF4444", "text": "#FF6666", "icon": "🔴"},
    "HIGH":     {"bg": "#3D2811", "border": "#FF8C00", "text": "#FFAA33", "icon": "🟠"},
    "MEDIUM":   {"bg": "#3D3511", "border": "#FFD700", "text": "#FFE44D", "icon": "🟡"},
    "LOW":      {"bg": "#113D28", "border": "#00CC88", "text": "#33DDAA", "icon": "🟢"},
}


def severity_badge(label: str, score: float = 0.0, inline: bool = False) -> None:
    """
    Render a severity badge.

    Args:
        label: Severity label (CRITICAL, HIGH, MEDIUM, LOW).
        score: Optional numeric score to display.
        inline: If True, render inline (no block margin).
    """
    style = _BADGE_STYLES.get(label, _BADGE_STYLES["LOW"])
    display = "inline-block" if inline else "block"
    score_html = f" ({score:.2f})" if score > 0 else ""

    st.markdown(
        f"""
        <span style="
            display: {display};
            background: {style['bg']};
            border: 1px solid {style['border']};
            color: {style['text']};
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.05em;
        ">
            {style['icon']} {label}{score_html}
        </span>
        """,
        unsafe_allow_html=True,
    )


def severity_dot(label: str) -> str:
    """Return a severity emoji dot for use in tables/text."""
    return _BADGE_STYLES.get(label, _BADGE_STYLES["LOW"])["icon"]
