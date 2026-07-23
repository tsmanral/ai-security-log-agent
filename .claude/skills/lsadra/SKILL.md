```markdown
# lsadra Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill teaches you how to contribute to the `lsadra` Python codebase, focusing on its coding conventions, commit patterns, and common development workflows. You'll learn how to implement security fixes, update configuration, and work with rate limiting, all while following the project's established practices for code style, testing, and documentation.

## Coding Conventions

- **Language:** Python (no framework detected)
- **File Naming:** Use `snake_case` for all Python files.
  - Example: `api_ingestion.py`, `device_registration.py`
- **Import Style:** Prefer **relative imports** within the package.
  - Example:
    ```python
    from .config import get_config
    from .ingestion import api_ingestion
    ```
- **Export Style:** Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ["rate_limiter", "RateLimitException"]
    ```
- **Commit Messages:** Use [Conventional Commits](https://www.conventionalcommits.org/) with prefixes like `fix` and `test`.
  - Example:
    ```
    fix(ratelimit): prevent bypass via header spoofing
    test(config): add regression test for missing env var
    ```

## Workflows

### Security Fix with Regression Test
**Trigger:** When fixing a security vulnerability or hardening a security control  
**Command:** `/security-fix`

1. Edit one or more implementation files to apply the security fix (e.g., `config.py`, `api_ingestion.py`, `device_registration.py`, `ratelimit.py`).
2. Edit or add a dedicated regression test file under `tests/security/` (typically `test_s6_XX_*.py`) to cover the specific issue.
3. Optionally update `.env.example` and/or `requirements.txt` if configuration or dependencies change.
4. Run and verify the regression suite:
    ```bash
    pytest tests/security/
    ```
**Example:**
```python
# lsadra/ratelimit.py
def is_rate_limited(user_id):
    # ... security fix applied here ...
    pass

# tests/security/test_s6_05_ratelimit_lru.py
def test_rate_limit_bypass():
    # ... regression test for bypass ...
    pass
```

---

### Add or Update Config with Env Doc
**Trigger:** When introducing or changing an environment variable or config setting  
**Command:** `/add-config`

1. Edit `lsadra/config.py` to add or update the config variable.
2. Edit `.env.example` to document the new or changed environment variable.
3. Edit relevant code files to use the new config (e.g., `server.py`, `api_ingestion.py`).
4. Add or update regression tests if needed.

**Example:**
```python
# lsadra/config.py
NEW_FEATURE_FLAG = os.getenv("NEW_FEATURE_FLAG", "false")

# .env.example
# NEW_FEATURE_FLAG=false

# server.py
from lsadra.config import NEW_FEATURE_FLAG
if NEW_FEATURE_FLAG == "true":
    enable_new_feature()
```

---

### Rate Limiter Implementation and Hardening
**Trigger:** When adding a new rate limiter or fixing bypasses/DoS in existing rate limiting logic  
**Command:** `/rate-limit-fix`

1. Create or edit `lsadra/ratelimit.py` to implement or update the rate limiter logic.
2. Edit code that uses the rate limiter (e.g., `api_ingestion.py`, `device_registration.py`).
3. Edit `lsadra/config.py` to add or update rate limit config variables.
4. Add or update regression tests in `tests/security/test_s6_05_ratelimit_lru.py`.
5. Verify that bypasses and DoS vectors are covered by tests.

**Example:**
```python
# lsadra/ratelimit.py
class RateLimiter:
    def __init__(self, max_requests):
        self.max_requests = max_requests
        # ... implementation ...

# tests/security/test_s6_05_ratelimit_lru.py
def test_rate_limit_dos_protection():
    # ... test for DoS vector ...
    pass
```

## Testing Patterns

- **Test File Pattern:** While the main codebase is Python, some test files use the pattern `*.test.ts` (TypeScript), but security regression tests are under `tests/security/` and named like `test_s6_XX_*.py`.
- **Testing Framework:** Not explicitly specified, but `pytest` is used for running Python tests.
- **Regression Tests:** For every security or config change, add or update a test under `tests/security/`.

**Example:**
```python
# tests/security/test_s6_10_config.py
def test_missing_env_var():
    # ... test logic ...
    pass
```

## Commands

| Command           | Purpose                                                         |
|-------------------|-----------------------------------------------------------------|
| /security-fix     | Start a security fix with a regression test                     |
| /add-config       | Add or update a config variable and document it in .env.example |
| /rate-limit-fix   | Implement or harden rate limiting logic and add regression test |
```
