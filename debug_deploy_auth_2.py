import os
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH_ID = os.getenv("TENSORDOCK_AUTH_ID") # User provided
ORG_ID = "d504aff1-6772-4aa3-a868-805f6aa4351f" # From v2 auth test
API_KEY = os.getenv("TENSORDOCK_API_KEY")
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
    # 1. Both api_key and api_token with User Auth ID
    test_payload("UserAuthID + Both Keys", {
        "uuid": AUTH_ID,
        "api_key": API_KEY,
        "api_token": API_KEY,
        "test": "1"
    })

    # 2. Org ID as uuid, with api_key
    test_payload("OrgID + api_key", {
        "uuid": ORG_ID,
        "api_key": API_KEY,
        "test": "1"
    })

    # 3. Org ID as uuid, with api_token
    test_payload("OrgID + api_token", {
        "uuid": ORG_ID,
        "api_token": API_KEY,
        "test": "1"
    })
    
    # 4. Org ID + Both
    test_payload("OrgID + Both", {
        "uuid": ORG_ID,
        "api_key": API_KEY,
        "api_token": API_KEY,
        "test": "1"
    })
