# AI-Sentinel V2 — Lab Deployment Configuration

## Overview

This guide deploys AI-Sentinel V2 on a **single KVM VPS** (1 vCPU, 4 GB RAM,
50 GB disk) alongside a self-hosted n8n instance.

---

## Architecture on VPS

| Component | Port | Approx. RAM |
|-----------|------|-------------|
| FastAPI (uvicorn) — ingestion + onboard API | 8000 | 80–150 MB |
| Streamlit Dashboard | 8501 | 100–200 MB |
| n8n (existing) | 5678 | 200–400 MB |
| SQLite | — | Negligible |
| **Total** | | **~400–750 MB** |

Remaining ~3.2 GB is available for the OS, buffers, and detection workloads.

---

## systemd Service Files

### API Server

```ini
# /etc/systemd/system/ai-sentinel-api.service
[Unit]
Description=AI-Sentinel V2 API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=sentinel
WorkingDirectory=/opt/ai-sentinel
ExecStart=/opt/ai-sentinel/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10
Environment=SENTINEL_SECRET_KEY=<REPLACE_WITH_SECURE_KEY>

[Install]
WantedBy=multi-user.target
```

### Streamlit Dashboard

```ini
# /etc/systemd/system/ai-sentinel-dashboard.service
[Unit]
Description=AI-Sentinel V2 Dashboard
After=ai-sentinel-api.service

[Service]
Type=simple
User=sentinel
WorkingDirectory=/opt/ai-sentinel
ExecStart=/opt/ai-sentinel/venv/bin/streamlit run ai_sentinel/ui/dashboard.py --server.port 8501 --server.headless true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable & Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-sentinel-api ai-sentinel-dashboard
sudo systemctl start  ai-sentinel-api ai-sentinel-dashboard
```

---

## Nginx Reverse Proxy (Optional)

```nginx
server {
    server_name sentinel.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:8000/static/;
    }

    listen 443 ssl;
    ssl_certificate     /etc/letsencrypt/live/sentinel.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sentinel.yourdomain.com/privkey.pem;
}
```

---

## V1 Legacy Interop

- **V1 is NOT required for V2**.  V2 uses its own database (`sentinel_v2.db`)
  and does not depend on the V1 `agent/` package.
- `main.py` remains available as a standalone dev/demo tool.

### Optional: Import V1 data

```python
# Helper script (run manually, one-time)
import sqlite3, json

v1 = sqlite3.connect("data/logs.db")
v2 = sqlite3.connect("data/sentinel_v2.db")

for row in v1.execute("SELECT * FROM parsed_logs"):
    v2.execute(
        """INSERT INTO normalized_events
           (timestamp, host, effective_username, source_ip, event_type,
            raw_message, attributes, is_synthetic)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
        (row[1], row[2], row[4], row[3], row[5], row[6], '{}'),
    )
v2.commit()
```

---

## Resource Tuning

| Parameter | Config location | Default | Purpose |
|-----------|----------------|---------|---------|
| `RETENTION_DAYS` | `config.py` | 30 | Auto-delete events older than N days |
| `MAX_EVENTS_PER_BATCH` | `config.py` | 100 | Cap events per API call |
| `DETECTION_THROTTLE_SECONDS` | `config.py` | 5.0 | Min gap between online detection runs |
| `AUTOENCODER_EPOCHS` | `config.py` | 50 | Lower = faster training, higher = better model |

When the VPS gets busy, increase `DETECTION_THROTTLE_SECONDS` and lower
`AUTOENCODER_EPOCHS` to reduce CPU spikes.

**Retention cron job** (optional):

```bash
# Weekly cleanup via cron
0 3 * * 0  /opt/ai-sentinel/venv/bin/python -c "from ai_sentinel.storage.database import cleanup_old_data; cleanup_old_data()"
```

---

## Coexistence with n8n

- n8n runs on port 5678 (default).
- AI-Sentinel uses ports 8000 and 8501.
- No port conflicts.  Both can run behind the same Nginx with different
  `server_name` or `location` blocks.
