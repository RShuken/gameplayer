import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TENSORDOCK_API_KEY")
BASE_URL = "https://dashboard.tensordock.com/api/v2"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_endpoint(path, params=None, method="GET", base_url=BASE_URL):
    url = f"{base_url}{path}"
    print(f"Testing {url} with params {params}...")
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, params=params)
        else:
            response = requests.post(url, headers=HEADERS, json=params, data=params) # Try both for v0
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Keys: {list(data.keys())}")
            if "data" in data:
                items = data["data"]
                if isinstance(items, list) and len(items) > 0:
                    print("First Item (List):")
                    print(items[0])
                elif isinstance(items, dict) and len(items) > 0:
                    print("First Item (Dict):")
                    first_key = list(items.keys())[0]
                    print(items[first_key])
            # Check for v0 style response
            if "hostnodes" in data:
                 print("Found hostnodes (v0 style)!")
                 print(list(data["hostnodes"].keys())[0])
        else:
            print(f"Error: {response.text[:100]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Test v2 locations with params
    params = {"gpu_model": "RTX 3090", "min_gpu_count": 1}
    test_endpoint("/locations", params=params)
    
    # Test v0 endpoint on api.tensordock.com
    v0_url = "https://api.tensordock.com/v0"
    v0_payload = {
        "uuid": os.getenv("TENSORDOCK_AUTH_ID"),
        "api_key": os.getenv("TENSORDOCK_API_KEY"),
        "gpu_names": "RTX 3090",
        "min_vram": 24,
        "min_gpu_count": 1
    }
    # Note: v0 uses form-data usually, or json?
    # Let's try POST to v0
    test_endpoint("/client/deploy/hostnodes", params=v0_payload, method="POST", base_url=v0_url)
