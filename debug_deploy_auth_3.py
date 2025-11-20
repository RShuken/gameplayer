import os
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH_ID = os.getenv("TENSORDOCK_AUTH_ID") # 1da9...
ORG_ID = "d504aff1-6772-4aa3-a868-805f6aa4351f"
KEY = os.getenv("TENSORDOCK_API_KEY") # AKbx...
URL = "https://dashboard.tensordock.com/api/v0/client/deploy/single"

def test_payload(name, payload):
    print(f"--- Testing {name} ---")
    try:
        response = requests.post(URL, data=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("\n")

if __name__ == "__main__":
    # 1. uuid=AuthID, api_key=AuthID, api_token=Key
    test_payload("uuid=AuthID, api_key=AuthID, api_token=Key", {
        "uuid": AUTH_ID,
        "api_key": AUTH_ID,
        "api_token": KEY,
        "test": "1"
    })

    # 2. uuid=OrgID, api_key=AuthID, api_token=Key
    test_payload("uuid=OrgID, api_key=AuthID, api_token=Key", {
        "uuid": ORG_ID,
        "api_key": AUTH_ID,
        "api_token": KEY,
        "test": "1"
    })
    
    # 3. uuid=AuthID, api_key=Key, api_token=AuthID
    test_payload("uuid=AuthID, api_key=Key, api_token=AuthID", {
        "uuid": AUTH_ID,
        "api_key": KEY,
        "api_token": AUTH_ID,
        "test": "1"
    })
