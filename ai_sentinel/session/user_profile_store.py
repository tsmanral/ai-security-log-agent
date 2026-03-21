"""
AI-Sentinel V2 — Per-user behavioural profile store.

Maintains rolling statistics (typical login hours, common IPs, failure
rates, known devices) for each user to support baseline comparisons.
"""

from collections import defaultdict
from typing import Any, Dict, List, Set


class UserProfileStore:
    """
    In-memory per-user behavioral profile.

    Each profile tracks:
        - Common login hours (set of ints 0–23).
        - Known IPs (set).
        - Known devices (set).
        - Cumulative success / failure counts.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "common_hours": set(),
                "known_ips": set(),
                "known_devices": set(),
                "total_successes": 0,
                "total_failures": 0,
            }
        )

    def update(self, user_id: str, events: List[Dict[str, Any]]) -> None:
        """
        Update the profile for *user_id* with a batch of new events.
        """
        p = self._profiles[user_id]
        for ev in events:
            import datetime as _dt

            ts = ev.get("timestamp")
            if isinstance(ts, str):
                try:
                    ts = _dt.datetime.fromisoformat(ts)
                except ValueError:
                    ts = None
            if ts:
                p["common_hours"].add(ts.hour)

            ip = ev.get("source_ip")
            if ip:
                p["known_ips"].add(ip)

            did = ev.get("device_id")
            if did:
                p["known_devices"].add(did)

            etype = ev.get("event_type", "")
            if "success" in etype or "accepted" in etype:
                p["total_successes"] += 1
            elif "fail" in etype or "failed" in etype:
                p["total_failures"] += 1

    def get(self, user_id: str) -> Dict[str, Any]:
        """Return the current profile for *user_id* (serialisable copy)."""
        p = self._profiles[user_id]
        return {
            "common_hours": sorted(p["common_hours"]),
            "known_ips": sorted(p["known_ips"]),
            "known_devices": sorted(p["known_devices"]),
            "total_successes": p["total_successes"],
            "total_failures": p["total_failures"],
        }

    def is_new_ip(self, user_id: str, ip: str) -> bool:
        """Check if the IP has been observed for this user before."""
        return ip not in self._profiles[user_id]["known_ips"]

    def is_unusual_hour(self, user_id: str, hour: int) -> bool:
        """Check if the hour is outside this user's common hours."""
        return hour not in self._profiles[user_id]["common_hours"]
