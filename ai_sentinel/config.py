"""
Central configuration for AI-Sentinel V2.

All tuneable parameters, file paths, secrets, and resource limits are defined here.
Environment variables override defaults where noted.
"""

import os
import secrets
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "sentinel_v2.db"
LOG_DIR = PROJECT_ROOT / "logs"

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
API_HOST: str = os.getenv("SENTINEL_API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("SENTINEL_API_PORT", "8000"))
DASHBOARD_PORT: int = int(os.getenv("SENTINEL_DASH_PORT", "8501"))

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# Secret key used to sign JWTs / session tokens (generate once, store in env)
SECRET_KEY: str = os.getenv("SENTINEL_SECRET_KEY", secrets.token_urlsafe(32))
TOKEN_ALGORITHM: str = "HS256"
REGISTRATION_TOKEN_LIFETIME_MINUTES: int = 15  # single-use, short-lived

# ---------------------------------------------------------------------------
# Rate Limiting (per-window)
# ---------------------------------------------------------------------------
RATE_LIMIT_REGISTER_PER_MIN: int = 5   # POST /api/devices/register per IP
RATE_LIMIT_EVENTS_PER_MIN: int = 60    # POST /api/events/batch per device

# ---------------------------------------------------------------------------
# Input Validation Caps
# ---------------------------------------------------------------------------
MAX_USERNAME_LENGTH: int = 128
MAX_HOSTNAME_LENGTH: int = 255
MAX_RAW_MESSAGE_LENGTH: int = 4096
MAX_EVENTS_PER_BATCH: int = 100

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
DETECTION_THROTTLE_SECONDS: float = 5.0  # min gap between online detection runs
STATISTICAL_BASELINE_SIGMA: float = 3.0  # z-score threshold for Layer 1
AUTOENCODER_PERCENTILE_THRESHOLD: float = 95.0  # reconstruction-error percentile

# ---------------------------------------------------------------------------
# Data Retention (lab mode)
# ---------------------------------------------------------------------------
RETENTION_DAYS: int = 30

# ---------------------------------------------------------------------------
# Model Defaults
# ---------------------------------------------------------------------------
ENSEMBLE_CONTAMINATION: float = 0.05
AUTOENCODER_LATENT_DIM: int = 4
AUTOENCODER_EPOCHS: int = 50
AUTOENCODER_LR: float = 1e-3
