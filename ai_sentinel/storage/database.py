"""
AI-Sentinel V2 — SQLite storage layer.

Manages the database schema for users, devices, normalized events, sessions,
user profiles, and anomaly detection results.  Provides CRUD helpers used by
the ingestion API, detection orchestrator, and dashboard.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_sentinel.config import DB_PATH, RETENTION_DAYS

logger = logging.getLogger(__name__)

# ── connection helper ──────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Return a connection to the V2 SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")      # better concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

# ── schema bootstrap ──────────────────────────────────────────────────────

_SCHEMA_SQL = """
-- Dashboard user accounts
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Registered endpoint devices
CREATE TABLE IF NOT EXISTS devices (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES users(id),
    hostname      TEXT NOT NULL,
    os_type       TEXT NOT NULL,
    display_name  TEXT,
    api_key_hash  TEXT NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen_at  DATETIME
);

-- Single-use, short-lived registration tokens
CREATE TABLE IF NOT EXISTS registration_tokens (
    token      TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id),
    expires_at DATETIME NOT NULL,
    used       BOOLEAN DEFAULT 0
);

-- Normalized events from all agents
CREATE TABLE IF NOT EXISTS normalized_events (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp          DATETIME NOT NULL,
    device_id          TEXT REFERENCES devices(id),
    user_id            TEXT REFERENCES users(id),
    host               TEXT,
    effective_username TEXT,
    source_ip          TEXT,
    event_type         TEXT NOT NULL,
    raw_message        TEXT NOT NULL,
    attributes         TEXT,
    is_synthetic       BOOLEAN DEFAULT 0
);

-- Per-device detection watermark (online mode)
CREATE TABLE IF NOT EXISTS detection_watermarks (
    device_id           TEXT PRIMARY KEY REFERENCES devices(id),
    last_processed_id   INTEGER DEFAULT 0,
    last_run_at         DATETIME
);

-- V2 anomaly detection results
CREATE TABLE IF NOT EXISTS anomalies_v2 (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER REFERENCES normalized_events(id),
    device_id       TEXT,
    user_id         TEXT,
    layer1_score    REAL,
    layer2_score    REAL,
    layer2_votes    INTEGER,
    layer3_score    REAL,
    is_anomaly      BOOLEAN,
    threat_type     TEXT,
    mitre_technique TEXT,
    narrative       TEXT,
    is_synthetic    BOOLEAN DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_events_user_ts   ON normalized_events(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_device_ts ON normalized_events(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_synthetic  ON normalized_events(is_synthetic);
CREATE INDEX IF NOT EXISTS idx_anomalies_user    ON anomalies_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_device  ON anomalies_v2(device_id);
"""


def init_db() -> None:
    """Create all tables and indexes if they do not yet exist."""
    logger.info("Initializing V2 database at %s", DB_PATH)
    conn = get_connection()
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    conn.close()
    logger.info("V2 database schema ready.")


# ── CRUD: users ───────────────────────────────────────────────────────────

def create_user(user_id: str, username: str, password_hash: str) -> None:
    """Insert a new dashboard user."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash),
    )
    conn.commit()
    conn.close()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Return a user row or *None*."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── CRUD: devices ─────────────────────────────────────────────────────────

def create_device(
    device_id: str,
    user_id: str,
    hostname: str,
    os_type: str,
    api_key_hash: str,
    display_name: Optional[str] = None,
) -> None:
    """Register a new endpoint device."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO devices
           (id, user_id, hostname, os_type, display_name, api_key_hash)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (device_id, user_id, hostname, os_type, display_name, api_key_hash),
    )
    conn.commit()
    conn.close()


def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a device by its ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_devices_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Return all devices belonging to a user."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM devices WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def touch_device(device_id: str) -> None:
    """Update *last_seen_at* for a device."""
    conn = get_connection()
    conn.execute(
        "UPDATE devices SET last_seen_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), device_id),
    )
    conn.commit()
    conn.close()


# ── CRUD: registration tokens ────────────────────────────────────────────

def store_token(token: str, user_id: str, expires_at: datetime) -> None:
    """Persist a new registration token."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO registration_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at.isoformat()),
    )
    conn.commit()
    conn.close()


def consume_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate and consume a registration token.

    Returns the token row (with ``user_id``) if valid, else *None*.
    A token is valid when it has not been used and has not expired.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM registration_tokens WHERE token = ?", (token,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    data = dict(row)
    now = datetime.utcnow()
    expires = datetime.fromisoformat(data["expires_at"])

    if data["used"] or now > expires:
        conn.close()
        return None

    # Mark as consumed
    conn.execute("UPDATE registration_tokens SET used = 1 WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return data


# ── CRUD: normalized events ──────────────────────────────────────────────

def insert_event(event: Dict[str, Any]) -> int:
    """Insert a single normalized event and return its row ID."""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO normalized_events
           (timestamp, device_id, user_id, host, effective_username,
            source_ip, event_type, raw_message, attributes, is_synthetic)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event.get("timestamp"),
            event.get("device_id"),
            event.get("user_id"),
            event.get("host"),
            event.get("effective_username"),
            event.get("source_ip"),
            event.get("event_type"),
            event.get("raw_message"),
            json.dumps(event.get("attributes", {})),
            event.get("is_synthetic", False),
        ),
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id or 0


def insert_events_batch(events: List[Dict[str, Any]]) -> int:
    """Bulk-insert normalized events. Returns count inserted."""
    conn = get_connection()
    cur = conn.cursor()
    for ev in events:
        cur.execute(
            """INSERT INTO normalized_events
               (timestamp, device_id, user_id, host, effective_username,
                source_ip, event_type, raw_message, attributes, is_synthetic)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ev.get("timestamp"),
                ev.get("device_id"),
                ev.get("user_id"),
                ev.get("host"),
                ev.get("effective_username"),
                ev.get("source_ip"),
                ev.get("event_type"),
                ev.get("raw_message"),
                json.dumps(ev.get("attributes", {})),
                ev.get("is_synthetic", False),
            ),
        )
    conn.commit()
    conn.close()
    return len(events)


def get_events_since(
    device_id: str, after_id: int, limit: int = 500
) -> List[Dict[str, Any]]:
    """Fetch events for a device newer than *after_id* (for online detection)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM normalized_events
           WHERE device_id = ? AND id > ?
           ORDER BY id ASC LIMIT ?""",
        (device_id, after_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_events_for_user(
    user_id: str, synthetic: bool = False, limit: int = 5000
) -> List[Dict[str, Any]]:
    """Fetch events belonging to a user, optionally filtered by synthetic flag."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM normalized_events
           WHERE user_id = ? AND is_synthetic = ?
           ORDER BY timestamp DESC LIMIT ?""",
        (user_id, int(synthetic), limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── CRUD: detection watermarks ────────────────────────────────────────────

def get_watermark(device_id: str) -> int:
    """Return the last processed event ID for online detection."""
    conn = get_connection()
    row = conn.execute(
        "SELECT last_processed_id FROM detection_watermarks WHERE device_id = ?",
        (device_id,),
    ).fetchone()
    conn.close()
    return dict(row)["last_processed_id"] if row else 0


def set_watermark(device_id: str, last_id: int) -> None:
    """Update the detection watermark for a device."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO detection_watermarks (device_id, last_processed_id, last_run_at)
           VALUES (?, ?, ?)
           ON CONFLICT(device_id) DO UPDATE SET
               last_processed_id = excluded.last_processed_id,
               last_run_at       = excluded.last_run_at""",
        (device_id, last_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


# ── CRUD: anomalies ──────────────────────────────────────────────────────

def insert_anomaly(anomaly: Dict[str, Any]) -> int:
    """Persist a detection result."""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO anomalies_v2
           (event_id, device_id, user_id,
            layer1_score, layer2_score, layer2_votes, layer3_score,
            is_anomaly, threat_type, mitre_technique, narrative, is_synthetic)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            anomaly.get("event_id"),
            anomaly.get("device_id"),
            anomaly.get("user_id"),
            anomaly.get("layer1_score"),
            anomaly.get("layer2_score"),
            anomaly.get("layer2_votes"),
            anomaly.get("layer3_score"),
            anomaly.get("is_anomaly"),
            anomaly.get("threat_type"),
            anomaly.get("mitre_technique"),
            anomaly.get("narrative"),
            anomaly.get("is_synthetic", False),
        ),
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id or 0


def get_anomalies_for_user(
    user_id: str, synthetic: bool = False, limit: int = 200
) -> List[Dict[str, Any]]:
    """Return anomalies belonging to a user."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM anomalies_v2
           WHERE user_id = ? AND is_synthetic = ?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, int(synthetic), limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Retention cleanup ─────────────────────────────────────────────────────

def cleanup_old_data() -> int:
    """Delete events and anomalies older than RETENTION_DAYS. Returns rows deleted."""
    cutoff = (datetime.utcnow() - timedelta(days=RETENTION_DAYS)).isoformat()
    conn = get_connection()
    cur = conn.execute(
        "DELETE FROM normalized_events WHERE timestamp < ?", (cutoff,)
    )
    events_deleted = cur.rowcount
    conn.execute("DELETE FROM anomalies_v2 WHERE created_at < ?", (cutoff,))
    conn.commit()
    conn.close()
    logger.info("Retention cleanup: removed %d events older than %s", events_deleted, cutoff)
    return events_deleted


# ── direct-run bootstrap ─────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_db()
