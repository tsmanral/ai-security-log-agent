"""
AI-Sentinel V3 — Narrative builder.

Generates human-readable threat narratives that reference all detection
layers: statistical baseline deviations, ensemble scores, autoencoder
reconstruction errors, and severity context.
"""

from typing import Any, Dict, Optional


class NarrativeBuilder:
    """Produce analyst-friendly natural-language alert descriptions."""

    @staticmethod
    def build(
        threat_type: str,
        mitre_id: str,
        row_data: Dict[str, Any],
        layer1_z: float = 0.0,
        layer2_score: float = 0.0,
        layer3_error: float = 0.0,
        severity_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Construct a narrative string from detection context.

        Args:
            threat_type: Classified threat name (e.g., "Brute Force Attack").
            mitre_id: MITRE ATT&CK technique ID.
            row_data: Feature + metadata dict for the event.
            layer1_z: Max z-score from statistical baseline.
            layer2_score: Averaged score from classical ensemble.
            layer3_error: Reconstruction error from autoencoder.
            severity_context: Optional dict with severity_score, severity_label, urgency.

        Returns:
            Multi-sentence narrative string.
        """
        ip = row_data.get("source_ip", "Unknown IP")
        user = row_data.get("effective_username", "Unknown")
        device = row_data.get("device_id", "Unknown Device")

        # Severity badge
        sev_label = "MEDIUM"
        sev_score = 0.0
        urgency = ""
        if severity_context:
            sev_label = severity_context.get("severity_label", "MEDIUM")
            sev_score = severity_context.get("severity_score", 0.0)
            urgency = severity_context.get("urgency", "")

        sev_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }.get(sev_label, "⚪")

        parts = [
            f"{sev_emoji} **[{sev_label}]** **{threat_type}** detected ({mitre_id}).",
            f"Source: **{ip}** → user **'{user}'** on device `{device}`.",
        ]

        if sev_score > 0:
            parts.append(f"Severity score: **{sev_score:.2f}**.")

        # Layer details
        layer_reasons = []
        if layer1_z > 0:
            layer_reasons.append(f"statistical baseline deviation of {layer1_z:.1f}σ")
        if layer2_score > 0:
            layer_reasons.append(f"ensemble anomaly score of {layer2_score:.2f}")
        if layer3_error > 0:
            layer_reasons.append(f"autoencoder reconstruction error of {layer3_error:.4f}")

        if layer_reasons:
            parts.append("Flagged due to " + ", ".join(layer_reasons) + ".")

        # Feature-level colour
        failures = row_data.get("failures_15m", 0)
        unique_users = row_data.get("unique_users_15m", 0)
        off_hours = row_data.get("is_off_hours", 0)

        details = []
        if failures:
            details.append(f"{int(failures)} failed logins in 15 min")
        if unique_users and unique_users > 1:
            details.append(f"{int(unique_users)} unique usernames targeted")
        if off_hours:
            details.append("activity during off-hours")
        if details:
            parts.append("Context: " + "; ".join(details) + ".")

        # Urgency from severity
        if urgency:
            parts.append(f"**{urgency}**")

        # Guidance
        advice_map = {
            "Brute Force Attack": "Consider blocking the source IP and enforcing account lockout.",
            "Credential Stuffing": "Verify MFA is enabled on targeted accounts.",
            "Low and Slow Attack": "Monitor this IP over the next 24 hours.",
            "Anomalous Off-Hour Access": "Confirm whether this access was authorised.",
        }
        advice = advice_map.get(threat_type)
        if advice:
            parts.append(f"**Recommendation**: {advice}")

        return " ".join(parts)
