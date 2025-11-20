import os
import requests
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

API_ENDPOINT = "https://dashboard.tensordock.com/api/v2"
API_KEY = os.getenv("TENSORDOCK_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_ssh_key():
    """Generates an SSH key pair if one doesn't exist."""
    key_path = "tensordock_key"
    if not os.path.exists(key_path):
        print("Generating SSH key pair...")
        subprocess.run(
            ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", key_path, "-N", ""],
            check=True,
            stdout=subprocess.DEVNULL
        )
    
    with open(f"{key_path}.pub", "r") as f:
        public_key = f.read().strip()
        
    return key_path, public_key

def deploy_server(location_id, gpu_slug, public_key):
    """Deploy using location-based deployment (simpler, auto-selects hostnode)."""
    print(f"Deploying to location {location_id}...")
    
    url = f"{API_ENDPOINT}/instances"
    
    payload = {
        "data": {
            "type": "virtualmachine",
            "attributes": {
                "type": "virtualmachine",
                "name": "lumine-agent",
                "image": "ubuntu2204",
                "resources": {
                    "vcpu_count": 8,
                    "ram_gb": 24,
                    "storage_gb": 100,
                    "gpus": {
                        gpu_slug: {
                            "count": 1
                        }
                    }
                },
                "location_id": location_id,
                "useDedicatedIp": True,
                "ssh_key": public_key
            }
        }
    }
    
    try:
        print("Sending deployment request...")
        response = requests.post(url, json=payload, headers=HEADERS)
        
        print(f"Status: {response.status_code}")
        data = response.json()
        
        # Check if there's an error in the response body
        if "error" in data:
            print(f"Deployment failed: {data.get('error')}")
            print(f"Full response: {data}")
            return None
        
        if response.status_code == 200:
            server_id = data.get("data", {}).get("id")
            if server_id:
                print(f"✓ Deployment initiated successfully!")
                return server_id
        
        print(f"Deployment failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
            
    except Exception as e:
        print(f"Deployment request failed: {e}")
        return None

def get_server_details(server_id):
    """Get instance details."""
    url = f"{API_ENDPOINT}/instances/{server_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

if __name__ == "__main__":
    print("=" * 60)
    print("TENSORDOCK DEPLOYMENT - A100 in Mischii, Romania")
    print("=" * 60)
    print("\nConfiguration:")
    print("  GPU: A100 (80GB VRAM)")
    print("  vCPUs: 8")
    print("  RAM: 24GB")
    print("  Storage: 100GB")
    print("  Network: Dedicated IP")
    print("  Cost: ~$0.93/hr (~$22/day)")
    print()
    
    # 1. Setup SSH Key
    key_path, public_key = generate_ssh_key()
    print(f"✓ SSH Key ready: {key_path}\n")
    
    # 2. Deploy to Mischii A100 (has confirmed capacity)
    location_id = "53006e5a-e27d-4630-a325-965adf8b5a0d"
    gpu_slug = "a100-sxm4-80gb"
    
    server_id = deploy_server(location_id, gpu_slug, public_key)
    
    if server_id:
        print(f"\n✓ Server ID: {server_id}")
        print("\nWaiting for server to start (this may take 1-2 minutes)...")
        
        # Poll for IP and status
        for attempt in range(30):  # Wait up to 5 minutes
            time.sleep(10)
            try:
                details = get_server_details(server_id)
                data = details.get("data", {})
                ip = data.get("ipAddress")
                status = data.get("status")
                
                print(f"  [{attempt+1}/30] Status: {status}, IP: {ip or 'pending...'}")
                
                if ip and status == "running":
                    print("\n" + "=" * 60)
                    print("SUCCESS! SERVER DEPLOYED")
                    print("=" * 60)
                    print(f"\nIP Address: {ip}")
                    print(f"SSH Command: ssh -i {key_path} user@{ip}")
                    print(f"API Endpoint: http://{ip}:8000")
                    print(f"\nServer ID: {server_id}")
                    
                    # Save to file
                    with open("server_info.txt", "w") as f:
                        f.write(f"SERVER_ID={server_id}\n")
                        f.write(f"IP={ip}\n")
                        f.write(f"SSH_KEY={os.path.abspath(key_path)}\n")
                        f.write(f"SSH_COMMAND=ssh -i {os.path.abspath(key_path)} user@{ip}\n")
                    
                    print(f"\n✓ Server info saved to server_info.txt")
                    break
            except Exception as e:
                print(f"  Polling error: {e}")
        else:
            print("\n⚠ Timed out waiting for server. Check TensorDock dashboard.")
            print(f"   Server ID: {server_id}")
    else:
        print("\n✗ Deployment failed. Please check the error messages above.")
