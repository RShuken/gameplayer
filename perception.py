import mss
import numpy as np
import cv2
import time
from typing import Optional, Tuple

class ScreenCapture:
    def __init__(self, monitor_index: int = 1):
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[monitor_index]
        
    def capture(self) -> np.ndarray:
        """
        Captures the screen and returns it as a BGR numpy array (OpenCV format).
        """
        # Grab the data
        sct_img = self.sct.grab(self.monitor)
        
        # Convert to numpy array
        img = np.array(sct_img)
        
        # Convert BGRA to BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        return img

    def save_capture(self, filename: str):
        """Helper to save the current screen to a file."""
        img = self.capture()
        cv2.imwrite(filename, img)
        print(f"Screenshot saved to {filename}")

if __name__ == "__main__":
    # Test the capture
    cap = ScreenCapture()
    start = time.time()
    img = cap.capture()
    end = time.time()
    print(f"Capture shape: {img.shape}")
    print(f"Time taken: {(end - start) * 1000:.2f} ms")
    cap.save_capture("test_capture.jpg")
