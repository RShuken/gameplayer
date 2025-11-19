import pyautogui
import time
import random
from typing import Literal

# Fail-safe: moving mouse to corner will throw exception
pyautogui.FAILSAFE = True

class Controller:
    def __init__(self):
        pass

    def move_mouse(self, x: int, y: int, duration: float = 0.1):
        """Moves mouse to (x, y) over 'duration' seconds."""
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, button: Literal['left', 'right', 'middle'] = 'left'):
        """Clicks the specified mouse button."""
        pyautogui.click(button=button)

    def press_key(self, key: str, duration: float = 0.1):
        """Presses a key for a specific duration."""
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)
        
    def type_text(self, text: str):
        """Types text."""
        pyautogui.write(text)

    def scroll(self, clicks: int):
        """Scrolls the mouse wheel."""
        pyautogui.scroll(clicks)

if __name__ == "__main__":
    # Test controller
    ctrl = Controller()
    print("Testing controller in 3 seconds... Move mouse to corner to abort.")
    time.sleep(3)
    
    current_x, current_y = pyautogui.position()
    print(f"Current position: {current_x}, {current_y}")
    
    # Move slightly
    ctrl.move_mouse(current_x + 50, current_y + 50)
    print("Moved mouse.")
