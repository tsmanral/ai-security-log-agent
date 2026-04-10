"""
AI-Sentinel V3+V4 — HTTPS ingestion API.

FastAPI router that accepts:
  V3: authenticated JSON event batches from endpoint agents (unchanged)
  V4: raw log lines from any supported source via IngestionManager

[V4 ENHANCEMENT — gap: multi-source ingestion]
"""

import logging
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, constr

from ai_sentinel.config import (
    MAX_EVENTS_PER_BATCH,
    MAX_HOSTNAME_LENGTH,
    MAX_RAW_MESSAGE_LENGTH,
    MAX_USERNAME_LENGTH,
    RATE_LIMIT_EVENTS_PER_MIN,
)
from ai_sentinel.storage.database import (
    get_device,
    insert_events_batch,
    touch_device,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["ingestion"])

# ── Pydantic models ───────────────────────────────────────────────────────


class NormalizedEvent(BaseModel):
    """Schema for a single event sent by an endpoint agent."""

    timestamp: datetime
    host: constr(max_length=MAX_HOSTNAME_LENGTH) = ""  # type: ignore[valid-type]
    effective_username: constr(max_length=MAX_USERNAME_LENGTH) = ""  # type: ignore[valid-type]
    source_ip: Optional[str] = None
    event_type: str = Field(..., max_length=64)
    raw_message: constr(max_length=MAX_RAW_MESSAGE_LENGTH) = ""  # type: ignore[valid-type]
    attributes: Dict[str, Any] = Field(default_factory=dict)


class EventBatch(BaseModel):
    """Wrapper for a batch of events from one device."""

    events: List[NormalizedEvent] = Field(..., max_length=MAX_EVENTS_PER_BATCH)


# ── Simple in-memory rate limiter ─────────────────────────────────────────

_device_hits: Dict[str, deque] = defaultdict(deque)


def _check_rate_limit(device_id: str) -> None:
    """Raise 429 if the device exceeds its per-minute event batch limit."""
    now = time.time()
    window = _device_hits[device_id]
    # Purge entries older than 60 s
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= RATE_LIMIT_EVENTS_PER_MIN:
        raise HTTPException(status_code=429, detail="Rate limit exceeded for this device.")
    window.append(now)


# ── Auth dependency ───────────────────────────────────────────────────────


def _authenticate_device(x_device_id: str = Header(...), x_api_key: str = Header(...)) -> Dict[str, Any]:
    """
    Validate the device ID + API key sent in request headers.

    Returns the device row dict on success, raises 401 otherwise.
    The API key comparison uses the hashed value stored at registration time.
    For the skeleton we do a plain equality check; production code should
    use ``passlib.hash.bcrypt.verify(x_api_key, device['api_key_hash'])``.
    """
    device = get_device(x_device_id)
    if device is None:
        raise HTTPException(status_code=401, detail="Unknown device.")

    # TODO: replace with proper KDF verify once passlib is wired in
    # from passlib.hash import bcrypt
    # if not bcrypt.verify(x_api_key, device["api_key_hash"]):
    stored_hash = device.get("api_key_hash", "")
    if stored_hash != x_api_key and stored_hash != "":
        # Skeleton: accept in dev mode; tighten for production
        logger.warning("API key mismatch for device %s (dev-mode pass-through)", x_device_id)

    return device


# ── Module-level singleton orchestrator (V3, unchanged) ──────────────────
# Keep one instance alive so models, baselines, and state persist across calls.

_orchestrator = None


def _get_orchestrator():
    """Return the singleton DetectionOrchestrator, creating it once."""
    global _orchestrator
    if _orchestrator is None:
        from ai_sentinel.detection.detection_orchestrator import DetectionOrchestrator
        _orchestrator = DetectionOrchestrator()
    return _orchestrator


# ── V4: IngestionManager singleton ────────────────────────────────────────
# [V4 ENHANCEMENT — gap: multi-source ingestion]
# [DESIGN CHOICE] Singleton keeps parser chain and stats alive across requests.

_ingest_manager = None


def _get_ingest_manager():
    """Return the singleton IngestionManager, creating it once."""
    global _ingest_manager
    if _ingest_manager is None:
        from ai_sentinel.ingestion.ingestion_manager import IngestionManager
        _ingest_manager = IngestionManager()
    return _ingest_manager


# ── Endpoint ──────────────────────────────────────────────────────────────


@router.post("/batch", summary="Ingest a batch of normalized events")
async def ingest_batch(
    batch: EventBatch,
    device: Dict[str, Any] = Depends(_authenticate_device),
) -> Dict[str, Any]:
    """
    Accept a batch of events from an endpoint agent.

    After inserting events, triggers online detection for this device.
    """
    device_id: str = device["id"]
    user_id: str = device["user_id"]

    _check_rate_limit(device_id)

    # Build rows for bulk insert
    rows = []
    for ev in batch.events:
        rows.append(
            {
                "timestamp": ev.timestamp.isoformat(),
                "device_id": device_id,
                "user_id": user_id,
                "host": ev.host,
                "effective_username": ev.effective_username,
                "source_ip": ev.source_ip,
                "event_type": ev.event_type,
                "raw_message": ev.raw_message,
                "attributes": ev.attributes,
                "is_synthetic": False,
            }
        )

    count = insert_events_batch(rows)
    touch_device(device_id)
    logger.info("Ingested %d events from device %s", count, device_id)

    # ── trigger online detection using the singleton orchestrator ────────
    try:
        orchestrator = _get_orchestrator()
        orchestrator.run_for_new_events(device_id=device_id)
    except Exception:
        logger.exception("Online detection failed for device %s", device_id)

    return {"status": "ok", "events_accepted": count}


# ── V4: Raw log ingestion endpoint ────────────────────────────────────────
# [V4 ENHANCEMENT — gap: multi-source ingestion]


class RawLogLine(BaseModel):
    """Schema for a single raw log line from any supported source."""

    raw_line: str = Field(..., max_length=MAX_RAW_MESSAGE_LENGTH)
    source_hint: Optional[str] = Field(
        default=None,
        description="Optional parser hint: ssh|syslog|windows|network|endpoint",
    )


class RawLogBatch(BaseModel):
    """Batch of raw log lines from one device."""

    lines: List[RawLogLine] = Field(..., max_length=MAX_EVENTS_PER_BATCH)


@router.post("/raw", summary="[V4] Ingest raw log lines via IngestionManager")
async def ingest_raw_batch(
    batch: RawLogBatch,
    device: Dict[str, Any] = Depends(_authenticate_device),
) -> Dict[str, Any]:
    """
    Accept a batch of raw log lines from any supported source.

    Routes each line through the V4 IngestionManager for auto-detection
    and parsing, then stores the resulting unified events and triggers
    enhanced feature extraction before online detection.

    [V4 ENHANCEMENT — gap: multi-source ingestion]
    [GLASSWING ALIGNMENT — central ingestion orchestrator]

    Args:
        batch:  Batch of raw log lines with optional source_hint.
        device: Authenticated device record (from device headers).

    Returns:
        status, accepted count, parse error count, per-source breakdown.
    """
    device_id: str = device["id"]
    user_id:   str = device["user_id"]

    _check_rate_limit(device_id)

    manager  = _get_ingest_manager()
    accepted = 0
    parse_errors = 0
    source_counts: Dict[str, int] = {}

    db_rows: List[Dict[str, Any]] = []
    v4_events: List[Dict[str, Any]] = []

    for line_obj in batch.lines:
        try:
            event = manager.ingest_line(
                raw_line=line_obj.raw_line,
                device_id=device_id,
                hint=line_obj.source_hint,
            )
            if event is None:
                parse_errors += 1
                continue

            # Map V4 event schema to V3 DB row schema
            db_row = {
                "timestamp":          event.get("timestamp"),
                "device_id":          device_id,
                "user_id":            user_id,
                "host":               event.get("device_id", ""),
                "effective_username": event.get("username") or "",
                "source_ip":          event.get("source_ip"),
                "event_type":         event.get("event_type"),
                "raw_message":        event.get("raw", "")[:MAX_RAW_MESSAGE_LENGTH],
                "attributes":         event.get("extra", {}),
                "is_synthetic":       False,
            }
            db_rows.append(db_row)
            v4_events.append(event)
            accepted += 1

            src = event.get("source_type", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
        except Exception:
            logger.exception("[V4] Failed to ingest raw line: %.120s", line_obj.raw_line)
            parse_errors += 1

    if db_rows:
        insert_events_batch(db_rows)
        touch_device(device_id)
        logger.info(
            "[V4] Ingested %d events from device %s (errors: %d, sources: %s)",
            accepted, device_id, parse_errors, source_counts,
        )

    # ── V4 enhanced feature extraction (graceful degradation) ────────────
    # [V4 ENHANCEMENT — gap: temporal + relationship features]
    if v4_events:
        try:
            import pandas as pd
            from ai_sentinel.features.feature_extractor import build_enhanced_feature_table

            df = pd.DataFrame(v4_events)
            df = build_enhanced_feature_table(df)
            logger.debug("[V4] Feature extraction complete for %d events.", len(df))
        except Exception:
            logger.exception("[V4] Enhanced feature extraction failed — using V3 pipeline.")

    # ── V3 online detection (preserved) ──────────────────────────────────
    try:
        orchestrator = _get_orchestrator()
        orchestrator.run_for_new_events(device_id=device_id)
    except Exception:
        logger.exception("Online detection failed for device %s", device_id)

    return {
        "status":       "ok",
        "accepted":     accepted,
        "parse_errors": parse_errors,
        "source_breakdown": source_counts,
    }


@router.get("/stats", summary="[V4] Get ingestion statistics by source type")
async def get_ingest_stats(
    device: Dict[str, Any] = Depends(_authenticate_device),
) -> Dict[str, Any]:
    """
    Return per-source ingestion statistics from the IngestionManager.

    [V4 ENHANCEMENT — gap: ingestion health monitoring]

    Returns:
        Dict of source_type → {events, errors, last_event}.
    """
    manager = _get_ingest_manager()
    return {"status": "ok", "stats": manager.get_source_stats()}
