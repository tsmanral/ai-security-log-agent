-- ============================================================================
-- LSADRA V4 — Schema Additions
-- Migration: 002_v4_schema
-- Run after: 001_initial_v3_schema.sql
-- Created:    2026-04-10
-- ============================================================================

-- [V4 ENHANCEMENT — gap: analyst feedback loop]
-- Analyst false-positive / true-positive feedback on individual alerts
-- [DESIGN CHOICE] No FK constraint on alert_id: feedback may arrive out-of-order
-- (e.g. UI feedback sent before anomaly write completes). Application layer
-- validates alert_id existence when rendering the feedback table.
CREATE TABLE IF NOT EXISTS alerts_feedback (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id             INTEGER NOT NULL,
    label                TEXT    NOT NULL CHECK(label IN ('true_positive','false_positive')),
    analyst_note         TEXT,
    fp_pattern           TEXT,
    suggested_thresholds TEXT,   -- JSON blob of {feature: new_threshold}
    source_type          TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- [V4 ENHANCEMENT — gap: multi-source ingestion health]
-- Ingestion health statistics per source type (upserted by scheduler job)
CREATE TABLE IF NOT EXISTS ingestion_stats (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type  TEXT NOT NULL UNIQUE,
    events_count INTEGER DEFAULT 0,
    parse_errors INTEGER DEFAULT 0,
    last_event   TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- V4 Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_feedback_alert     ON alerts_feedback(alert_id);
CREATE INDEX IF NOT EXISTS idx_feedback_label     ON alerts_feedback(label);
CREATE INDEX IF NOT EXISTS idx_feedback_source    ON alerts_feedback(source_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_source   ON ingestion_stats(source_type);
