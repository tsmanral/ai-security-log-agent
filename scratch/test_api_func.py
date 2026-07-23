import asyncio
from ai_sentinel.ui.api_dashboard import api_events
from ai_sentinel.auth import create_access_token

async def test_api():
    # Simulate demouser context
    user = {
        "user_id": "e42fc102-3673-41c8-834e-00d524827015",
        "username": "demouser",
        "role": "ANALYST"
    }
    
    print("Testing api_events function directly...")
    try:
        events = await api_events(limit=10, user=user)
        print(f"Result: Found {len(events)} events")
        for e in events:
            print(f"  - {e['timestamp']} | {e['event_type']}")
    except Exception as e:
        print(f"API Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_api())
