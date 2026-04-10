-- ============================================================================
-- AI-Sentinel V3 — Initial Schema Migration
-- Migration: 001_initial_v3_schema
-- Created:   2026-04-03
-- ============================================================================

-- Dashboard user accounts with roles
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'ANALYST',  -- ADMIN | ANALYST | VIEWER
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
    status        TEXT NOT NULL DEFAULT 'BASELINING', -- BASELINING | ONLINE | OFFLINE
    event_count   INTEGER NOT NULL DEFAULT 0,
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

-- V3 anomaly detection results (expanded)
CREATE TABLE IF NOT EXISTS anomalies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER REFERENCES normalized_events(id),
    device_id       TEXT,
    user_id         TEXT,
    source_ip       TEXT,
    layer1_score    REAL,
    layer2_score    REAL,
    layer2_votes    INTEGER,
    layer3_score    REAL,
    severity_score  REAL,
    severity_label  TEXT,     -- CRITICAL | HIGH | MEDIUM | LOW
    is_anomaly      BOOLEAN,
    threat_type     TEXT,
    attack_type     TEXT,     -- normalized attack category for incident grouping
    mitre_technique TEXT,
    mitre_confidence REAL,   -- SHAP-based confidence in MITRE mapping
    narrative       TEXT,
    shap_values     TEXT,     -- JSON blob of per-feature SHAP values
    incident_id     INTEGER REFERENCES incidents(id),
    is_synthetic    BOOLEAN DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Incident management
CREATE TABLE IF NOT EXISTS incidents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id       TEXT REFERENCES devices(id),
    source_ip       TEXT,
    attack_type     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'OPEN',  -- OPEN | INVESTIGATING | RESOLVED | FALSE_POSITIVE
    assigned_to     TEXT REFERENCES users(id),
    severity_label  TEXT,
    anomaly_count   INTEGER NOT NULL DEFAULT 1,
    first_seen      DATETIME NOT NULL,
    last_seen       DATETIME NOT NULL,
    resolved_at     DATETIME,
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Device heartbeats
CREATE TABLE IF NOT EXISTS device_heartbeats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id   TEXT NOT NULL REFERENCES devices(id),
    timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cpu_pct     REAL,
    mem_pct     REAL,
    agent_version TEXT
);

-- Model registry for persistence + drift tracking
CREATE TABLE IF NOT EXISTS model_registry (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name    TEXT NOT NULL,
    model_type    TEXT NOT NULL,       -- ensemble | autoencoder | baseline
    file_path     TEXT NOT NULL,
    version       INTEGER NOT NULL DEFAULT 1,
    trained_at    DATETIME NOT NULL,
    event_count   INTEGER NOT NULL DEFAULT 0,
    metrics       TEXT,               -- JSON blob: accuracy, f1, etc.
    is_stale      BOOLEAN DEFAULT FALSE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Pre-aggregated metrics (5-minute windows)
CREATE TABLE IF NOT EXISTS metrics_5min (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id     TEXT NOT NULL,
    window_start  DATETIME NOT NULL,
    event_count   INTEGER NOT NULL DEFAULT 0,
    anomaly_count INTEGER NOT NULL DEFAULT 0,
    avg_severity  REAL DEFAULT 0.0,
    max_severity  REAL DEFAULT 0.0,
    unique_ips    INTEGER DEFAULT 0,
    unique_users  INTEGER DEFAULT 0,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, window_start)
);

-- Threat intelligence cache (AbuseIPDB)
CREATE TABLE IF NOT EXISTS threat_intel_cache (
    ip_address      TEXT PRIMARY KEY,
    abuse_score     INTEGER,
    country_code    TEXT,
    isp             TEXT,
    domain          TEXT,
    is_tor          BOOLEAN DEFAULT FALSE,
    total_reports   INTEGER,
    last_reported   DATETIME,
    raw_response    TEXT,       -- full JSON response
    queried_at      DATETIME NOT NULL,
    expires_at      DATETIME NOT NULL
);

-- IP geolocation resolution cache
CREATE TABLE IF NOT EXISTS ip_geolocation (
    ip_address   TEXT PRIMARY KEY,
    latitude     REAL,
    longitude    REAL,
    city         TEXT,
    country      TEXT,
    resolved_at  DATETIME
);

-- Feature drift detection (PSI snapshots)
CREATE TABLE IF NOT EXISTS feature_drift (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name    TEXT NOT NULL,
    feature_name  TEXT NOT NULL,
    psi_value     REAL NOT NULL,
    is_drifted    BOOLEAN DEFAULT FALSE,
    measured_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_events_user_ts     ON normalized_events(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_device_ts   ON normalized_events(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_synthetic    ON normalized_events(is_synthetic);
CREATE INDEX IF NOT EXISTS idx_events_source_ip    ON normalized_events(source_ip);
CREATE INDEX IF NOT EXISTS idx_anomalies_device    ON anomalies(device_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_user      ON anomalies(user_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_incident  ON anomalies(incident_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_severity  ON anomalies(severity_label);
CREATE INDEX IF NOT EXISTS idx_anomalies_created   ON anomalies(created_at);
CREATE INDEX IF NOT EXISTS idx_incidents_status     ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_device     ON incidents(device_id);
CREATE INDEX IF NOT EXISTS idx_heartbeats_device    ON device_heartbeats(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics5m_device     ON metrics_5min(device_id, window_start);
CREATE INDEX IF NOT EXISTS idx_drift_model          ON feature_drift(model_name, measured_at);
CREATE INDEX IF NOT EXISTS idx_ti_cache_expires     ON threat_intel_cache(expires_at);
