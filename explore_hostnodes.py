import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_ENDPOINT = "https://dashboard.tensordock.com/api/v2"
API_KEY = os.getenv("TENSORDOCK_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def explore_hostnodes():
    """Explore all hostnodes to find ones with good RAM ratios."""
    url = f"{API_ENDPOINT}/hostnodes"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        hostnodes = data.get("data", {}).get("hostnodes", [])
        
        print(f"Found {len(hostnodes)} total hostnodes\n")
        print("=" * 100)
        
        # Look for hostnodes with GPUs and good RAM ratios
        good_options = []
        
        for host in hostnodes:
            resources = host.get("available_resources", {})
            gpus = resources.get("gpus", [])
            max_ram = resources.get("max_ram_per_gpu", 0)
            
            for gpu in gpus:
                if gpu.get("availableCount", 0) > 0:
                    gpu_name = gpu.get("v0Name", "")
                    price = gpu.get("price_per_hr", 0)
                    
                    # Calculate what we can get
                    option = {
                        "host_id": host["id"],
                        "location": host.get("location", {}).get("city", "Unknown"),
                        "gpu_name": gpu_name,
                        "gpu_price": price,
                        "max_ram_per_gpu": max_ram,
                        "available_gpus": gpu.get("availableCount"),
                        "pricing": host.get("pricing", {})
                    }
                    
                    # Filter for RTX 3090/4090 or better
                    if "3090" in gpu_name or "4090" in gpu_name or "a100" in gpu_name.lower():
                        good_options.append(option)
        
        # Sort by max RAM per GPU (descending)
        good_options.sort(key=lambda x: x["max_ram_per_gpu"], reverse=True)
        
        print("\nBest Options (sorted by max RAM per GPU):\n")
        for i, opt in enumerate(good_options[:15], 1):
            print(f"{i}. {opt['gpu_name']} in {opt['location']}")
            print(f"   Max RAM per GPU: {opt['max_ram_per_gpu']}GB")
            print(f"   GPU Price: ${opt['gpu_price']}/hr")
            print(f"   Available: {opt['available_gpus']} GPU(s)")
            
            # Calculate total cost for 1 GPU + 24GB RAM + 4 vCPUs + 100GB storage
            ram_cost = 24 * opt['pricing'].get('per_gb_ram_hr', 0)
            vcpu_cost = 4 * opt['pricing'].get('per_vcpu_hr', 0)
            storage_cost = 100 * opt['pricing'].get('per_gb_storage_hr', 0)
            total_cost = opt['gpu_price'] + ram_cost + vcpu_cost + storage_cost
            
            print(f"   Est. Total Cost (1 GPU + 24GB RAM + 4 vCPUs + 100GB): ${total_cost:.3f}/hr")
            print(f"   Host ID: {opt['host_id']}")
            print()
        
        return good_options
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    explore_hostnodes()
