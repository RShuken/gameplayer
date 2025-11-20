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

def deploy_server_hostnode(host_id, gpu_slug, public_key, ssh_port, api_port):
    """Deploy using hostnode-based deployment with port forwarding."""
    print(f"Deploying to hostnode {host_id}...")
    
    url = f"{API_ENDPOINT}/instances"
    
    payload = {
        "data": {
            "type": "virtualmachine",
            "attributes": {
                "type": "virtualmachine",
                "name": "lumine-agent",
                "image": "ubuntu2204",
                "resources": {
                    "vcpu_count": 6,  # Within ratio limits
                    "ram_gb": 15,     # Within ratio limits  
                    "storage_gb": 100,
                    "gpus": {
                        gpu_slug: {
                            "count": 1
                        }
                    }
                },
                "hostnode_id": host_id,
                "useDedicatedIp": False,
                "port_forwards": [
                    {
                        "internal_port": 22,
                        "external_port": ssh_port,
                        "protocol": "tcp"
                    },
                    {
                        "internal_port": 8000,
                        "external_port": api_port,
                        "protocol": "tcp"
                    }
                ],
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
            return None
        
        if response.status_code == 200:
            server_id = data.get("data", {}).get("id")
            if server_id:
                print(f"✓ Deployment initiated successfully!")
                return server_id
        
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
    print("TENSORDOCK DEPLOYMENT - RTX 3090 (Hostnode-Based)")
    print("=" * 60)
    print("\nConfiguration:")
    print("  GPU: RTX 3090 (24GB VRAM)")
    print("  vCPUs: 6 (within ratio limits)")
    print("  RAM: 15GB (within ratio limits)")
    print("  Storage: 100GB")
    print("  Network: Port Forwarding")
    print("  Cost: ~$0.28/hr (~$7/day)")
    print()
    
    # 1. Setup SSH Key
    key_path, public_key = generate_ssh_key()
    print(f"✓ SSH Key ready: {key_path}\n")
    
    # 2. Target a specific RTX 3090 hostnode that we know has ports
    target_host_id = "1d0a2af8-1206-457b-b7b1-ddf2ab0c10eb"  # Rzeszow RTX 3090
    target_gpu_slug = "geforcertx3090-pcie-24gb"
    
    print(f"Targeting hostnode: {target_host_id}")
    
    # Get available ports
    print("Fetching available ports...")
    available_ports = get_hostnode_ports(target_host_id)
    
    if len(available_ports) < 2:
        print(f"ERROR: Not enough ports available. Found: {available_ports}")
        exit(1)
    
    ssh_port = available_ports[0]
    api_port = available_ports[1]
    print(f"✓ Using ports: SSH={ssh_port}, API={api_port}\n")
    
    # 3. Deploy
    server_id = deploy_server_hostnode(target_host_id, target_gpu_slug, public_key, ssh_port, api_port)
    
    if server_id:
        print(f"\n✓ Server ID: {server_id}")
        print("\nWaiting for server to start (this may take 1-2 minutes)...")
        
        # Poll for IP and status
        for attempt in range(30):
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
                    print(f"SSH Port: {ssh_port}")
                    print(f"API Port: {api_port}")
                    print(f"SSH Command: ssh -i {key_path} -p {ssh_port} user@{ip}")
                    print(f"API Endpoint: http://{ip}:{api_port}")
                    
                    # Save to file
                    with open("server_info.txt", "w") as f:
                        f.write(f"SERVER_ID={server_id}\n")
                        f.write(f"IP={ip}\n")
                        f.write(f"SSH_PORT={ssh_port}\n")
                        f.write(f"API_PORT={api_port}\n")
                        f.write(f"SSH_KEY={os.path.abspath(key_path)}\n")
                        f.write(f"SSH_COMMAND=ssh -i {os.path.abspath(key_path)} -p {ssh_port} user@{ip}\n")
                    
                    print(f"\n✓ Server info saved to server_info.txt")
                    break
            except Exception as e:
                print(f"  Polling error: {e}")
        else:
            print("\n⚠ Timed out waiting for server. Check TensorDock dashboard.")
            print(f"   Server ID: {server_id}")
    else:
        print("\n✗ Deployment failed. Please check the error messages above.")
