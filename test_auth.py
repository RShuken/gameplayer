import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TENSORDOCK_API_KEY")
AUTH_ID = os.getenv("TENSORDOCK_AUTH_ID")

def test_auth():
    url = "https://dashboard.tensordock.com/api/v2/auth/test"
    
    # Try using the Key as the Bearer token
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"Testing Auth with Token: {API_KEY[:5]}...")
    
    try:
        response = requests.post(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200 and response.json().get("success"):
            print("SUCCESS: API Key is valid for v2.")
            return True
    except Exception as e:
        print(f"Error: {e}")

    # If that fails, maybe it's the Auth ID? (Unlikely but checking)
    # Or maybe we need to stick to v0 if these are v0 keys.
    return False

if __name__ == "__main__":
    test_auth()
