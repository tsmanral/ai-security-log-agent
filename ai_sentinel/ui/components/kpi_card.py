"""
AI-Sentinel V3 — KPI card component.

Renders styled metric cards for the SOC dashboard.
"""

import streamlit as st


def kpi_card(
    label: str,
    value: str | int | float,
    delta: str = "",
    icon: str = "📊",
    color: str = "#4A9EFF",
) -> None:
    """
    Render a styled KPI card using Streamlit's st.markdown.

    Args:
        label: KPI label text.
        value: The primary metric value.
        delta: Optional delta/change indicator.
        icon: Emoji icon for the card.
        color: Accent color (hex).
    """
    delta_html = ""
    if delta:
        delta_color = "#10B981" if not delta.startswith("-") else "#FF4444"
        delta_html = f'<span style="color:{delta_color};font-size:0.85rem;">{delta}</span>'

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1A1F2E 0%, #1E2536 100%);
            border-left: 3px solid {color};
            border-radius: 8px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.5rem;
        ">
            <div style="color:#8899AA;font-size:0.8rem;margin-bottom:0.3rem;">
                {icon} {label}
            </div>
            <div style="color:#E0E0E0;font-size:1.8rem;font-weight:700;line-height:1.2;">
                {value}
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
