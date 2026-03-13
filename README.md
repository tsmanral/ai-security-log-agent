# AI-Sentinel: SIEM Anomaly Detection Platform

"Bridging the Gap: An Open-Source, Explainable Alternative to Enterprise SIEM Anomaly Detection"

## Overview
AI-Sentinel is a lightweight, open-source research platform designed to emulate core SIEM capabilities seen in enterprise tools like Splunk and Microsoft Sentinel. It focuses on the detection of anomalies in SSH authentication logs using an ensemble of Machine Learning models (Isolation Forest, Local Outlier Factor, One-Class SVM).

A key feature of AI-Sentinel is **Explainability**. Instead of just flagging an event as an anomaly, the platform utilizes SHAP (SHapley Additive exPlanations) to interpret model decisions. These interpretations are then passed through a custom heuristic ruling engine to generate human-readable threat narratives and map incidents to MITRE ATT&CK techniques.

## Features
- **Data Generation**: Creates synthetic SSH authentication logs representing normal operations, brute-force attacks, credential stuffing, low-and-slow attacks, and anomalous off-hour accesses.
- **Log Parsing & Storage**: Real-time parsing of syslog formats and persistent storage via SQLite.
- **Feature Engineering**: Extraction of complex temporal (cyclic times) and behavioral (IP diversity, session pacing) features.
- **Ensemble ML Detection**: Combines Local Outlier Factor, One-Class SVM, and Isolation Forest models via a voting ensemble to reduce false positives.
- **Threat Narratives (XAI)**: Generates clear, non-technical explanations for security analysts outlining *why* a particular event was flagged.
- **Interactive Dashboard**: A Streamlit-based UI for monitoring network activity and reviewing generated alerts.

For a deep dive into the system design, view the [Architecture Diagrams](docs/architecture_diagrams.md).

## Project Structure
```text
ai-security-log-agent/
├── agent/
│   ├── database.py             # SQLite configuration and adapters
│   ├── log_collector.py        # Tail/Ingestion mechanisms
│   ├── log_parser.py           # Regex-based SSH log parser
│   ├── alert_manager.py        # Pipeline orchestrator for anomalies
│   ├── detection/              # Classification mappings & Rules
│   ├── explainability/         # SHAP implementation & Natural language gen
│   ├── features/               # Behavioral and Temporal Extractors
│   └── models/                 # Base and implementation ML algorithms
├── dashboard/
│   └── dashboard.py            # Streamlit Dashboard UI
├── data/
│   └── logs.db                 # Generated tracking SQLite DB
├── datasets/
│   └── generate_ssh_logs.py    # Mock anomaly/normal SSH gen
├── evaluation/
│   ├── evaluate_models.py      # Batch processing and system eval script
│   └── plot_results.py         # Visual metric plotters
├── logs/
│   └── generated_auth.log      # Raw synthetic logs output
├── main.py                     # Main execution and pipeline flow
├── README.md                   
└── requirements.txt            
```

## Quick Start
1. **Install Dependencies**:
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
