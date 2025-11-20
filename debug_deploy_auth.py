import os
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH_ID = os.getenv("TENSORDOCK_AUTH_ID")
API_KEY = os.getenv("TENSORDOCK_API_KEY")
URL = "https://dashboard.tensordock.com/api/v0/client/deploy/single"

def test_payload(name, payload, as_json=False):
    print(f"--- Testing {name} ---")
    try:
        if as_json:
            response = requests.post(URL, json=payload)
        else:
            response = requests.post(URL, data=payload)
            
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("\n")

if __name__ == "__main__":
    # Base payload without deployment details (expecting 400 missing params, not 400 missing api key)
    # If we get "Missing API key", auth failed.
    # If we get "Missing host_id" or similar, auth worked!
    
    # 1. Standard v0 form-data with api_key
    test_payload("Form-data: api_key", {
        "uuid": AUTH_ID,
        "api_key": API_KEY,
        "test": "1"
    })

    # 2. Standard v0 form-data with api_token
    test_payload("Form-data: api_token", {
        "uuid": AUTH_ID,
        "api_token": API_KEY,
        "test": "1"
    })

    # 3. JSON with api_key
    test_payload("JSON: api_key", {
        "uuid": AUTH_ID,
        "api_key": API_KEY,
        "test": "1"
    }, as_json=True)
    
    # 4. JSON with api_token
    test_payload("JSON: api_token", {
        "uuid": AUTH_ID,
        "api_token": API_KEY,
        "test": "1"
    }, as_json=True)
