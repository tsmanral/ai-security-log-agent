"""
AI-Sentinel V2 — Linux endpoint agent.

Lightweight daemon that tails ``/var/log/auth.log`` (configurable),
parses SSH and sudo events, and sends them in batches over HTTPS to the
AI-Sentinel collector.

Designed to run as a systemd service on the monitored host.

Usage::

    python linux_agent.py --config /etc/ai-sentinel-agent/config.yml
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to use httpx (async-capable), fall back to urllib for zero-dep installs
try:
    import httpx  # type: ignore

    _HAS_HTTPX = True
except ImportError:
    import urllib.request
    import urllib.error

    _HAS_HTTPX = False

# Try to use yaml for config; fall back to a simple key: value parser
try:
    import yaml  # type: ignore

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ai-sentinel-agent] %(levelname)s %(message)s",
)
logger = logging.getLogger("ai-sentinel-agent")

# ── Configuration ─────────────────────────────────────────────────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    "server_url": "http://localhost:8000",
    "collector_endpoint": "/api/events/batch",
    "device_id": "",
    "api_key": "",
    "log_paths": ["/var/log/auth.log"],
    "batch_size": 50,
    "flush_interval_seconds": 10,
}


def load_config(path: str) -> Dict[str, Any]:
    """Load agent config from a YAML file."""
    cfg = dict(DEFAULT_CONFIG)
    p = Path(path)
    if not p.exists():
        logger.warning("Config file %s not found, using defaults.", path)
        return cfg

    with open(p) as f:
        if _HAS_YAML:
            loaded = yaml.safe_load(f) or {}
        else:
            # Minimal key: value parser
            loaded = {}
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    loaded[k.strip().strip('"')] = v.strip().strip('"')

    cfg.update(loaded)
    return cfg


# ── Simple SSH / sudo line parser (subset of parsers_linux.py) ────────────

import re

_AUTH_RE = re.compile(
    r"(Failed|Accepted)\s+(password|publickey)\s+(?:for invalid user\s+)?"
    r"(?:for\s+)?(\S+)\s+from\s+(\S+)\s+port\s+(\d+)"
)
_SUDO_RE = re.compile(r"(\S+)\s*:\s*.*COMMAND=(.*)")
_SYSLOG_RE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+\S+\[(?P<pid>\d+)\]:\s+(?P<message>.*)$"
)


def _parse_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a syslog line into a minimal event dict, or return None."""
    line = line.strip()
    if not line:
        return None

    m = _SYSLOG_RE.match(line)
    if not m:
        return None

    g = m.groupdict()
    from datetime import datetime

    try:
        ts = datetime.strptime(
            f"{datetime.now().year} {g['month']} {g['day']} {g['time']}",
            "%Y %b %d %H:%M:%S",
        )
    except ValueError:
        return None

    msg = g["message"]

    # SSH auth
    auth = _AUTH_RE.search(msg)
    if auth:
        return {
            "timestamp": ts.isoformat(),
            "host": g["host"],
            "effective_username": auth.group(3),
            "source_ip": auth.group(4),
            "event_type": f"ssh_{auth.group(1).lower()}_{auth.group(2).lower()}",
            "raw_message": line[:4096],
            "attributes": {"src_port": int(auth.group(5))},
        }

    # Sudo
    sudo = _SUDO_RE.search(msg)
    if sudo:
        return {
            "timestamp": ts.isoformat(),
            "host": g["host"],
            "effective_username": sudo.group(1),
            "source_ip": None,
            "event_type": "sudo_command",
            "raw_message": line[:4096],
            "attributes": {"command": sudo.group(2).strip()},
        }

    return None  # skip unrecognised lines


# ── HTTP sender with exponential backoff ──────────────────────────────────

MAX_BACKOFF = 60  # seconds


def _send_batch(
    events: List[Dict[str, Any]],
    server_url: str,
    endpoint: str,
    device_id: str,
    api_key: str,
) -> bool:
    """
    POST a batch of events to the collector.  Returns True on success.

    Implements exponential backoff on failure (1 → 2 → 4 → ... → 60 s).
    """
    url = f"{server_url.rstrip('/')}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-Device-Id": device_id,
        "X-Api-Key": api_key,
    }
    body = json.dumps({"events": events}).encode()

    backoff = 1
    while True:
        try:
            if _HAS_HTTPX:
                with httpx.Client(timeout=15) as client:
                    resp = client.post(url, content=body, headers=headers)
                    resp.raise_for_status()
            else:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                urllib.request.urlopen(req, timeout=15)

            logger.debug("Sent batch of %d events.", len(events))
            return True

        except Exception as exc:
            logger.warning("Send failed (%s), retrying in %ds ...", exc, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)


# ── File tailer ───────────────────────────────────────────────────────────


def _tail(path: str, batch_size: int, flush_interval: float, cfg: Dict[str, Any]):
    """
    Tail a log file, parse lines, batch them, and send periodically.
    """
    logger.info("Tailing %s  (batch=%d, flush=%ds)", path, batch_size, flush_interval)
    buffer: List[Dict[str, Any]] = []
    last_flush = time.time()

    with open(path, "r") as f:
        # Seek to end so we only send new lines
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if line:
                ev = _parse_line(line)
                if ev:
                    buffer.append(ev)

            now = time.time()
            should_flush = (
                len(buffer) >= batch_size or (buffer and now - last_flush >= flush_interval)
            )

            if should_flush:
                _send_batch(
                    buffer,
                    cfg["server_url"],
                    cfg["collector_endpoint"],
                    cfg["device_id"],
                    cfg["api_key"],
                )
                buffer.clear()
                last_flush = now

            if not line:
                time.sleep(0.5)  # no new data, sleep briefly


# ── Main ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="AI-Sentinel Linux Endpoint Agent")
    parser.add_argument("--config", default="/etc/ai-sentinel-agent/config.yml")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if not cfg.get("device_id") or not cfg.get("api_key"):
        logger.error("device_id and api_key must be set in config.")
        sys.exit(1)

    log_paths = cfg.get("log_paths", ["/var/log/auth.log"])
    if isinstance(log_paths, str):
        # Fallback parser creates a string; handle empty or comma-separated
        log_paths = [p.strip() for p in log_paths.split(",") if p.strip()]

    # If the fallback parser failed to parse the YAML list, it might be empty
    if not log_paths:
        log_paths = ["/var/log/auth.log"]

    # For simplicity, tail the first configured path (single-threaded)
    # A production agent could spawn a thread per path
    target = log_paths[0]
    _tail(
        target,
        int(cfg.get("batch_size", 50)),
        float(cfg.get("flush_interval_seconds", 10)),
        cfg,
    )


if __name__ == "__main__":
    main()
