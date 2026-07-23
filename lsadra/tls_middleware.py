"""
LSADRA V3 — TLS enforcement middleware.

When ``REQUIRE_TLS`` is enabled, this middleware rejects any non-HTTPS
request with a 403 Forbidden response. Health endpoints are exempted
so that internal load balancers and probes continue to work.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from lsadra.config import REQUIRE_TLS

logger = logging.getLogger(__name__)

# Paths that are allowed without TLS (health checks, internal probes)
_EXEMPT_PATHS = {"/", "/api/health", "/docs", "/openapi.json", "/redoc"}


class TLSEnforcementMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces HTTPS connections.

    If ``REQUIRE_TLS`` is True, any HTTP request (not HTTPS) that hits a
    non-exempt endpoint receives a 403 response.
    """

    async def dispatch(self, request: Request, call_next):
        if REQUIRE_TLS:
            scheme = request.url.scheme
            forwarded_proto = request.headers.get("x-forwarded-proto", scheme)

            if forwarded_proto != "https" and request.url.path not in _EXEMPT_PATHS:
                logger.warning(
                    "Blocked non-TLS request to %s from %s",
                    request.url.path,
                    request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "TLS is required. Use HTTPS to access this endpoint."
                    },
                )

        response = await call_next(request)
        return response
