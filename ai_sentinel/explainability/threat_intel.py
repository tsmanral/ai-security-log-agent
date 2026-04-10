"""
AI-Sentinel V3 — Threat Intelligence enrichment.

Queries AbuseIPDB for IP reputation data and caches results in SQLite.
Supports background querying via FastAPI BackgroundTasks.
"""

import logging
from typing import Any, Dict, Optional

from ai_sentinel.config import ABUSEIPDB_API_KEY, THREAT_INTEL_CACHE_HOURS
from ai_sentinel.storage.database import get_threat_intel, upsert_threat_intel

logger = logging.getLogger(__name__)


async def query_abuseipdb(ip_address: str) -> Optional[Dict[str, Any]]:
    """
    Query AbuseIPDB for threat intelligence on an IP address.

    Returns the parsed response dict, or None on failure.
    Results are cached in the threat_intel_cache table.
    """
    # Check cache first
    cached = get_threat_intel(ip_address)
    if cached:
        logger.debug("Threat intel cache hit for %s", ip_address)
        return cached

    if not ABUSEIPDB_API_KEY:
        logger.debug("No AbuseIPDB API key configured — skipping lookup for %s", ip_address)
        return None

    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.abuseipdb.com/api/v2/check",
                headers={
                    "Key": ABUSEIPDB_API_KEY,
                    "Accept": "application/json",
                },
                params={
                    "ipAddress": ip_address,
                    "maxAgeInDays": "90",
                    "verbose": "",
                },
            )
            response.raise_for_status()
            data = response.json().get("data", {})

        # Cache the result
        upsert_threat_intel(
            ip_address=ip_address,
            abuse_score=data.get("abuseConfidenceScore", 0),
            country_code=data.get("countryCode", ""),
            isp=data.get("isp", ""),
            domain=data.get("domain", ""),
            is_tor=data.get("isTor", False),
            total_reports=data.get("totalReports", 0),
            last_reported=data.get("lastReportedAt", ""),
            raw_response=str(data),
            cache_hours=THREAT_INTEL_CACHE_HOURS,
        )

        logger.info(
            "AbuseIPDB lookup for %s: score=%d, reports=%d",
            ip_address,
            data.get("abuseConfidenceScore", 0),
            data.get("totalReports", 0),
        )
        return data

    except ImportError:
        logger.warning("httpx not installed — cannot query AbuseIPDB.")
        return None
    except Exception:
        logger.exception("AbuseIPDB lookup failed for %s", ip_address)
        return None


def enrich_anomaly_background(ip_address: str) -> None:
    """
    Synchronous wrapper for background task enrichment.
    Can be called from FastAPI BackgroundTasks.
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule in the existing event loop
            asyncio.ensure_future(query_abuseipdb(ip_address))
        else:
            asyncio.run(query_abuseipdb(ip_address))
    except RuntimeError:
        asyncio.run(query_abuseipdb(ip_address))


def get_ip_reputation(ip_address: str) -> Dict[str, Any]:
    """
    Get threat intelligence for an IP (cache-only, synchronous).

    Returns a dict with abuse_score, country_code, etc., or an empty dict.
    """
    cached = get_threat_intel(ip_address)
    if cached:
        return {
            "ip": ip_address,
            "abuse_score": cached.get("abuse_score", 0),
            "country_code": cached.get("country_code", ""),
            "isp": cached.get("isp", ""),
            "domain": cached.get("domain", ""),
            "is_tor": cached.get("is_tor", False),
            "total_reports": cached.get("total_reports", 0),
        }
    return {"ip": ip_address, "abuse_score": None, "status": "not_queried"}
