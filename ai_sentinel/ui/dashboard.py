"""
AI-Sentinel V2 — Streamlit dashboard.

Pages:
    1. 🔑 Login
    2. 🖥️ My Devices — registered devices, last-seen, status
    3. 📊 My Activity — per-user event timeline with anomaly highlights
    4. 🚨 Alerts — anomaly details with 4-layer breakdown
    5. 🔌 Connect My Device — token generation + one-liner
    6. 🛠️ Admin / Testing — synthetic data view (optional toggle)
"""

import html
import uuid
from datetime import datetime

import streamlit as st

from ai_sentinel.onboarding.token_manager import generate_token
from ai_sentinel.storage.database import (
    create_user,
    get_anomalies_for_user,
    get_devices_for_user,
    get_events_for_user,
    get_user_by_username,
    init_db,
)

# ── initialise DB ─────────────────────────────────────────────────────────
init_db()

# ── session state ─────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Login"


# ── sidebar navigation ───────────────────────────────────────────────────

def _sidebar():
    if st.session_state.user:
        st.sidebar.title(f"👤 {st.session_state.user['username']}")
        pages = ["My Devices", "My Activity", "Alerts", "Connect My Device", "Admin / Testing"]
        st.session_state.page = st.sidebar.radio("Navigate", pages)
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()


# ── pages ─────────────────────────────────────────────────────────────────

def page_login():
    st.title("🔐 AI-Sentinel — Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            user = get_user_by_username(username)
            if user and user["password_hash"] == password:  # TODO: use bcrypt
                st.session_state.user = user
                st.session_state.page = "My Devices"
                st.rerun()
            else:
                st.error("Invalid credentials.")
    with col2:
        if st.button("Register"):
            if username and password:
                try:
                    uid = str(uuid.uuid4())
                    create_user(uid, username, password)  # TODO: hash password
                    st.success("Account created! Please log in.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")


def page_devices():
    st.title("🖥️ My Devices")
    user_id = st.session_state.user["id"]
    devices = get_devices_for_user(user_id)

    if not devices:
        st.info("No devices registered. Go to **Connect My Device** to add one!")
        return

    for d in devices:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            col1.markdown(f"**{html.escape(d.get('display_name') or d['hostname'])}**")
            col2.caption(f"OS: {d['os_type']}  |  ID: `{d['id'][:8]}…`")
            last_seen = d.get("last_seen_at", "Never")
            col3.caption(f"Last seen: {last_seen}")
            st.divider()


def page_activity():
    st.title("📊 My Activity")
    user_id = st.session_state.user["id"]
    events = get_events_for_user(user_id, synthetic=False, limit=500)

    if not events:
        st.info("No events received yet.")
        return

    st.dataframe(
        [
            {
                "Time": e["timestamp"],
                "Host": html.escape(e.get("host", "")),
                "User": html.escape(e.get("effective_username", "")),
                "IP": e.get("source_ip", ""),
                "Type": e.get("event_type", ""),
            }
            for e in events
        ],
        use_container_width=True,
    )


def page_alerts():
    st.title("🚨 Alerts")
    user_id = st.session_state.user["id"]
    anomalies = get_anomalies_for_user(user_id, synthetic=False)

    if not anomalies:
        st.success("No anomalies detected 🎉")
        return

    for a in anomalies:
        severity = "🔴" if (a.get("layer2_votes", 0) or 0) >= 2 else "🟡"
        with st.expander(f"{severity} {a.get('threat_type', 'Unknown')} — {a.get('created_at', '')}"):
            st.markdown(a.get("narrative", "No narrative available."))
            col1, col2, col3 = st.columns(3)
            col1.metric("Baseline Z", f"{a.get('layer1_score', 0):.2f}")
            col2.metric("Ensemble", f"{a.get('layer2_score', 0):.2f}")
            col3.metric("AE Error", f"{a.get('layer3_score', 0):.4f}")
            st.caption(f"MITRE: {a.get('mitre_technique', 'N/A')}  |  Device: `{a.get('device_id', '')[:8]}…`")


def page_connect():
    st.title("🔌 Connect My Device")
    user_id = st.session_state.user["id"]

    st.markdown(
        """
        Add a new device to your AI-Sentinel workspace.
        Generate a **one-time registration token** below, then run the
        installer on your target machine.
        """
    )

    if st.button("Generate Token"):
        token = generate_token(user_id)
        st.session_state["last_token"] = token

    if "last_token" in st.session_state:
        token = st.session_state["last_token"]
        st.success(f"Token: `{token}`  *(valid for 15 minutes, single use)*")

        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"
            
        server_address = f"http://{local_ip}:8000"

        st.subheader("Linux")
        st.code(
            f'curl -s {server_address}/static/installer_linux.sh | sudo bash -s -- --token {token} --server {server_address}',
            language="bash",
        )

        st.subheader("Windows (Future)")
        st.info("Download the Windows installer MSI (coming soon) and enter the token during setup.")


def page_admin():
    st.title("🛠️ Admin / Testing")
    user_id = st.session_state.user["id"]

    show_synthetic = st.toggle("Show synthetic data", value=False)
    anomalies = get_anomalies_for_user(user_id, synthetic=show_synthetic)

    st.subheader(f"Anomalies ({'Synthetic' if show_synthetic else 'Real'})")
    if anomalies:
        st.dataframe(
            [
                {
                    "Time": a["created_at"],
                    "Threat": a.get("threat_type", ""),
                    "MITRE": a.get("mitre_technique", ""),
                    "L1 Z": a.get("layer1_score", 0),
                    "L2 Score": a.get("layer2_score", 0),
                    "L3 AE": a.get("layer3_score", 0),
                    "Anomaly": a.get("is_anomaly", False),
                }
                for a in anomalies
            ],
            use_container_width=True,
        )
    else:
        st.info("No data to show.")


# ── main ──────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="AI-Sentinel", page_icon="🛡️", layout="wide")
    _sidebar()

    if not st.session_state.user:
        page_login()
        return

    page_map = {
        "My Devices": page_devices,
        "My Activity": page_activity,
        "Alerts": page_alerts,
        "Connect My Device": page_connect,
        "Admin / Testing": page_admin,
    }
    page_map.get(st.session_state.page, page_devices)()


if __name__ == "__main__":
    main()
