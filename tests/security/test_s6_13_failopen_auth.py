"""
Regression test — §6 #13: Fail-open device authentication.

Attacker story: device-auth mismatch used to only log a warning and return the
device (a dev-mode pass-through) — fail-OPEN. Any attacker who knew a valid
device_id could ingest events with any (or no) API key. The fix makes
_authenticate_device fail CLOSED: the stored bcrypt hash is verified, and a
wrong/empty key is rejected with HTTP 401.

This module exercises the bcrypt-verify branch explicitly (stored_hash starts
with "$2"), distinct from #01 which covers the empty-stored-hash and legacy
plaintext branches.

All data below is SYNTHETIC — obviously-fake device IDs and keys only.
"""

import bcrypt
import pytest
from fastapi import HTTPException

from lsadra.ingestion.api_ingestion import _authenticate_device
from lsadra.storage.database import create_device, create_user
from tests.fixtures import setup_test_db

# ── Synthetic constants (never real credentials) ─────────────────────────────
_DEVICE_ID = "test-device-001"
_CORRECT_KEY = "test-secret-abc123"
_WRONG_KEY = "test-wrong-key-999"


@pytest.fixture(autouse=True)
def _test_db(tmp_path):
    """
    Point the DB at a fresh tmp sqlite file and create the devices table.

    Must run before any create_device call: setup_test_db patches
    config.DB_PATH / db_module.DB_PATH and calls init_db().
    """
    setup_test_db(tmp_path)


@pytest.fixture
def _bcrypt_device():
    """Register a device whose api_key_hash is a real bcrypt hash of _CORRECT_KEY."""
    stored = bcrypt.hashpw(_CORRECT_KEY.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    assert stored.startswith("$2"), "expected a bcrypt ($2) hash for this test"
    # devices.user_id is a FK to users (PRAGMA foreign_keys=ON) — create the
    # owner first. Synthetic user only.
    create_user("user-1", "user-1", "synthetic-not-a-real-hash", "ANALYST")
    create_device(_DEVICE_ID, "user-1", "test-host", "linux", stored)
    return _DEVICE_ID


def test_bcrypt_correct_key_authenticates(_bcrypt_device):
    """POSITIVE bcrypt path: the correct key verifies against the $2 hash."""
    device = _authenticate_device(x_device_id=_bcrypt_device, x_api_key=_CORRECT_KEY)
    assert device["id"] == _DEVICE_ID


def test_bcrypt_wrong_key_rejected(_bcrypt_device):
    """
    LOAD-BEARING: a wrong key against the bcrypt row must be rejected 401.

    Pre-fix (fail-open pass-through) this returned the device instead of
    raising — reverting the fix makes this assertion FAIL.
    """
    with pytest.raises(HTTPException) as ei:
        _authenticate_device(x_device_id=_bcrypt_device, x_api_key=_WRONG_KEY)
    assert ei.value.status_code == 401
    assert ei.value.detail == "Invalid API key."


def test_bcrypt_empty_key_rejected(_bcrypt_device):
    """Guard rail: an empty API key against the bcrypt row also fails closed (401)."""
    with pytest.raises(HTTPException) as ei:
        _authenticate_device(x_device_id=_bcrypt_device, x_api_key="")
    assert ei.value.status_code == 401
    assert ei.value.detail == "Invalid API key."


def test_bcrypt_oversize_key_fails_closed(_bcrypt_device):
    """
    §6 #15 hardening: direct bcrypt rejects keys > 72 bytes with ValueError.
    An attacker sending an over-long key must get a 401 (fail CLOSED), never a
    500 or a pass-through. Pins the try/except around bcrypt.checkpw.
    """
    with pytest.raises(HTTPException) as ei:
        _authenticate_device(x_device_id=_bcrypt_device, x_api_key="A" * 200)
    assert ei.value.status_code == 401
    assert ei.value.detail == "Invalid API key."
