import sqlite3
import os

DB_PATH = 'data/sentinel_v3.db'
DEVICE_ID = 'b997415c-9653-4f45-87bf-f4a84d936f76'

def delete_device_manual():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=OFF;") # Temporarily off to avoid order issues, though we'll be thorough
    
    try:
        tables = [
            ('anomalies', 'device_id'),
            ('incidents', 'device_id'),
            ('detection_watermarks', 'device_id'),
            ('device_heartbeats', 'device_id'),
            ('normalized_events', 'device_id'),
            ('metrics_5min', 'device_id'),
            ('devices', 'id')
        ]
        
        print(f"Starting deletion for device: {DEVICE_ID}")
        
        for table, col in tables:
            cur = conn.execute(f"DELETE FROM {table} WHERE {col} = ?", (DEVICE_ID,))
            print(f"Deleted {cur.rowcount} rows from {table}")
            
        conn.commit()
        print("Successfully deleted device and all related data.")
        
    except Exception as e:
        print(f"Error during deletion: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    delete_device_manual()
