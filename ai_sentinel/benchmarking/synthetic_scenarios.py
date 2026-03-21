"""
AI-Sentinel V2 — Synthetic attack scenario generator.

Produces synthetic normalized events for benchmarking and controlled tests.
Always sets ``is_synthetic = True``.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List


class SyntheticScenarioGenerator:
    """Generate attack scenarios as lists of normalized event dicts."""

    @staticmethod
    def brute_force(
        target_user: str = "root",
        source_ip: str = "192.168.1.200",
        device_id: str = "synthetic-device",
        user_id: str = "synthetic-user",
        count: int = 80,
    ) -> List[Dict[str, Any]]:
        """Rapid-fire password failures from one IP against one user."""
        base = datetime.utcnow() - timedelta(minutes=15)
        events = []
        for i in range(count):
            events.append({
                "timestamp": (base + timedelta(seconds=i * 2)).isoformat(),
                "host": "target-host",
                "device_id": device_id,
                "user_id": user_id,
                "effective_username": target_user,
                "source_ip": source_ip,
                "event_type": "ssh_failed_password",
                "raw_message": f"Failed password for {target_user} from {source_ip}",
                "attributes": {},
                "is_synthetic": True,
            })
        return events

    @staticmethod
    def credential_stuffing(
        source_ip: str = "10.0.0.99",
        device_id: str = "synthetic-device",
        user_id: str = "synthetic-user",
        count: int = 60,
    ) -> List[Dict[str, Any]]:
        """Failures across many usernames from a single IP."""
        users = [f"user{i}" for i in range(count)]
        base = datetime.utcnow() - timedelta(minutes=15)
        return [
            {
                "timestamp": (base + timedelta(seconds=i * 3)).isoformat(),
                "host": "target-host",
                "device_id": device_id,
                "user_id": user_id,
                "effective_username": u,
                "source_ip": source_ip,
                "event_type": "ssh_failed_password",
                "raw_message": f"Failed password for {u} from {source_ip}",
                "attributes": {},
                "is_synthetic": True,
            }
            for i, u in enumerate(users)
        ]

    @staticmethod
    def off_hour_access(
        username: str = "admin",
        source_ip: str = "172.16.0.5",
        device_id: str = "synthetic-device",
        user_id: str = "synthetic-user",
    ) -> List[Dict[str, Any]]:
        """Successful login at 3 AM."""
        ts = datetime.utcnow().replace(hour=3, minute=15, second=0)
        return [
            {
                "timestamp": ts.isoformat(),
                "host": "target-host",
                "device_id": device_id,
                "user_id": user_id,
                "effective_username": username,
                "source_ip": source_ip,
                "event_type": "ssh_accepted_publickey",
                "raw_message": f"Accepted publickey for {username} from {source_ip}",
                "attributes": {},
                "is_synthetic": True,
            }
        ]

    @staticmethod
    def normal_traffic(
        device_id: str = "synthetic-device",
        user_id: str = "synthetic-user",
        count: int = 500,
    ) -> List[Dict[str, Any]]:
        """Baseline normal traffic for training models."""
        users = ["deploy", "admin", "devops", "svc"]
        ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
        base = datetime.utcnow() - timedelta(hours=24)
        events = []
        for i in range(count):
            events.append({
                "timestamp": (base + timedelta(seconds=i * 120 + random.randint(0, 60))).isoformat(),
                "host": "prod-server",
                "device_id": device_id,
                "user_id": user_id,
                "effective_username": random.choice(users),
                "source_ip": random.choice(ips),
                "event_type": random.choice(["ssh_accepted_publickey", "session_opened"]),
                "raw_message": "synthetic normal event",
                "attributes": {},
                "is_synthetic": True,
            })
        return events
