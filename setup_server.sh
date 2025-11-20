#!/bin/bash
# TensorDock Server Setup for Qwen2-VL-7B-Instruct
# This script installs all dependencies and sets up the model server

set -e  # Exit on error

echo "=========================================="
echo "QWEN2-VL-7B SERVER SETUP"
echo "=========================================="
echo ""

# Update system
echo "[1/8] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "[2/8] Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    build-essential \
    nvidia-cuda-toolkit \
    htop

# Verify NVIDIA GPU
echo "[3/8] Verifying NVIDIA GPU..."
nvidia-smi

# Create project directory
echo "[4/8] Setting up project directory..."
mkdir -p ~/lumine-agent
cd ~/lumine-agent

# Create Python virtual environment
echo "[5/8] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support
echo "[6/8] Installing PyTorch with CUDA 12.1..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Transformers and dependencies
echo "[7/8] Installing Transformers and model dependencies..."
pip install transformers==4.37.0
pip install accelerate==0.25.0
pip install pillow==10.1.0
pip install qwen-vl-utils
pip install tiktoken
pip install einops
pip install transformers_stream_generator
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-multipart==0.0.6

# Create the server script
echo "[8/8] Creating model server script..."
cat > server.py << 'EOF'
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import uvicorn
from PIL import Image
import io
import base64

print("=" * 60)
print("QWEN2-VL-7B MODEL SERVER")
print("=" * 60)

# Initialize FastAPI
app = FastAPI(title="Qwen2-VL Game Agent API")

# Global variables for model and processor
model = None
processor = None
device = None

@app.on_event("startup")
async def load_model():
    """Load the Qwen2-VL model on server startup."""
    global model, processor, device
    
    print("\n[STARTUP] Loading Qwen2-VL-7B-Instruct model...")
    print("This may take a few minutes on first run...\n")
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # Load model
    model_name = "Qwen/Qwen2-VL-7B-Instruct"
    
    print(f"\nLoading model: {model_name}")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    print("Loading processor...")
    processor = AutoProcessor.from_pretrained(model_name)
    
    print("\n✓ Model loaded successfully!")
    print(f"✓ Model parameters: ~7B")
    print(f"✓ Precision: FP16")
    print(f"✓ Ready to process game frames\n")
    print("=" * 60)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "model": "Qwen2-VL-7B-Instruct",
        "device": str(device),
        "ready": model is not None
    }

@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    instruction: str = Form(...)
):
    """
    Process a game screenshot and return the next action.
    
    Args:
        image: Screenshot from the game
        instruction: High-level instruction (e.g., "explore the area", "fight enemies")
    
    Returns:
        JSON with predicted action
    """
    try:
        # Read and process image
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Resize if too large (to save memory)
        max_size = 1024
        if max(pil_image.size) > max_size:
            pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Create prompt for game agent
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": pil_image,
                    },
                    {
                        "type": "text",
                        "text": f"You are a game-playing AI agent. Based on this game screenshot, {instruction}. Respond with a single action command like 'move forward', 'attack', 'jump', 'interact', etc."
                    },
                ],
            }
        ]
        
        # Prepare for inference
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(device)
        
        # Generate response
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False
            )
        
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        output_text = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        return JSONResponse({
            "success": True,
            "action": output_text.strip(),
            "instruction": instruction
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

if __name__ == "__main__":
    print("Starting Qwen2-VL API server...")
    print("Server will be available at http://0.0.0.0:8000")
    print("Endpoints:")
    print("  GET  /           - Health check")
    print("  POST /predict    - Process game frame")
    print("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
EOF

echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "To start the model server:"
echo "  1. Activate the virtual environment:"
echo "     source ~/lumine-agent/venv/bin/activate"
echo ""
echo "  2. Start the server:"
echo "     cd ~/lumine-agent"
echo "     python server.py"
echo ""
echo "The server will listen on port 8000"
echo "First startup will download the model (~14GB)"
echo ""
