"""
AI-Sentinel V2 — Registration token manager.

Generates single-use, time-limited tokens that tie a device registration
request back to the user who initiated it in the dashboard.
"""

import secrets
from datetime import datetime, timedelta

from ai_sentinel.config import REGISTRATION_TOKEN_LIFETIME_MINUTES
from ai_sentinel.storage.database import consume_token, store_token

from typing import Optional, Dict, Any


def generate_token(user_id: str) -> str:
    """
    Create a new registration token for *user_id*.

    The token is a 32-char URL-safe random string, valid for
    ``REGISTRATION_TOKEN_LIFETIME_MINUTES`` minutes.

    Returns:
        The plain-text token string (shown to the user once).
    """
    token = secrets.token_urlsafe(24)  # 32-char URL-safe string
    expires = datetime.utcnow() + timedelta(minutes=REGISTRATION_TOKEN_LIFETIME_MINUTES)
    store_token(token, user_id, expires)
    return token


def validate_and_consume(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a registration token.

    If valid (exists, not used, not expired), marks it as consumed and
    returns the token row including ``user_id``.  Otherwise returns *None*.
    """
    return consume_token(token)
