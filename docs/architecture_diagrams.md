# AI-Sentinel Architecture Diagrams

## 1. System Architecture Overview
The overall high-level architecture of the AI-Sentinel platform.

![System Architecture Overview](./images/system_architecture_overview.png)

## 2. Processing Pipeline Flowchart
The chronological data flow of an SSH log through the entire SIEM platform.

```mermaid
graph TD
    A[Raw SSH Logs] --> B[Log Collector]
    B --> C[Log Parser]
    C --> D[(SQLite Database)]
    D --> E[Feature Extractor]
    E --> F[Temporal Features]
    E --> G[Behavioral Features]
    F --> H[ML Ensemble Models]
    G --> H
    H --> I{Anomaly Detected?}
    I -- Yes --> J[SHAP Explainer]
    I -- No --> K[Ignore / Normal]
    J --> L[Rule Engine]
    L --> M[Threat Narrative Generator]
    M --> N[Alert Database]
    N --> O[Analyst Dashboard]
```

## 3. Ingestion Layer Architecture
A zoomed-in view of how un-structured logs are converted and stored continuously.

```mermaid
sequenceDiagram
    participant OS as Operating System
    participant FS as File System
    participant Watchdog as Python Watchdog
    participant Parser as Log Parser (Regex)
    participant DB as SQLite Database
    
    OS->>FS: Append new sshd event
    Watchdog->>FS: Detect file modification
    FS-->>Watchdog: Fetch unread lines
    Watchdog->>Parser: Send raw text line
    Parser->>Parser: Extract timestamp, IP, User, Event Type
    Parser->>DB: INSERT INTO parsed_logs
    DB-->>Watchdog: Commit Success
```

## 4. Machine Learning Detection Layer
The voting ensemble mechanism used for robust anomaly detection.

```mermaid
flowchart LR
    Data[(Feature Matrix)] --> IF[Isolation Forest\nOutliers]
    Data --> LOF[Local Outlier Factor\nNeighborhoods]
    Data --> OCSVM[One-Class SVM\nDecision Boundaries]
    
    IF --> |Vote 0/1| V[Majority Voting Ensemble]
    LOF --> |Vote 0/1| V
    OCSVM --> |Vote 0/1| V
    
    V --> |Count >= 2| Alert[Flag Anomaly]
    V --> |Count < 2| Normal[Mark Normal]
    
    IF -.-> |Raw Score| Avg[Score Average]
    LOF -.-> |Raw Score| Avg
    OCSVM -.-> |Raw Score| Avg
    
    Avg --> FinalScore[Final Anomaly Score]
    FinalScore --> Alert
```

## 5. Explainability and Alerting Layer
How a flagged anomaly is translated into a MITRE ATT&CK technique and human-readable narrative.

```mermaid
graph LR
    A[Flagged Anomaly Row] --> B[SHAP Tree Explainer]
    A --> C[Attack Classifier / Rule Engine]
    
    B --> D[Top 3 Contributing Features\n e.g. 'failures_15m']
    C --> E[MITRE TTP\n e.g. T1110.001]
    
    D --> F[Threat Narrative Generator]
    E --> F
    A --> F
    
    F --> |Natural Language String| G[Alert Manager]
    G --> H[(Anomalies Table)]
```
