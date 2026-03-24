# AI-Sentinel: SIEM Anomaly Detection Platform

"Bridging the Gap: An Open-Source, Explainable Alternative to Enterprise SIEM Anomaly Detection"

## Overview
AI-Sentinel is a lightweight, open-source research platform designed to emulate core SIEM capabilities seen in enterprise tools like Splunk and Microsoft Sentinel. It focuses on the detection of anomalies in SSH authentication logs using an ensemble of Machine Learning models (Isolation Forest, Local Outlier Factor, One-Class SVM).

A key feature of AI-Sentinel is **Explainability**. Instead of just flagging an event as an anomaly, the platform utilizes SHAP (SHapley Additive exPlanations) to interpret model decisions. These interpretations are then passed through a custom heuristic ruling engine to generate human-readable threat narratives and map incidents to MITRE ATT&CK techniques.

## Features
- **Centralized V2 SIEM Server**: FastAPI ingestion layer with HTTP payload validation and single-use JWT device registration tokens.
- **Endpoint Agents**: Standalone Python endpoint agent (`linux_agent.py`) that tails logs, batches them, and handles exponential HTTP backoff for transmission to the master server.
- **4-Layer Real-Time Detection**: Pipelined detection queue using per-entity Rolling Z-Scores, Isolation Forest, Local Outlier Factor, One-Class SVM, a Majority-Vote Ensemble, and an aggressive PyTorch Autoencoder.
- **Threat Narratives (XAI)**: Generates clear, non-technical explanations using SHAP aggregations mapped directly to MITRE ATT&CK techniques.
- **V2 Dashboard**: Streamlit interface containing User Profiles, Device Registration (w/ `curl` install scripts), Live Alerts, and User Journeys.

For a deep dive into the system design, view the [V2 Deployment Guide](deploy/lab_config.md) and [Architecture Diagrams](docs/architecture_diagrams.md).

## Project Structure
```text
ai-security-log-agent/
├── ai_sentinel/              # V2: Modern Agent-based SIEM Platform
│   ├── config.py             # Global constants and HTTP thresholds
│   ├── benchmarking/         # Real-time event simulation payload generators
│   ├── detection/            # 4-layer orchestration pipeline
│   ├── endpoint_agent/       # Linux/Windows standalone agent codes
│   ├── explainability/       # SHAP and threat narrative text generation
│   ├── features/             # Sliding-window features (IP diversity, etc.)
│   ├── ingestion/            # Server-side API and parser scripts
│   ├── models/               # PyTorch AE and scikit-learn statistical models
│   ├── onboarding/           # Secure device token generation & bash installers
│   ├── session/              # Cross-device user journey tracking
│   ├── storage/              # SQLite ORM functions and schema definitions
│   └── ui/                   # Modular multi-page Streamlit dashboard
├── deploy/                   # Systemd config for lab deployment
├── data/                     # Generated tracking SQLite DBs
├── server.py                 # V2: Central Collector API Entrypoint
├── windows_agent_simulator.py# Helper snippet to test agents on Windows
├── main.py                   # V1: Legacy single-machine script
└── README.md                   
```

## Quick Start (V2 Distributed Architecture)

### 1. Launch the Server & Dashboard
Install dependencies, then start the central API collector:
```bash
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```
In a new terminal window, start the V2 web interface:
```bash
python -m streamlit run ai_sentinel/ui/dashboard.py
```
*The dashboard will spawn at `http://localhost:8501`. Create an account on the "Login" page to access the master UI.*

### 2. Connect a Device (Windows Simulator)
Since WSL networking and Windows Event Logs are complex to test out of the box, we provide an all-in-one simulator script that runs the agent natively on your Windows host against a dummy log file:
```bash
python windows_agent_simulator.py
```
This script handles the token registration, spawns a dummy API connection, and creates `dummy_auth.log`. **To test detection, open `dummy_auth.log` in Notepad, paste this 10 times in a row, and save.**
```text
Mar 20 20:05:00 Test-PC sshd[123]: Failed password for admin from 10.0.0.99 port 5555
```
Watch the SIEM Alerts dashboard light up instantly!

### 3. Connect a Device (Linux/WSL Install)
If you have a Linux server or Linux VM on the same network:
1. Go to the **Connect My Device** page in your dashboard.
2. Copy the generated `curl` configuration string.
3. Paste it directly into the Linux VM's terminal. It will install the daemon and systemd service automatically.

To simulate attacks on a live Linux VM:
```bash
# Normal login Event:
sudo bash -c 'echo "$(date "+%b %d %H:%M:%S") my-wsl-device sshd[123]: Accepted publickey for admin from 10.0.0.50 port 5555" >> /var/log/auth.log'

# Brute Force attack (creates 15 failed logins):
for i in {1..15}; do
  sudo bash -c 'echo "$(date "+%b %d %H:%M:%S") my-wsl-device sshd[456]: Failed password for root from 192.168.1.99 port 22" >> /var/log/auth.log'
done
```

***

## Production Deployment (Hostinger or VPS)

When moving this platform to a production server (like Hostinger, DigitalOcean, or AWS), you only need to push the core code.

### 1. Files to Ignore (`git push`)
We have added a `.gitignore` file to prevent sensitive or local-only files from being pushed to your repository. **Do not commit:**
- `data/sentinel_v2.db` (Contains your local API keys and user accounts)
- `dummy_auth.log` (Local test logs)
- `agent_config.yml` (Your local agent's API key)
- `venv/` or `__pycache__/`

### 2. Deploying the Server
1. `git clone` your repository on the Hostinger VPS.
2. Install the requirements (`pip install -r requirements.txt`).
3. Start the API Server using a production process manager like `pm2` or `systemd`:
   ```bash
   # Example using pm2
   pm2 start "python -m uvicorn server:app --host 0.0.0.0 --port 8000" --name ai-sentinel-api
   ```
4. Start the Dashboard (if you want the UI hosted publicly):
   ```bash
   pm2 start "python -m streamlit run ai_sentinel/ui/dashboard.py --server.port 8501" --name ai-sentinel-ui
   ```
5. *(Highly Recommended)* Set up an **Nginx Reverse Proxy** with SSL (Certbot/Let's Encrypt) to route HTTPS traffic `yourdomain.com/api` to port `8000`, and `yourdomain.com` to your Streamlit dashboard on port `8501`.

### 3. Connecting Real Devices
Once your server is running on a public IP/domain, access the dashboard, generate a token, and run the `curl` installer on your real infrastructure servers. They will instantly begin streaming `/var/log/auth.log` over the internet to your Hostinger server!

***

## Quick Start (V1 Legacy Monolith)1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Full Evaluation Pipeline (Generate -> Ingest -> Evaluate -> Alert)**:
   ```bash
   python main.py --pipeline
   ```

3. **Launch the Analyst Dashboard**:
   ```bash
   python main.py --dashboard
   ```
   *The dashboard will be available at `http://localhost:8501`.*

## Architecture Data Flow
1. Raw Logs are generated and written to `logs/generated_auth.log`
2. `log_collector.py` reads and parses via `log_parser.py`, sending unstructured dicts to `database.py` (which writes to `logs.db`).
3. `evaluate_models.py` pulls from DB and orchestrates `feature_extractor.py` to create a `pandas.DataFrame`.
4. Feature matrix splits into Train/Test. The ensemble is trained on chronologically early samples (treating them as baseline).
5. The ensemble predicts on the rest. Anomalies (Score hits) are sent to `AlertManager`.
6. `AlertManager` fetches SHAP rankings, queries the `rule_engine.py` / `attack_classifier.py` for MITRE techniques, and uses `threat_narrative.py` to create the final explanation.
7. Explanations are committed to the `anomalies` table and presented on the Streamlit dashboard.
