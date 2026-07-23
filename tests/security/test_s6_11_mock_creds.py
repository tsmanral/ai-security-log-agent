"""Regression test for §6 #11 — Client-side mock credentials seeded in production.

Attacker story: A production SPA build shipped an offline `login()` fallback whose
`SEED_CREDS` table unconditionally contained `admin`/`admin` (plus demo users). When
the backend was offline, the browser authenticated `admin`/`admin` client-side and
granted an ADMIN session with no server involvement at all.

The fix (commit c78e30a) gates the default seed behind a build-time DEV guard:
`SEED_CREDS` is a ternary on `import.meta.env.DEV` — the real credential object in dev
builds, and `{}` (empty) in production builds. In prod, `resolveCred('admin')` returns
null, so the offline `login()` fallback cannot authenticate admin client-side.

There is no JS/TS runtime in this Python harness, so this is a SOURCE-TEXT INVARIANT
check: open frontend/src/services/api.ts and assert the seed declaration is DEV-gated
and that no unconditional admin/admin seeding remains. A straight revert (restoring the
ungated object literal) drops the `import.meta.env.DEV` token from the declaration and
FAILS this test. No DB/app/TestClient plumbing is needed here.
"""

import pathlib

# tests/security/test_s6_11_mock_creds.py -> parents[2] == repo root
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
API_TS = REPO_ROOT / "frontend" / "src" / "services" / "api.ts"

# Build-time guard token the fix relies on. If the seed is reverted to an
# unconditional object literal, this token is no longer wrapped around the
# SEED_CREDS declaration.
DEV_GUARD = "import.meta.env.DEV"

# Pre-fix shape: SEED_CREDS assigned a direct object literal (no DEV ternary),
# with admin/admin as the first entry. The exact pre-fix source (commit c78e30a)
# indents the object entries with two spaces directly after `= {`. Its presence
# means the fix was reverted.
PREFIX_UNCONDITIONAL_SEED = (
    "= {\n  admin: { password: 'admin', role: 'ADMIN' }"
)


def _read_api_ts() -> str:
    assert API_TS.is_file(), f"expected frontend source at {API_TS}"
    return API_TS.read_text(encoding="utf-8")


def _seed_creds_declaration(source: str) -> str:
    """Slice the SEED_CREDS declaration window: from `const SEED_CREDS` up to and
    including its terminating `};`."""
    start = source.find("const SEED_CREDS")
    assert start != -1, "could not locate `const SEED_CREDS` declaration in api.ts"
    end = source.find("};", start)
    assert end != -1, "could not locate terminator `};` for SEED_CREDS declaration"
    return source[start : end + 2]


def test_seed_creds_declaration_is_dev_gated():
    """The SEED_CREDS default seed must be wrapped by the build-time DEV guard,
    so production builds seed nothing."""
    source = _read_api_ts()
    declaration = _seed_creds_declaration(source)
    assert DEV_GUARD in declaration, (
        "SEED_CREDS default mock-credential seed is not gated behind "
        f"`{DEV_GUARD}` — production builds would seed admin/admin and "
        "authenticate client-side offline (§6 #11 regression)."
    )


def test_no_unconditional_admin_seeding():
    """No ungated `admin: { password: 'admin', role: 'ADMIN' }` object-literal seed
    may remain — that is the exact pre-fix shape that granted ADMIN in prod."""
    source = _read_api_ts()
    assert PREFIX_UNCONDITIONAL_SEED not in source, (
        "Found pre-fix unconditional SEED_CREDS object literal seeding "
        "admin/admin with no DEV ternary — the §6 #11 fix has been reverted."
    )


def test_offline_login_admin_seed_requires_dev_build():
    """End-to-end source invariant: the admin/admin seed and its DEV guard must
    co-occur inside the same declaration window (the seed only exists in the
    dev branch of the ternary), never as a standalone unconditional assignment."""
    source = _read_api_ts()
    declaration = _seed_creds_declaration(source)

    if "admin: { password: 'admin', role: 'ADMIN' }" in declaration:
        # If the admin seed is present at all, it MUST be inside the DEV branch.
        assert DEV_GUARD in declaration, (
            "admin/admin seed present but not DEV-gated — production builds "
            "would authenticate admin client-side (§6 #11)."
        )
    # And regardless, the prod branch must collapse the seed to empty.
    assert ": {}" in declaration, (
        "SEED_CREDS declaration lacks the production-empty `: {}` branch — "
        "production builds must seed no mock credentials (§6 #11)."
    )
