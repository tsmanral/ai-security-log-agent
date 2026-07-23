<div align="center">

# 🛡️ AI-Sentinel

### Open-source, explainable SIEM anomaly detection — built to run anywhere.

**Real-time, multi-source log detection with ML ensembles, SHAP explainability, and human-readable threat narratives — no LLM API keys required.**

<br/>

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=flat-square)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/smoke_tests-27%2F27_passing-brightgreen.svg?style=flat-square)](tests/test_v4_smoke.py)
[![GitHub Stars](https://img.shields.io/github/stars/tsmanral/ai-security-log-agent?style=flat-square)](https://github.com/tsmanral/ai-security-log-agent/stargazers)

</div>

---

## Why AI-Sentinel?

Enterprise SIEMs like Splunk and Microsoft Sentinel are powerful — and heavy, expensive, and opaque. Lightweight consumer tools watch the network but have no real detection intelligence. **AI-Sentinel fills the gap**: a self-hostable SOC platform that explains *why* every alert fired.

- 🧠 **Multi-layer ML detection** — statistical baselining (Z-score), ensemble models (Isolation Forest, LOF, One-Class SVM), and a PyTorch autoencoder, with drift tracking via Population Stability Index.
- 🔍 **Explainable by design** — SHAP feature attribution, composite severity scoring with a plain-English breakdown per alert, and MITRE ATT&CK technique mapping with confidence scores.
- 🌐 **Multi-source ingestion** — parsers for SSH auth logs, Syslog, Windows Events, network flows (NetFlow / firewall), and endpoint telemetry through a single raw-log API.
- 📖 **Threat narratives without an LLM** — a pure-template case-file generator turns correlated anomalies into readable incident stories. Zero API keys, zero recurring cost.
- 🚨 **Detection rules that matter** — brute force, credential stuffing, port scans, exfiltration, LOLBin abuse, persistence, and lateral movement, all with tunable thresholds and analyst feedback loops.
- 📊 **Full SOC dashboard** — 10-page Streamlit interface: live alerts, investigation case files, multi-source health, threat intel (AbuseIPDB), model analytics, device behavior, feedback & threshold tuning, and admin management with RBAC + JWT auth.

## Quick Start

> Requires **Python 3.12** (scikit-learn is not yet compatible with 3.14 — check versions with `py -0` on Windows).

```bash
# 1. Clone and set up
git clone https://github.com/tsmanral/ai-security-log-agent.git
cd ai-security-log-agent
py -3.12 -m venv venv            # Linux/macOS: python3.12 -m venv venv
venv/Scripts/pip install -r requirements.txt   # Linux/macOS: venv/bin/pip

# 2. Start the API server (creates the database on first launch)
venv/Scripts/python -m uvicorn server:app --host 0.0.0.0 --port 8000

# 3. In a second terminal, start the dashboard
venv/Scripts/streamlit run ai_sentinel/ui/dashboard.py
```

Open **http://localhost:8501**, register an account, and connect your first device from the **Connect My Device** page — it generates a one-line install command for any Linux host.

To validate the full pipeline (parsers, rules, severity, narratives, DB, scheduler):

```bash
venv/Scripts/python tests/test_v4_smoke.py    # expected: 27/27 passed
```

### Docker (production)

```bash
cp .env.example .env    # set JWT secrets, TLS flags, optional AbuseIPDB key
docker compose up -d
```

This starts the API (`:8000`), the dashboard (`:8501`), and an idle agent simulator.

## Ingesting Logs

Any log line from any source, through one endpoint:

```bash
curl -X POST http://localhost:8000/api/events/raw \
  -H "Content-Type: application/json" \
  -H "X-Device-Id: <device-id>" -H "X-Api-Key: <api-key>" \
  -d '{"lines": [{"raw_line": "Jan  5 12:34:56 server sudo[999]: root : COMMAND=/bin/bash", "source_hint": "syslog"}]}'
```

Per-source ingestion health is available at `GET /api/events/stats`.

## Architecture

```mermaid
graph TD
    A[Endpoint Agents] -->|HTTPS + API Key| B[Ingestion API]
    R[Raw Log Sources] -->|HTTPS + API Key| V[Raw Ingestion API]
    V --> IM[Ingestion Manager<br/>Syslog · Windows · NetFlow · Endpoint · SSH]
    IM --> FE[Feature Extractor]
    B --> C[Detection Orchestrator<br/>Z-Score · ML Ensemble · Autoencoder]
    FE --> RE[Rule Engine + Lateral Movement]
    RE --> SV[Dynamic Severity Scoring]
    C --> SV
    SV --> INC[Incident Grouping]
    INC --> NB[Narrative Builder<br/>SHAP + MITRE ATT&CK]
    NB --> DB[(SQLite)]
    DB --> DASH[SOC Dashboard]
```

Background jobs (APScheduler) handle cross-source correlation, lateral-movement scans, metrics pre-aggregation, geo-resolution, threat-intel caching, drift detection, and data retention — no external queue or cron required.

## Project Structure

```
ai_sentinel/        Core platform: auth, ingestion, detection, storage, scheduler, UI
tests/              Test suite + end-to-end smoke tests
datasets/           Synthetic SSH log generator for local experimentation
fleet_simulator.py  Multi-device fleet traffic simulator
windows_agent_simulator.py  All-in-one Windows test agent
server.py           FastAPI entry point
```

## Contributing

Contributions are welcome! The workflow is intentionally simple:

1. **Fork** the repo and create a feature branch from `main` (`git checkout -b feature/my-improvement`).
2. Make your change and run the smoke tests (`python tests/test_v4_smoke.py`).
3. Open a **pull request** against `main` with a clear description.

`main` is the only long-lived branch — all work lands through short-lived feature branches and PRs. Bug reports and feature ideas are welcome in [Issues](https://github.com/tsmanral/ai-security-log-agent/issues).

## License

Distributed under the **GNU Affero General Public License v3.0**. See [LICENSE](LICENSE) for details.

## Author

**Tribhuwan Singh**

[![GitHub](https://img.shields.io/badge/GitHub-tsmanral-181717?style=flat-square&logo=github)](https://github.com/tsmanral)
[![Email](https://img.shields.io/badge/Email-tribhuwan.singh1108%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white)](mailto:tribhuwan.singh1108@gmail.com)

## Contributors

Thanks to everyone who has contributed to AI-Sentinel:

<a href="https://github.com/tsmanral/ai-security-log-agent/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=tsmanral/ai-security-log-agent" alt="Contributors" />
</a>

---

<div align="center">
⭐ If AI-Sentinel is useful to you, consider starring the repo — it helps the project reach more people.
</div>
