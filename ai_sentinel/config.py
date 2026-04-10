"""
Central configuration for AI-Sentinel V3.

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
DB_PATH = DATA_DIR / "sentinel_v3.db"
LOG_DIR = PROJECT_ROOT / "logs"
MODEL_DIR = DATA_DIR / "models"

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
API_HOST: str = os.getenv("SENTINEL_API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("SENTINEL_API_PORT", "8000"))
DASHBOARD_PORT: int = int(os.getenv("SENTINEL_DASH_PORT", "8501"))

# ---------------------------------------------------------------------------
# Security — TLS
# ---------------------------------------------------------------------------
REQUIRE_TLS: bool = os.getenv("SENTINEL_REQUIRE_TLS", "false").lower() == "true"
TLS_CERT_PATH: str = os.getenv("SENTINEL_TLS_CERT", "")
TLS_KEY_PATH: str = os.getenv("SENTINEL_TLS_KEY", "")

# ---------------------------------------------------------------------------
# Security — JWT / RBAC
# ---------------------------------------------------------------------------
# Secret key used to sign JWTs / session tokens (generate once, store in env)
JWT_SECRET: str = os.getenv("SENTINEL_JWT_SECRET", secrets.token_urlsafe(32))
SECRET_KEY: str = os.getenv("SENTINEL_SECRET_KEY", JWT_SECRET)  # backward compat
TOKEN_ALGORITHM: str = "HS256"
JWT_EXPIRATION_MINUTES: int = int(os.getenv("SENTINEL_JWT_EXPIRATION_MINUTES", "480"))
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
# Detection — Baselining
# ---------------------------------------------------------------------------
MIN_BASELINE_EVENTS: int = int(os.getenv("SENTINEL_MIN_BASELINE_EVENTS", "200"))

# ---------------------------------------------------------------------------
# Detection — Thresholds
# ---------------------------------------------------------------------------
DETECTION_THROTTLE_SECONDS: float = 5.0  # min gap between online detection runs
STATISTICAL_BASELINE_SIGMA: float = 3.0  # z-score threshold for Layer 1
AUTOENCODER_PERCENTILE_THRESHOLD: float = 95.0  # reconstruction-error percentile

# ---------------------------------------------------------------------------
# Severity Scoring
# ---------------------------------------------------------------------------
SEVERITY_THRESHOLDS: dict = {
    "CRITICAL": float(os.getenv("SENTINEL_SEVERITY_CRITICAL", "0.9")),
    "HIGH": float(os.getenv("SENTINEL_SEVERITY_HIGH", "0.7")),
    "MEDIUM": float(os.getenv("SENTINEL_SEVERITY_MEDIUM", "0.4")),
    "LOW": float(os.getenv("SENTINEL_SEVERITY_LOW", "0.0")),
}

# ---------------------------------------------------------------------------
# Incident Management
# ---------------------------------------------------------------------------
INCIDENT_WINDOW_MINUTES: int = int(os.getenv("SENTINEL_INCIDENT_WINDOW_MINUTES", "15"))

# ---------------------------------------------------------------------------
# Device Monitoring
# ---------------------------------------------------------------------------
DEVICE_ONLINE_THRESHOLD_MINUTES: int = int(
    os.getenv("SENTINEL_DEVICE_ONLINE_THRESHOLD_MINUTES", "5")
)

# ---------------------------------------------------------------------------
# Model Defaults
# ---------------------------------------------------------------------------
ENSEMBLE_CONTAMINATION: float = 0.05
AUTOENCODER_LATENT_DIM: int = 4
AUTOENCODER_EPOCHS: int = 50
AUTOENCODER_LR: float = 1e-3

# ---------------------------------------------------------------------------
# Feature Drift Detection
# ---------------------------------------------------------------------------
PSI_DRIFT_THRESHOLD: float = float(os.getenv("SENTINEL_PSI_DRIFT_THRESHOLD", "0.2"))
FP_RATE_THRESHOLD: float = float(os.getenv("SENTINEL_FP_RATE_THRESHOLD", "0.15"))

# ---------------------------------------------------------------------------
# Threat Intelligence
# ---------------------------------------------------------------------------
ABUSEIPDB_API_KEY: str = os.getenv("SENTINEL_ABUSEIPDB_API_KEY", "")
THREAT_INTEL_CACHE_HOURS: int = int(os.getenv("SENTINEL_TI_CACHE_HOURS", "24"))

# ---------------------------------------------------------------------------
# Metrics Aggregation
# ---------------------------------------------------------------------------
METRICS_AGGREGATION_INTERVAL_MINUTES: int = int(
    os.getenv("SENTINEL_METRICS_INTERVAL_MINUTES", "5")
)

# ---------------------------------------------------------------------------
# Data Retention
# ---------------------------------------------------------------------------
RETENTION_DAYS: int = int(os.getenv("SENTINEL_RETENTION_DAYS", "30"))
DATA_RETENTION_DAYS: int = RETENTION_DAYS  # alias
