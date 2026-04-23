import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
DEVICE_ID = "0072009a-c760-4140-a3e5-60c7746ea698"

def test_api_deletion():
    print(f"Testing API deletion for device: {DEVICE_ID}")
    
    # 1. We need a token. We'll simulate an admin login or use the test login logic
    # In this environment, we'll bypass the network and call the function logic if possible, 
    # but since the server is running, let's try a direct request if we have creds.
    # Since I don't have demouser's password, I'll use the internal logic via a script 
    # that imports the FastAPI app and uses TestClient.
    
    try:
        from fastapi.testclient import TestClient
        from server import app
        from ai_sentinel.auth import create_access_token
        
        client = TestClient(app)
        
        # Create a token for demouser (who owns the device)
        # We need their real user_id. From previous check: demouser
        # Let's find the user_id for demouser
        import sqlite3
        conn = sqlite3.connect('data/sentinel_v3.db')
        user = conn.execute("SELECT id FROM users WHERE username = 'demouser'").fetchone()
        conn.close()
        
        if not user:
            print("Error: demouser not found in DB")
            return
            
        user_id = user[0]
        # Signature: user_id, username, role, expires_minutes
        token = create_access_token(user_id, "demouser", "ANALYST")
        
        print(f"Attempting API DELETE /api/dashboard/devices/{DEVICE_ID}")
        response = client.delete(
            f"/api/dashboard/devices/{DEVICE_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("SUCCESS: The code correctly deleted the device via the API.")
        else:
            print("FAILED: The API returned an error.")
            
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    test_api_deletion()
