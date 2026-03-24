"""
AI-Sentinel V2 — Windows Agent + Server Simulator.

This script makes it easy to test the V2 pipeline locally on Windows.
1. Starts the FastAPI server (`server.py`) in the background.
2. Waits for it to boot.
3. Grabs a user from the DB and generates a registration token.
4. Registers a fake Windows device with the API.
5. Starts the Python agent tailing a `dummy_auth.log` file.
"""

import os
import subprocess
import time
import requests
import sqlite3
import sys

SERVER_URL = "http://127.0.0.1:8000"

print("1. Starting FastAPI Server in the background...")
server_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "server:app"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Give the server 3 seconds to bind to port 8000
time.sleep(3)

print("2. Looking up a user to generate a registration token...")
try:
    from ai_sentinel.storage.database import init_db
    from ai_sentinel.onboarding.token_manager import generate_token
    init_db()

    conn = sqlite3.connect("data/sentinel_v2.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("Error: No users found. Please open the dashboard (streamlit run ai_sentinel/ui/dashboard.py) and create an account first!")
        server_proc.kill()
        exit(1)
    
    user_id = row[0]
    token = generate_token(user_id)
except Exception as e:
    print(f"Failed to generate token from DB: {e}")
    server_proc.kill()
    exit(1)

print("3. Registering 'Test-Windows-VM' with the API...")
try:
    resp = requests.post(f"{SERVER_URL}/api/devices/register", json={
        "token": token,
        "hostname": "Test-Windows-VM",
        "os_type": "windows"
    })
    
    if resp.status_code != 200:
        print(f"API Error ({resp.status_code}): {resp.text}")
        server_proc.kill()
        exit(1)
        
    device_data = resp.json()
except Exception as e:
    print(f"Failed to communicate with API at {SERVER_URL}: {e}")
    server_proc.kill()
    exit(1)

print("4. Creating agent_config.yml and dummy_auth.log...")
config_yaml = f"""server_url: "{SERVER_URL}"
collector_endpoint: "/api/events/batch"
device_id: "{device_data['device_id']}"
api_key: "{device_data['api_key']}"
log_paths:
  - "dummy_auth.log"
batch_size: 1
flush_interval_seconds: 2
"""
with open("agent_config.yml", "w") as f:
    f.write(config_yaml)

with open("dummy_auth.log", "w") as f:
    f.write("Mar 20 20:00:00 Test-PC sshd[123]: Accepted publickey for auth_user from 192.168.1.50 port 5555\\n")

print("5. Starting the endpoint agent! (Press Ctrl+C to stop both Server and Agent)")
print("=" * 70)
print("👉 INSTRUCTIONS:")
print("👉 Open 'dummy_auth.log' in Notepad.")
print("👉 Paste new SSH log lines into the file and save to trigger anomalies!")
print("=" * 70)

try:
    subprocess.run([
        sys.executable, 
        "-m", "ai_sentinel.endpoint_agent.linux_agent", 
        "--config", "agent_config.yml"
    ])
except KeyboardInterrupt:
    pass
finally:
    print("Shutting down API server...")
    server_proc.kill()
