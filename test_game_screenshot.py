#!/usr/bin/env python3
"""
Test the remote Qwen2-VL server with a real game screenshot.
Usage: python test_game_screenshot.py <path_to_screenshot>
"""

import sys
import cv2
import numpy as np
from model import RemoteVLM

# Server configuration
SERVER_URL = "http://91.150.160.37:43002"

def test_screenshot(image_path: str, instruction: str = "describe what you see in this game scene"):
    """Test the VLM with a game screenshot."""
    
    print("=" * 70)
    print("TESTING QWEN2-VL WITH GAME SCREENSHOT")
    print("=" * 70)
    print(f"\nServer: {SERVER_URL}")
    print(f"Image: {image_path}")
    print(f"Instruction: {instruction}")
    print()
    
    # Load image
    print("[1/3] Loading image...")
    image = cv2.imread(image_path)
    if image is None:
        print(f"ERROR: Could not load image from {image_path}")
        return
    
    print(f"✓ Image loaded: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Initialize remote VLM
    print("\n[2/3] Connecting to remote VLM...")
    vlm = RemoteVLM(server_url=SERVER_URL)
    
    # Get prediction
    print("\n[3/3] Getting prediction from model...")
    print("(This may take 5-10 seconds for the first inference)")
    print()
    
    try:
        action = vlm.predict(image, instruction)
        
        print("=" * 70)
        print("RESULT")
        print("=" * 70)
        print(f"\nModel Response:\n{action}")
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_game_screenshot.py <path_to_screenshot> [instruction]")
        print("\nExample:")
        print("  python test_game_screenshot.py game_screenshot.png")
        print("  python test_game_screenshot.py game_screenshot.png 'what enemies do you see?'")
        sys.exit(1)
    
    image_path = sys.argv[1]
    instruction = sys.argv[2] if len(sys.argv) > 2 else "You are a game-playing AI agent. Describe what you see in this game screenshot and suggest what action to take next."
    
    test_screenshot(image_path, instruction)
