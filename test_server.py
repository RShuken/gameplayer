import requests
from PIL import Image
import io

# Test the deployed Qwen2-VL server
SERVER_URL = "http://91.150.160.37:43002"

print("=" * 60)
print("TESTING QWEN2-VL SERVER")
print("=" * 60)
print(f"\nServer: {SERVER_URL}")

# Test health endpoint
print("\n[1/2] Testing health endpoint...")
try:
    response = requests.get(f"{SERVER_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test prediction with a simple test image
print("\n[2/2] Testing prediction endpoint...")
try:
    # Create a simple test image (red square)
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    files = {'image': ('test.png', img_bytes, 'image/png')}
    data = {'instruction': 'describe what you see'}
    
    print("Sending test image...")
    response = requests.post(f"{SERVER_URL}/predict", files=files, data=data, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
