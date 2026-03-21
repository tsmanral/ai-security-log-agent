"""
AI-Sentinel V2 — Device registration API.

FastAPI router that lets endpoint agents register themselves using a
short-lived token obtained from the dashboard.
"""

import logging
import secrets
import time
import uuid
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, constr

from ai_sentinel.config import (
    MAX_HOSTNAME_LENGTH,
    RATE_LIMIT_REGISTER_PER_MIN,
)
from ai_sentinel.onboarding.token_manager import validate_and_consume
from ai_sentinel.storage.database import create_device, get_device, get_devices_for_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/devices", tags=["onboarding"])

# ── Rate limiting (per-IP) ────────────────────────────────────────────────

_ip_hits: Dict[str, deque] = defaultdict(deque)


def _check_ip_rate(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = _ip_hits[client_ip]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= RATE_LIMIT_REGISTER_PER_MIN:
        raise HTTPException(status_code=429, detail="Registration rate limit exceeded.")
    window.append(now)


# ── Pydantic schemas ─────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Payload sent by the installer / agent to register a device."""

    token: str = Field(..., description="Single-use registration token from the dashboard")
    hostname: constr(max_length=MAX_HOSTNAME_LENGTH) = ""  # type: ignore[valid-type]
    os_type: str = Field(..., pattern="^(linux|windows)$")
    display_name: Optional[str] = None


class RegisterResponse(BaseModel):
    """Returned to the agent after successful registration."""

    device_id: str
    api_key: str  # shown once, agent must store it
    collector_url: str
    log_paths: List[str]


class DeviceConfig(BaseModel):
    """Configuration returned to the agent on refresh."""

    device_id: str
    collector_url: str
    log_paths: List[str]


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.post("/register", response_model=RegisterResponse, summary="Register a new device")
async def register_device(body: RegisterRequest, request: Request) -> RegisterResponse:
    """
    Register an endpoint agent.

    1. Validates the single-use token (checks expiry + used flag).
    2. Derives ``user_id`` from the token.
    3. Generates a random ``device_id`` and API key.
    4. Stores the device with a **hashed** API key.
    5. Returns the plain-text API key once so the agent can persist it.
    """
    _check_ip_rate(request)

    token_data = validate_and_consume(body.token)
    if token_data is None:
        raise HTTPException(status_code=400, detail="Invalid or expired registration token.")

    user_id: str = token_data["user_id"]
    device_id = str(uuid.uuid4())
    api_key = secrets.token_urlsafe(32)

    # For production: hash with passlib.hash.bcrypt.hash(api_key)
    # Skeleton stores raw for dev convenience — swap before deployment
    api_key_hash = api_key  # TODO: bcrypt.hash(api_key)

    create_device(
        device_id=device_id,
        user_id=user_id,
        hostname=body.hostname,
        os_type=body.os_type,
        api_key_hash=api_key_hash,
        display_name=body.display_name,
    )
    logger.info(
        "Device registered: id=%s hostname=%s user=%s",
        device_id, body.hostname, user_id,
    )

    # Default config (Linux)
    default_log_paths = ["/var/log/auth.log"] if body.os_type == "linux" else []

    return RegisterResponse(
        device_id=device_id,
        api_key=api_key,
        collector_url="/api/events/batch",
        log_paths=default_log_paths,
    )


@router.get("/config/{device_id}", response_model=DeviceConfig, summary="Get device config")
async def get_device_config(device_id: str) -> DeviceConfig:
    """
    Return the current configuration for a registered device.

    The agent can call this periodically to pick up config changes
    (e.g., new log paths, rotated API key).
    """
    device = get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found.")

    return DeviceConfig(
        device_id=device_id,
        collector_url="/api/events/batch",
        log_paths=["/var/log/auth.log"] if device["os_type"] == "linux" else [],
    )
