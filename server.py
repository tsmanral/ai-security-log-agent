"""
AI-Sentinel V2 — FastAPI server (primary V2 entrypoint).

Mounts the ingestion and device-registration routers, serves static
assets (for the Linux installer), and provides an OpenAPI spec at ``/docs``.

Usage::

    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ai_sentinel.ingestion.api_ingestion import router as events_router
from ai_sentinel.onboarding.device_registration import router as devices_router
from ai_sentinel.storage.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Initialise database ──────────────────────────────────────────────────
init_db()

# ── FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(
    title="AI-Sentinel V2 API",
    version="2.0.0",
    description=(
        "Real-time ingestion, device onboarding, and detection API "
        "for the AI-Sentinel SIEM research platform."
    ),
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


@app.get("/", tags=["health"])
async def health():
    """Simple health check."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/health", tags=["health"])
async def api_health():
    """API health endpoint."""
    return {"status": "ok", "service": "ai-sentinel-api"}
