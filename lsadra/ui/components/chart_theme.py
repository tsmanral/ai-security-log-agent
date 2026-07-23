"""
LSADRA V3 — Plotly chart theme.

Consistent dark SOC-style theme for all Plotly charts across the dashboard.
"""

_SOC_COLORS = {
    "bg": "#0E1117",
    "paper": "#1A1F2E",
    "grid": "#2A2F3E",
    "text": "#E0E0E0",
    "muted_text": "#8899AA",
    "critical": "#FF4444",
    "high": "#FF8C00",
    "medium": "#FFD700",
    "low": "#00CC88",
    "info": "#4A9EFF",
    "accent": "#7C3AED",
    "success": "#10B981",
    "surface": "#1E2536",
}

SEVERITY_COLORS = {
    "CRITICAL": _SOC_COLORS["critical"],
    "HIGH": _SOC_COLORS["high"],
    "MEDIUM": _SOC_COLORS["medium"],
    "LOW": _SOC_COLORS["low"],
}

PALETTE = [
    "#4A9EFF", "#7C3AED", "#10B981", "#FF8C00",
    "#FF4444", "#FFD700", "#06B6D4", "#F472B6",
]


def apply_soc_theme(fig, title: str = "") -> None:
    """Apply the SOC dark theme to a Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_SOC_COLORS["paper"],
        plot_bgcolor=_SOC_COLORS["bg"],
        font=dict(family="Inter, sans-serif", color=_SOC_COLORS["text"], size=12),
        title=dict(
            text=title,
            font=dict(size=16, color=_SOC_COLORS["text"]),
            x=0.0,
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=_SOC_COLORS["muted_text"]),
        ),
        xaxis=dict(
            gridcolor=_SOC_COLORS["grid"],
            zerolinecolor=_SOC_COLORS["grid"],
        ),
        yaxis=dict(
            gridcolor=_SOC_COLORS["grid"],
            zerolinecolor=_SOC_COLORS["grid"],
        ),
    )


def get_severity_color(label: str) -> str:
    """Get the hex color for a severity label."""
    return SEVERITY_COLORS.get(label, _SOC_COLORS["info"])
