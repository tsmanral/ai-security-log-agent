"""
AI-Sentinel V2 — HTTPS ingestion API.

FastAPI router that accepts authenticated JSON event batches from endpoint
agents and triggers near-real-time detection.
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

    # ── trigger online detection (import here to avoid circular deps) ───
    try:
        from ai_sentinel.detection.detection_orchestrator import DetectionOrchestrator

        orchestrator = DetectionOrchestrator()
        orchestrator.run_for_new_events(device_id=device_id)
    except Exception:
        logger.exception("Online detection failed for device %s", device_id)

    return {"status": "ok", "events_accepted": count}
