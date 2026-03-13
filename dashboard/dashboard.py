import streamlit as st
import pandas as pd
import sqlite3
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(
    page_title="AI-Sentinel SIEM Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# SQLite Connection
DB_PATH = Path(__file__).parent.parent / "data" / "logs.db"

@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        logs_df = pd.read_sql_query("SELECT * FROM parsed_logs ORDER BY timestamp DESC LIMIT 5000", conn)
        anomalies_df = pd.read_sql_query("SELECT * FROM anomalies ORDER BY timestamp DESC", conn)
    except Exception as e:
        logs_df = pd.DataFrame()
        anomalies_df = pd.DataFrame()
    conn.close()
    return logs_df, anomalies_df

# UI Header
st.title("🛡️ AI-Sentinel Threat Detection SIEM")
st.markdown("An Open-Source, Explainable Alternative to Enterprise SIEM Anomaly Detection")

if not DB_PATH.exists():
    st.error(f"Database not found at {DB_PATH}. Please run the data generator and evaluator first.")
    st.stop()

# Load Data
logs, anomalies = load_data()

if logs.empty:
    st.warning("No logs found in the database. Ensure the collector has run.")
    st.stop()

# --- Top Key Metrics ---
col1, col2, col3, col4 = st.columns(4)

total_events = len(logs)
total_anomalies = len(anomalies)

if not logs.empty:
    unique_ips = logs['src_ip'].nunique()
else:
    unique_ips = 0
    
col1.metric("Total Ingested Events (Recent)", f"{total_events:,}")
col2.metric("Unique Source IPs", f"{unique_ips:,}")
col3.metric("Detected Anomalies", f"{total_anomalies:,}", delta_color="inverse")
if total_events > 0:
    anomaly_rate = (total_anomalies / total_events) * 100
    col4.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")

st.markdown("---")

# --- Activity Visualization ---
st.subheader("Network Activity Over Time")

if not logs.empty and 'timestamp' in logs.columns:
    logs['timestamp'] = pd.to_datetime(logs['timestamp'])
    
    # Bucket logs into hour/minute bins
    # Depending on the timescale of the generated logs, group by hour usually works
    # We will resample based on count
    time_index_df = logs.set_index('timestamp')
    activity_ts = time_index_df.resample('H').size().reset_index(name='Event Count')
    
    st.line_chart(activity_ts.set_index('timestamp')['Event Count'])

st.markdown("---")

# --- Detected Threats Layout ---
st.subheader("Explainable Alerts (Recent Anomalies)")

if anomalies.empty:
    st.info("No anomalies detected in the database.")
else:
    # Use tabs for different views
    tab1, tab2 = st.tabs(["Active Alerts", "Threat Summary"])
    
    with tab1:
        # Show the most recent 5 anomalies in detail with their narratives
        recent_anomalies = anomalies.head(5)
        for _, alert in recent_anomalies.iterrows():
            with st.expander(f"🔴 [{alert['threat_type']}] Score: {alert['anomaly_score']:.2f} | MITRE: {alert['mitre_technique']}", expanded=True):
                st.write(f"**Generated Narrative:**")
                st.info(alert['narrative'])
                
                # Fetch associated log if possible
                log_row = logs[logs['id'] == alert['log_id']]
                if not log_row.empty:
                    st.write("**Associated Raw Log:**")
                    st.code(log_row.iloc[0]['raw_message'], language="text")

    with tab2:
        # Group by threat type
        st.write("Distribution of Detected Threats")
        threat_counts = anomalies['threat_type'].value_counts()
        st.bar_chart(threat_counts)
        
        # Threat table
        st.write("Full Alert Log")
        st.dataframe(anomalies[['log_id', 'timestamp', 'threat_type', 'mitre_technique', 'anomaly_score']], use_container_width=True)

st.sidebar.header("System Status")
st.sidebar.text("Status: Online 🟢")
st.sidebar.text("Models: Ensemble Loaded")
st.sidebar.text("Explainability: SHAP")

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
