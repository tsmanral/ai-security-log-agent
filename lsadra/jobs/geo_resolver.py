"""
LSADRA V3 — IP geolocation resolver.

Uses the ``geopy`` Nominatim geocoder (or ipinfo fallback) to resolve
IP addresses stored in ``normalized_events`` that don't yet have entries
in ``ip_geolocation``. Rate-limited to 1 request/second per Nominatim ToS.
"""

import logging
import time
from typing import Optional, Tuple

from lsadra.storage.database import get_unresolved_ips, upsert_ip_geolocation

logger = logging.getLogger(__name__)

# Rate limit: 1 request per second (Nominatim ToS)
_RATE_LIMIT_SECONDS = 1.0


def _resolve_ip(ip_address: str) -> Optional[Tuple[float, float, str, str]]:
    """
    Attempt to geolocate an IP address.

    Returns (latitude, longitude, city, country) or None on failure.
    """
    # Skip private / reserved IPs
    if _is_private_ip(ip_address):
        return (0.0, 0.0, "Private", "Local")

    try:
        # Try ipinfo.io (free, no API key needed for basic lookups)
        import httpx

        response = httpx.get(
            f"https://ipinfo.io/{ip_address}/json",
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            loc = data.get("loc", "0,0").split(",")
            lat = float(loc[0]) if len(loc) >= 2 else 0.0
            lon = float(loc[1]) if len(loc) >= 2 else 0.0
            city = data.get("city", "")
            country = data.get("country", "")
            return (lat, lon, city, country)

    except ImportError:
        logger.debug("httpx not available for IP geolocation.")
    except Exception:
        logger.debug("ipinfo.io lookup failed for %s", ip_address)

    # Fallback: try geopy Nominatim
    try:
        from geopy.geocoders import Nominatim

        geolocator = Nominatim(user_agent="lsadra-v3")
        location = geolocator.geocode(ip_address)
        if location:
            return (location.latitude, location.longitude, "", "")
    except ImportError:
        logger.debug("geopy not available for IP geolocation.")
    except Exception:
        logger.debug("Nominatim lookup failed for %s", ip_address)

    return None


def _is_private_ip(ip: str) -> bool:
    """Check if an IP address is private/reserved."""
    try:
        import ipaddress
        return ipaddress.ip_address(ip).is_private
    except (ValueError, TypeError):
        return False


def run(limit: int = 50) -> int:
    """
    Resolve unresolved IPs from events.

    Returns the number of IPs successfully resolved.
    """
    unresolved = get_unresolved_ips(limit=limit)
    if not unresolved:
        logger.debug("No unresolved IPs to process.")
        return 0

    resolved_count = 0
    for ip in unresolved:
        result = _resolve_ip(ip)
        if result:
            lat, lon, city, country = result
            upsert_ip_geolocation(ip, lat, lon, city, country)
            resolved_count += 1
            logger.debug("Resolved IP %s → %s, %s", ip, city, country)

        # Rate limiting
        time.sleep(_RATE_LIMIT_SECONDS)

    logger.info("Geo resolution: resolved %d/%d IPs.", resolved_count, len(unresolved))
    return resolved_count
