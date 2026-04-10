"""
AI-Sentinel V3 — Background job scheduler.

Uses APScheduler to run periodic tasks:
  - Metrics aggregation (every 5 min)
  - Device offline detection (every 2 min)
  - Threat intel refresh (every 24h)
  - IP geolocation resolution (every 24h)
  - Feature drift detection (every 24h)
  - Data cleanup (daily at 02:00 UTC)
"""

import logging

logger = logging.getLogger(__name__)

_scheduler = None


def start_scheduler() -> None:
    """Initialize and start the APScheduler background scheduler."""
    global _scheduler

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning(
            "APScheduler not installed — background jobs will not run. "
            "Install with: pip install apscheduler"
        )
        return

    _scheduler = BackgroundScheduler(timezone="UTC")

    # ── Job 1: Metrics aggregation (every 5 min) ─────────────────────────
    _scheduler.add_job(
        _run_metrics_aggregation,
        IntervalTrigger(minutes=5),
        id="metrics_aggregation",
        name="Metrics Pre-Aggregation",
        replace_existing=True,
    )

    # ── Job 2: Device offline detection (every 2 min) ────────────────────
    _scheduler.add_job(
        _run_device_offline_check,
        IntervalTrigger(minutes=2),
        id="device_offline_check",
        name="Device Offline Detection",
        replace_existing=True,
    )

    # ── Job 3: Threat intel refresh (every 24h) ──────────────────────────
    _scheduler.add_job(
        _run_threat_intel_refresh,
        IntervalTrigger(hours=24),
        id="threat_intel_refresh",
        name="Threat Intel Refresh",
        replace_existing=True,
    )

    # ── Job 4: IP geolocation resolution (every 24h) ─────────────────────
    _scheduler.add_job(
        _run_geo_resolution,
        IntervalTrigger(hours=24),
        id="geo_resolution",
        name="IP Geolocation Resolution",
        replace_existing=True,
    )

    # ── Job 5: Feature drift detection (every 24h) ───────────────────────
    _scheduler.add_job(
        _run_drift_detection,
        IntervalTrigger(hours=24),
        id="drift_detection",
        name="Feature Drift Detection",
        replace_existing=True,
    )

    # ── Job 6: Data cleanup (daily at 02:00 UTC) ─────────────────────────
    _scheduler.add_job(
        _run_data_cleanup,
        CronTrigger(hour=2, minute=0),
        id="data_cleanup",
        name="Data Retention Cleanup",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Background scheduler started with %d jobs.", len(_scheduler.get_jobs()))


def stop_scheduler() -> None:
    """Stop the background scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped.")
        _scheduler = None


# ── Job implementations ──────────────────────────────────────────────────


def _run_metrics_aggregation() -> None:
    """Aggregate metrics into 5-minute windows."""
    try:
        from ai_sentinel.storage.metrics_aggregator import run
        run()
    except Exception:
        logger.exception("Metrics aggregation job failed.")


def _run_device_offline_check() -> None:
    """Check device heartbeats and mark offline devices."""
    try:
        from datetime import datetime, timedelta
        from ai_sentinel.config import DEVICE_ONLINE_THRESHOLD_MINUTES
        from ai_sentinel.storage.database import get_all_devices, update_device_status

        threshold = datetime.utcnow() - timedelta(minutes=DEVICE_ONLINE_THRESHOLD_MINUTES)
        devices = get_all_devices()

        for device in devices:
            if device.get("status") == "BASELINING":
                continue  # Don't change BASELINING devices

            last_seen = device.get("last_seen_at")
            if last_seen:
                try:
                    last_dt = datetime.fromisoformat(last_seen)
                    if last_dt < threshold and device.get("status") != "OFFLINE":
                        update_device_status(device["id"], "OFFLINE")
                        logger.info("Device %s marked OFFLINE (last seen: %s)", device["id"], last_seen)
                except (ValueError, TypeError):
                    pass
            elif device.get("status") == "ONLINE":
                update_device_status(device["id"], "OFFLINE")

    except Exception:
        logger.exception("Device offline check job failed.")


def _run_threat_intel_refresh() -> None:
    """Re-query AbuseIPDB for expiring cache entries."""
    try:
        import asyncio
        from ai_sentinel.storage.database import get_expiring_threat_intel
        from ai_sentinel.explainability.threat_intel import query_abuseipdb

        expiring = get_expiring_threat_intel(limit=50)
        if not expiring:
            return

        async def _refresh():
            for entry in expiring:
                await query_abuseipdb(entry["ip_address"])

        asyncio.run(_refresh())
        logger.info("Threat intel refresh: processed %d entries.", len(expiring))
    except Exception:
        logger.exception("Threat intel refresh job failed.")


def _run_geo_resolution() -> None:
    """Resolve unresolved IP addresses using geopy."""
    try:
        from ai_sentinel.jobs.geo_resolver import run
        run()
    except Exception:
        logger.exception("Geo resolution job failed.")


def _run_drift_detection() -> None:
    """Run feature drift detection across models."""
    try:
        from ai_sentinel.detection.drift_detector import run
        run()
    except Exception:
        logger.exception("Feature drift detection job failed.")


def _run_data_cleanup() -> None:
    """Delete data past the retention period."""
    try:
        from ai_sentinel.storage.database import cleanup_old_data
        deleted = cleanup_old_data()
        logger.info("Data cleanup: removed %d expired rows.", deleted)
    except Exception:
        logger.exception("Data cleanup job failed.")
