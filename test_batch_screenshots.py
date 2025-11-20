#!/usr/bin/env python3
"""
Batch test script for testing multiple game screenshots with RemoteVLM.
Tests all images in testing/screenshots/ and generates a detailed report.
"""

import os
import sys
import base64
from pathlib import Path
from PIL import Image
import requests
from datetime import datetime
import cv2
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model import RemoteVLM

# Configuration
SCREENSHOTS_DIR = "testing/screenshots"
RESULTS_DIR = "testing/results"
SERVER_URL = "http://91.150.160.37:43002"

def setup_directories():
    """Create necessary directories if they don't exist."""
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)

def get_screenshots():
    """Get all image files from screenshots directory."""
    screenshots_path = Path(SCREENSHOTS_DIR)
    if not screenshots_path.exists():
        print(f"❌ Error: Screenshots directory not found: {SCREENSHOTS_DIR}")
        sys.exit(1)

    # Get all common image formats
    extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    screenshots = []
    for ext in extensions:
        screenshots.extend(screenshots_path.glob(f'*{ext}'))
        screenshots.extend(screenshots_path.glob(f'*{ext.upper()}'))

    return sorted(screenshots)

def test_screenshot(model, screenshot_path):
    """Test a single screenshot and return results."""
    print(f"\n{'='*70}")
    print(f"Testing: {screenshot_path.name}")
    print(f"{'='*70}")

    try:
        # Load and display image info
        with Image.open(screenshot_path) as img:
            width, height = img.size
            print(f"📐 Image size: {width}x{height} pixels")
            print(f"📄 Format: {img.format}")
            file_size = screenshot_path.stat().st_size / 1024  # KB
            print(f"💾 File size: {file_size:.1f} KB")

        # Load image as numpy array (BGR format as expected by cv2/RemoteVLM)
        image_array = cv2.imread(str(screenshot_path))
        if image_array is None:
            raise ValueError(f"Failed to load image: {screenshot_path}")

        # Test with model
        instruction = (
            "You are a game-playing AI agent. Analyze this Genshin Impact screenshot "
            "and describe: 1) What you see in the scene, 2) Character/UI information visible, "
            "3) What action or objective seems most appropriate next."
        )

        print(f"\n🤖 Querying model...")
        response = model.predict(image_array, instruction)

        print(f"\n📝 Model Response:")
        print(f"{'-'*70}")
        print(response)
        print(f"{'-'*70}")

        return {
            'success': True,
            'file': screenshot_path.name,
            'size': f"{width}x{height}",
            'file_size_kb': f"{file_size:.1f}",
            'response': response,
            'error': None
        }

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        return {
            'success': False,
            'file': screenshot_path.name,
            'size': None,
            'file_size_kb': None,
            'response': None,
            'error': error_msg
        }

def generate_report(results):
    """Generate a summary report of all tests."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(RESULTS_DIR) / f"test_report_{timestamp}.txt"

    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("BATCH SCREENSHOT TEST REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Server: {SERVER_URL}\n")
        f.write(f"Total tests: {len(results)}\n")

        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {failed}\n")
        f.write("\n")

        # Detailed results
        for i, result in enumerate(results, 1):
            f.write("="*70 + "\n")
            f.write(f"TEST #{i}: {result['file']}\n")
            f.write("="*70 + "\n")

            if result['success']:
                f.write(f"Status: ✓ SUCCESS\n")
                f.write(f"Image size: {result['size']}\n")
                f.write(f"File size: {result['file_size_kb']} KB\n")
                f.write(f"\nModel Response:\n")
                f.write("-"*70 + "\n")
                f.write(result['response'] + "\n")
                f.write("-"*70 + "\n")
            else:
                f.write(f"Status: ✗ FAILED\n")
                f.write(f"Error: {result['error']}\n")

            f.write("\n")

    return report_path

def main():
    """Main test execution."""
    print("="*70)
    print("BATCH SCREENSHOT TESTING WITH QWEN2-VL")
    print("="*70)
    print(f"Server: {SERVER_URL}")
    print(f"Screenshots directory: {SCREENSHOTS_DIR}")
    print()

    # Setup
    setup_directories()

    # Get screenshots
    screenshots = get_screenshots()
    if not screenshots:
        print(f"❌ No screenshots found in {SCREENSHOTS_DIR}")
        sys.exit(1)

    print(f"Found {len(screenshots)} screenshot(s) to test:")
    for i, screenshot in enumerate(screenshots, 1):
        print(f"  {i}. {screenshot.name}")
    print()

    # Initialize model
    print("🔌 Connecting to remote VLM server...")
    model = RemoteVLM(server_url=SERVER_URL)
    print("✓ Connected\n")

    # Test each screenshot
    results = []
    for screenshot in screenshots:
        result = test_screenshot(model, screenshot)
        results.append(result)

    # Generate report
    print(f"\n{'='*70}")
    print("GENERATING REPORT")
    print(f"{'='*70}")

    report_path = generate_report(results)
    print(f"✓ Report saved to: {report_path}")

    # Summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total tests: {len(results)}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
