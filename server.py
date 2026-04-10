"""
AI-Sentinel V3 — FastAPI server (primary V3 entrypoint).

Mounts all routers (ingestion, device registration, incidents, heartbeats,
admin), applies TLS and CORS middleware, manages model lifecycle, and
integrates the background job scheduler.

Usage::

    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_sentinel.auth import (
    create_access_token,
    get_current_user,
    require_role,
    verify_password,
)
from ai_sentinel.config import REQUIRE_TLS
from ai_sentinel.ingestion.api_ingestion import router as events_router
from ai_sentinel.onboarding.device_registration import router as devices_router
from ai_sentinel.storage.database import (
    get_all_incidents,
    get_device,
    get_incident,
    get_user_by_username,
    init_db,
    insert_heartbeat,
    touch_device,
    update_device_status,
    update_incident_status,
    assign_incident as db_assign_incident,
)
from ai_sentinel.tls_middleware import TLSEnforcementMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── lifespan (startup / shutdown) ─────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: init DB and start scheduler on startup."""
    init_db()
    logger.info("V3 database initialized.")

    # Start background scheduler
    try:
        from ai_sentinel.jobs.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        logger.info("Background job scheduler started.")
    except Exception:
        logger.warning("Background scheduler not available — jobs will not run.")

    yield

    # Shutdown
    try:
        from ai_sentinel.jobs.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Background job scheduler stopped.")
    except Exception:
        pass


# ── FastAPI app ───────────────────────────────────────────────────────────

app = FastAPI(
    title="AI-Sentinel V3 API",
    version="3.0.0",
    description=(
        "Real-time ingestion, device onboarding, ML detection, incident management, "
        "and threat intelligence API for the AI-Sentinel SIEM platform."
    ),
    lifespan=lifespan,
)

# Middleware
app.add_middleware(TLSEnforcementMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(events_router)
app.include_router(devices_router)

# Serve static files (e.g., installer script for agents)
STATIC_DIR = Path(__file__).parent / "ai_sentinel" / "onboarding"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve the endpoint agent script
AGENT_DIR = Path(__file__).parent / "ai_sentinel" / "endpoint_agent"
if AGENT_DIR.exists():
    app.mount("/agent", StaticFiles(directory=str(AGENT_DIR)), name="agent")


# ── Health endpoints ─────────────────────────────────────────────────────


@app.get("/", tags=["health"])
async def health():
    """Simple health check."""
    return {
        "status": "ok",
        "version": "3.0.0",
        "tls_enforced": REQUIRE_TLS,
    }


@app.get("/api/health", tags=["health"])
async def api_health():
    """API health endpoint."""
    return {"status": "ok", "service": "ai-sentinel-api", "version": "3.0.0"}


# ── Auth endpoints ───────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


@app.post("/api/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(req: LoginRequest):
    """Authenticate and return a JWT access token."""
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user.get("role", "ANALYST"),
    )
    return TokenResponse(
        access_token=token,
        role=user.get("role", "ANALYST"),
        user_id=user["id"],
    )


# ── Heartbeat endpoint ─────────────────────────────────────────────────


class HeartbeatRequest(BaseModel):
    device_id: str
    cpu_pct: Optional[float] = None
    mem_pct: Optional[float] = None
    agent_version: Optional[str] = None


@app.post("/heartbeat", tags=["heartbeat"])
async def heartbeat(req: HeartbeatRequest):
    """Record a heartbeat from an endpoint agent."""
    device = get_device(req.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Unknown device.")

    insert_heartbeat(
        device_id=req.device_id,
        cpu_pct=req.cpu_pct,
        mem_pct=req.mem_pct,
        agent_version=req.agent_version,
    )
    touch_device(req.device_id)

    # Ensure device is not marked OFFLINE
    if device.get("status") == "OFFLINE":
        update_device_status(req.device_id, "ONLINE")

    return {"status": "ok", "device_id": req.device_id}


# ── Incident endpoints ──────────────────────────────────────────────────


class IncidentStatusRequest(BaseModel):
    status: str  # OPEN | INVESTIGATING | RESOLVED | FALSE_POSITIVE
    notes: str = ""


class IncidentAssignRequest(BaseModel):
    user_id: str


@app.post("/incidents/{incident_id}/status", tags=["incidents"])
async def update_incident(
    incident_id: int,
    req: IncidentStatusRequest,
    user: dict = Depends(require_role("ADMIN", "ANALYST")),
):
    """Update the status of an incident. Requires ADMIN or ANALYST role."""
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    valid_statuses = {"OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}.",
        )

    update_incident_status(incident_id, req.status, req.notes)
    return {"status": "ok", "incident_id": incident_id, "new_status": req.status}


@app.post("/incidents/{incident_id}/assign", tags=["incidents"])
async def assign_incident(
    incident_id: int,
    req: IncidentAssignRequest,
    user: dict = Depends(require_role("ADMIN", "ANALYST")),
):
    """Assign an incident to a user. Requires ADMIN or ANALYST role."""
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    db_assign_incident(incident_id, req.user_id)
    return {"status": "ok", "incident_id": incident_id, "assigned_to": req.user_id}


@app.get("/api/incidents", tags=["incidents"])
async def list_incidents(
    status: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(require_role("ADMIN", "ANALYST")),
):
    """List incidents, optionally filtered by status."""
    incidents = get_all_incidents(status=status, limit=limit)
    return {"incidents": incidents, "count": len(incidents)}


# ── Admin endpoints ─────────────────────────────────────────────────────


@app.post("/admin/retrain", tags=["admin"])
async def retrain_models(
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_role("ADMIN")),
):
    """
    Trigger a full model retrain in the background.
    Requires ADMIN role.
    """

    def _do_retrain():
        try:
            from ai_sentinel.detection.detection_orchestrator import DetectionOrchestrator
            from ai_sentinel.features.feature_extractor import build_features
            from ai_sentinel.storage.database import get_connection

            conn = get_connection()
            rows = conn.execute(
                "SELECT * FROM normalized_events ORDER BY timestamp DESC LIMIT 10000"
            ).fetchall()
            conn.close()

            if not rows:
                logger.warning("No events found for retraining.")
                return

            events = [dict(r) for r in rows]
            df = build_features(events)
            if df.empty:
                logger.warning("Feature extraction returned empty DataFrame.")
                return

            orchestrator = DetectionOrchestrator()
            orchestrator.train(df)
            logger.info("Model retrain completed successfully (%d events).", len(df))
        except Exception:
            logger.exception("Model retrain failed.")

    background_tasks.add_task(_do_retrain)
    return {"status": "accepted", "message": "Model retrain started in background."}
