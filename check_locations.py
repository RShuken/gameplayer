import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TENSORDOCK_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Get locations to see what's available
response = requests.get("https://dashboard.tensordock.com/api/v2/locations", headers=HEADERS)
data = response.json()

print("=== LOCATION-BASED OPTIONS (Meeting or Exceeding Requirements) ===\n")
print("Minimum Requirements: 24GB VRAM, 24GB RAM, 8 vCPUs, 100GB storage\n")

locations = data.get("data", {}).get("locations", [])

options = []

for loc in locations:
    city = loc.get("city", "Unknown")
    country = loc.get("country", "Unknown")
    
    for gpu in loc.get("gpus", []):
        gpu_name = gpu.get("displayName", "")
        v0_name = gpu.get("v0Name", "")
        
        # Get VRAM from GPU name
        vram = 0
        if "3090" in v0_name or "4090" in v0_name:
            vram = 24
        elif "a100" in v0_name.lower():
            if "80gb" in v0_name.lower():
                vram = 80
            else:
                vram = 40
        elif "h100" in v0_name.lower():
            vram = 80
        
        # Only consider GPUs with >= 24GB VRAM
        if vram >= 24:
            max_vcpus = gpu.get("resources", {}).get("max_vcpus", 0)
            max_ram = gpu.get("resources", {}).get("max_ram_gb", 0)
            max_storage = gpu.get("resources", {}).get("max_storage_gb", 0)
            
            # Check if it can handle our requirements (or better)
            can_handle = max_vcpus >= 8 and max_ram >= 24 and max_storage >= 100
            
            if can_handle:
                gpu_price = gpu.get("price_per_hr", 0)
                vcpu_price = gpu.get("pricing", {}).get("per_vcpu_hr", 0)
                ram_price = gpu.get("pricing", {}).get("per_gb_ram_hr", 0)
                storage_price = gpu.get("pricing", {}).get("per_gb_storage_hr", 0)
                
                # Calculate cost for our config (1 GPU, 8 vCPUs, 24GB RAM, 100GB storage)
                total_cost = gpu_price + (8 * vcpu_price) + (24 * ram_price) + (100 * storage_price)
                
                # Check network features
                network_features = gpu.get("network_features", {})
                dedicated_ip = network_features.get("dedicated_ip_available", False)
                port_forwarding = network_features.get("port_forwarding_available", False)
                
                options.append({
                    "location": f"{city}, {country}",
                    "gpu": gpu_name,
                    "v0_name": v0_name,
                    "vram": vram,
                    "max_vcpus": max_vcpus,
                    "max_ram": max_ram,
                    "max_storage": max_storage,
                    "total_cost": total_cost,
                    "location_id": loc.get("id"),
                    "dedicated_ip": dedicated_ip,
                    "port_forwarding": port_forwarding
                })

# Sort by cost
options.sort(key=lambda x: x["total_cost"])

print(f"Found {len(options)} suitable location-based options:\n")

for i, opt in enumerate(options, 1):
    print(f"{i}. {opt['gpu']} ({opt['vram']}GB VRAM) in {opt['location']}")
    print(f"   Max Resources: {opt['max_vcpus']} vCPUs, {opt['max_ram']}GB RAM, {opt['max_storage']}GB storage")
    print(f"   Cost: ${opt['total_cost']:.3f}/hr (~${opt['total_cost']*24:.2f}/day)")
    print(f"   Network: {'Dedicated IP' if opt['dedicated_ip'] else 'Port Forwarding' if opt['port_forwarding'] else 'Unknown'}")
    print(f"   Location ID: {opt['location_id']}")
    print(f"   GPU Slug: {opt['v0_name']}")
    print()

if len(options) > 0:
    print("\n=== RECOMMENDATION ===")
    best = options[0]
    print(f"Best option: {best['gpu']} in {best['location']}")
    print(f"Cost: ${best['total_cost']:.3f}/hr")
    print(f"This meets all requirements with {best['vram']}GB VRAM")
