import sqlite3
import json
from datetime import datetime

def test_diagnostics():
    conn = sqlite3.connect('data/sentinel_v3.db')
    conn.row_factory = sqlite3.Row
    
    # 1. Get demouser ID
    user = conn.execute("SELECT id, username FROM users WHERE username = 'demouser'").fetchone()
    if not user:
        print("Error: demouser not found")
        return
    uid = user['id']
    print(f"Diagnostics for user: {user['username']} ({uid})")
    
    # 2. Check Devices
    devices = conn.execute("SELECT * FROM devices WHERE user_id = ?", (uid,)).fetchall()
    print(f"Found {len(devices)} devices")
    for d in devices:
        print(f"  - Device: {d['id']} | Host: {d['hostname']} | UserID: {d['user_id']}")
        
    # 3. Check Events
    events = conn.execute("SELECT * FROM normalized_events WHERE user_id = ? LIMIT 5", (uid,)).fetchall()
    print(f"Found {len(events)} recent events for user")
    for e in events:
        print(f"  - Event: {e['timestamp']} | Type: {e['event_type']} | Synthetic: {e['is_synthetic']}")

    conn.close()

if __name__ == "__main__":
    test_diagnostics()
