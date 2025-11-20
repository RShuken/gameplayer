import os
import requests
import time
import uuid
import subprocess
from dotenv import load_dotenv

load_dotenv()

API_ENDPOINT = "https://dashboard.tensordock.com/api/v2"
API_KEY = os.getenv("TENSORDOCK_API_KEY")
AUTH_ID = os.getenv("TENSORDOCK_AUTH_ID") # Not used in v2 header, but maybe needed? No, v2 uses Bearer.

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

def list_available_hostnodes(gpu_model="RTX 3090"):
    """Lists hostnodes with the specified GPU."""
    print(f"Searching for hostnodes with {gpu_model} (v2)...")
    
    # Map friendly name to v2 slug if possible, or just search generic
    # The docs say "gpu - Filter by GPU type (optional)"
    # Let's try to find the slug from a broad search first if we can, or guess.
    # 3090 slug is likely "geforcertx3090-pcie-24gb" based on 4090 example.
    
    url = f"{API_ENDPOINT}/hostnodes"
    params = {
        "minVcpu": 4,
        "minRamGb": 16,
        # "gpu": "geforcertx3090-pcie-24gb" # Let's try without first to see what we get, or filter client side
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        hostnodes = data.get("data", {}).get("hostnodes", [])
        available = []
        
        print(f"Found {len(hostnodes)} candidate hostnodes. Filtering for {gpu_model}...")
        
        for host in hostnodes:
            resources = host.get("available_resources", {})
            gpus = resources.get("gpus", [])
            
            for gpu in gpus:
                name = gpu.get("v0Name", "").lower() # v0Name seems to be the slug/display name mix?
                # Example: "geforcertx4090-pcie-24gb"
                
                if "3090" in name and gpu.get("availableCount", 0) > 0:
                    price = gpu.get("price_per_hr", 999)
                    print(f"Found {name} on {host['id']} for ${price}/hr")
                    available.append({
                        "host_id": host["id"],
                        "price": price,
                        "location": host.get("location", {}).get("city", "Unknown"),
                        "gpu_slug": gpu.get("v0Name"), # We need this for the deploy payload
                        "gpu_count": gpu.get("availableCount")
                    })
        
        # Sort by price
        available.sort(key=lambda x: x["price"])
        return available

    except Exception as e:
        print(f"List failed: {e}")
        if 'response' in locals():
            print(f"Response: {response.text[:200]}")
        return []

def get_hostnode_ports(host_id):
    """Get available ports from a specific hostnode."""
    url = f"{API_ENDPOINT}/hostnodes/{host_id}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        available_ports = data.get("data", {}).get("available_resources", {}).get("available_ports", [])
        return available_ports
    except Exception as e:
        print(f"Failed to get ports: {e}")
        return []

def deploy_server(host_id, gpu_slug, public_key, use_dedicated_ip=True):
    """Deploys a server using v2 API."""
    print(f"Deploying on host {host_id} with {gpu_slug}...")
    
    url = f"{API_ENDPOINT}/instances"
    
    payload = {
      "data": {
        "type": "virtualmachine",
        "attributes": {
          "name": f"lumine-agent-{str(uuid.uuid4())[:6]}",
          "type": "virtualmachine",
          "image": "ubuntu2204", # Ubuntu 22.04
          "resources": {
            "vcpu_count": 8,
            "ram_gb": 24,
            "storage_gb": 100, # Min 100GB
            "gpus": {
              gpu_slug: {
                "count": 1
              }
            }
          },
          "hostnode_id": host_id,
          "useDedicatedIp": use_dedicated_ip,
          "ssh_key": public_key
        }
      }
    }
    
    # Only add port forwards if not using dedicated IP
    if not use_dedicated_ip:
        # This path won't be used for high-RAM hosts
        pass
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            # Success response: {"data": {"type": "virtualmachine", "id": "...", ...}}
            server_id = data.get("data", {}).get("id")
            if server_id:
                return server_id
        
        print(f"Deployment failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
            
    except Exception as e:
        print(f"Deployment request failed: {e}")
        return None

def get_server_details(server_id):
    url = f"{API_ENDPOINT}/instances/{server_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

if __name__ == "__main__":
    # 1. Setup SSH Key
    key_path, public_key = generate_ssh_key()
    print(f"SSH Key ready: {key_path}")
    
    # 2. Target the Mischii A100 (1500GB RAM per GPU - unlimited!)
    target_host_id = "da3cc8f7-c7e9-4484-b5d5-5f630660c665"
    target_gpu_slug = "a100-sxm4-80gb"
    
    print(f"\nTargeting Mischii A100 (Host: {target_host_id})")
    print("This hostnode supports 1500GB RAM per GPU - no ratio limits!")
    print("Using dedicated IP mode (no port forwarding needed)")
    
    # 3. Deploy with dedicated IP
    print("\nDeploying server...")
    server_id = deploy_server(target_host_id, target_gpu_slug, public_key, use_dedicated_ip=True)
            
    if server_id:
        print(f"\nServer deploying... ID: {server_id}")
        print("Waiting for IP (this may take a minute)...")
        
        # Poll for IP
        for _ in range(30): # Wait up to 300s
            time.sleep(10)
            try:
                details = get_server_details(server_id)
                # v2 details: {"data": {"ipAddress": "...", ...}}
                ip = details.get("data", {}).get("ipAddress")
                status = details.get("data", {}).get("status")
                
                print(f"Status: {status}, IP: {ip}")
                
                if ip and status == "running":
                    print(f"\nSUCCESS! Server Deployed.")
                    print(f"IP Address: {ip}")
                    print(f"SSH Command: ssh -i {key_path} user@{ip}")
                    print(f"API will be available at: http://{ip}:8000")
                    
                    # Save to file
                    with open("server_info.txt", "w") as f:
                        f.write(f"IP={ip}\nSSH_KEY={os.path.abspath(key_path)}\n")
                    break
            except Exception as e:
                print(f"Polling error: {e}")
        else:
            print("Timed out waiting for IP. Check dashboard.")
    else:
        print("\nFailed to deploy on any available hostnode.")
