"""
AI-Sentinel V2 — Cross-device user journey analyser.

Detects anomalies that span multiple devices for the same user, such as
concurrent sessions from geographically distant IPs or rapid device-hopping.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class UserJourneyAnalyzer:
    """
    Analyse user activity across all their registered devices
    to find suspicious cross-device patterns.
    """

    def __init__(self, max_device_switch_seconds: int = 300):
        self.max_switch_gap = timedelta(seconds=max_device_switch_seconds)

    def analyse(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scan a user's events for journey-level anomalies.

        Currently detects:
            1. **Rapid device switching** — same user active on two distinct
               devices within ``max_device_switch_seconds``.
            2. **Concurrent distinct IPs** — same user authenticated from two
               different IPs within a short window.

        Args:
            events: Chronologically sorted events for one user.

        Returns:
            List of anomaly dicts (may be empty).
        """
        findings: List[Dict[str, Any]] = []
        if len(events) < 2:
            return findings

        prev = events[0]
        for ev in events[1:]:
            ts_prev = _to_dt(prev.get("timestamp"))
            ts_curr = _to_dt(ev.get("timestamp"))
            if ts_prev is None or ts_curr is None:
                prev = ev
                continue

            gap = ts_curr - ts_prev

            # Different device within a short gap
            if (
                prev.get("device_id") != ev.get("device_id")
                and gap <= self.max_switch_gap
            ):
                findings.append({
                    "type": "rapid_device_switch",
                    "description": (
                        f"User active on device {prev.get('device_id')} and "
                        f"{ev.get('device_id')} within {gap.total_seconds():.0f}s."
                    ),
                    "timestamp": ev.get("timestamp"),
                })

            # Different source IP within a short gap (same or different device)
            ip_prev = prev.get("source_ip")
            ip_curr = ev.get("source_ip")
            if (
                ip_prev and ip_curr
                and ip_prev != ip_curr
                and gap <= self.max_switch_gap
            ):
                findings.append({
                    "type": "concurrent_distinct_ips",
                    "description": (
                        f"User seen from {ip_prev} and {ip_curr} within "
                        f"{gap.total_seconds():.0f}s."
                    ),
                    "timestamp": ev.get("timestamp"),
                })

            prev = ev

        return findings


def _to_dt(val: Any) -> Any:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return None
    return None
