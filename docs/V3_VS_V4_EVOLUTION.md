# LSADRA V3 vs. V4: Technical & Architectural Evolution

This document details the comprehensive evolution of the LSADRA platform from the V3 prototype to the V4 Enterprise-Grade production baseline.

---

## 1. Technology Stack Evolution

| Category | LSADRA V3 | LSADRA V4 |
| :--- | :--- | :--- |
| **Frontend Framework** | Streamlit (Python-based) | **React 18 + Vite (TypeScript)** |
| **Styling** | Native Streamlit Components | **Tailwind CSS + Lucide Icons** |
| **Backend API** | FastAPI (Basic Endpoints) | **FastAPI (High-Throughput + Async)** |
| **Language** | Python 3.10+ | **Python 3.12 (Backend) + TypeScript (Frontend)** |
| **State Management** | Streamlit Session State | **React Hooks + LocalStorage Persistence** |
| **Communication** | Sync HTTP Requests | **Async REST API + Reactive Polling** |

---

## 2. Architectural Paradigm Shift

### **V3: The "Integrated" Prototype**
- **Architecture**: Semi-monolithic. The UI and Backend were tightly coupled within the Python environment.
- **Data Flow**: Direct function calls between Streamlit components and the detection logic.
- **Limitation**: High latency under heavy log loads and limited UI flexibility for complex data visualizations like relationship graphs.

### **V4: The "Decoupled" Enterprise System**
- **Architecture**: Fully Decoupled Frontend/Backend. A modern Client-Server model.
- **Data Flow**: The React frontend communicates with the FastAPI backend via a well-defined REST API.
- **Improvement**: Sub-100ms UI responsiveness, cross-page state synchronization, and the ability to scale the ingestion engine independently of the analyst dashboard.

---

## 3. Data Ingestion & Normalization

| Feature | LSADRA V3 | LSADRA V4 |
| :--- | :--- | :--- |
| **Source Variety** | Primarily Linux SSH (auth.log) | **Multi-Source (Syslog, Windows, Network, Endpoint)** |
| **Parsing Logic** | Rigid Regex for SSH | **Modular Parser Interface (BaseParser ABC)** |
| **Windows Support** | None (Synthetic only) | **Native Event ID 4624/4625 Parsing** |
| **Network Visibility** | Limited | **NetFlow & iptables Support** |
| **Ingestion API** | `/api/events/batch` | **`/api/events/raw` (Generic string ingestion)** |

---

## 4. Detection & Analysis Capabilities

### **V3 Detection**
- **Ensemble ML**: Relied strictly on Z-Score, Random Forest, and Autoencoder ensemble voting.
- **Narrative**: Simple SHAP-based feature importance lists.
- **Context**: Isolated event analysis.

### **V4 Detection (The "Understanding" Engine)**
- **Hybrid Stack**: Correlates **Deterministic Rules** (Brute Force, LOLBins) with **ML Anomaly Scores**.
- **Behavioral Logic**: Tracks lateral movement patterns and credential stuffing across multiple devices.
- **XAI Narratives**: Generates plain-English case files with MITRE ATT&CK technique mapping and confidence scoring.
- **Feedback Loop**: Integrated False Positive (FP) pattern analysis to dynamically tune thresholds.

---

## 5. Incident Management & Response

| Feature | LSADRA V3 | LSADRA V4 |
| :--- | :--- | :--- |
| **Grouping** | Basic time-window clustering | **Entity-Relation Mapping (IP, User, Host)** |
| **Visualization** | Static DataTables | **Force-Directed Graphs & Interactive Timelines** |
| **Response** | Manual Status Update (Open/Resolved) | **Interactive Remediation Playbooks** |
| **Automation** | None | **Scripted Execution (PowerShell/Bash/CLI)** |
| **Audit Log** | Basic status history | **Phased Remediation Log (Operator actions + results)** |

---

## 6. Key Tooling & Infrastructure Changes

1.  **Vite Build System**: Replaced standard Python execution for the UI, enabling Hot Module Replacement (HMR) and optimized production bundles.
2.  **SQLite Migration Logic**: Shifted from raw `init_db()` to an additive migration sequence (`001`, `002`), ensuring database schema safety during upgrades.
3.  **Modern Icons & UI**: Transitioned from generic text labels to a premium **Lucide-React** icon set and glassmorphic UI elements for a state-of-the-art SOC experience.
4.  **Enhanced Smoke Testing**: Introduced `test_v4_smoke.py`, a comprehensive 27-step validation suite for parsers, rules, and API integrity.

---

## 7. Summary of the V4 "Quantum Leap"

LSADRA V4 transforms the project from a **research prototype** into a **deployable security platform**. The transition to React/TypeScript removes the "Streamlit bottleneck," allowing for the high-density data visualizations and interactive automation tools required by professional SOC analysts.
