import time
import traceback
from perception import ScreenCapture
from controller import Controller
from model import VLM, RemoteVLM
import re

class Agent:
    def __init__(self, dummy_model=False, remote_url=None):
        self.perception = ScreenCapture()
        self.controller = Controller()
        
        if remote_url:
            self.vlm = RemoteVLM(server_url=remote_url)
        else:
            self.vlm = VLM(dummy=dummy_model)
            
        self.running = False

    def parse_action(self, response: str):
        """
        Parses the VLM response to determine the action.
        Expected format: "Action: <command>" or just natural language describing the action.
        For this MVP, we'll look for keywords.
        """
        response = response.lower()
        
        if "walk forward" in response or "move forward" in response or "w key" in response:
            print("Action: Walk Forward")
            self.controller.press_key("w", duration=1.0)
        elif "turn left" in response:
            print("Action: Turn Left")
            self.controller.move_mouse(-100, 0)
        elif "turn right" in response:
            print("Action: Turn Right")
            self.controller.move_mouse(100, 0)
        elif "attack" in response or "click" in response:
            print("Action: Attack")
            self.controller.click()
        else:
            print(f"No specific action parsed from: {response}")

    def run(self, instruction: str = "Explore the world"):
        self.running = True
        print(f"Agent started with instruction: {instruction}")
        print("Press Ctrl+C to stop or move mouse to corner (failsafe).")
        
        try:
            while self.running:
                start_time = time.time()
                
                # 1. Perceive
                frame = self.perception.capture()
                
                # 2. Reason
                # We construct a prompt that includes the high-level goal
                prompt = f"You are playing a game. Your goal is: {instruction}. Look at the screenshot. What should you do next? Output the action clearly."
                response = self.vlm.predict(frame, prompt)
                print(f"VLM Thought: {response}")
                
                # 3. Act
                self.parse_action(response)
                
                # Rate limiting (though inference is the real limit)
                # time.sleep(0.1) 
                
        except KeyboardInterrupt:
            print("Agent stopped by user.")
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
        finally:
            self.running = False

if __name__ == "__main__":
    # Mode Selection
    print("Select Mode:")
    print("1. Dummy Mode (Test loop)")
    print("2. Local GPU (Qwen2-VL)")
    print("3. Remote Cloud (TensorDock)")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        agent = Agent(dummy_model=True)
    elif choice == "2":
        agent = Agent(dummy_model=False)
    elif choice == "3":
        url = input("Enter Server URL (e.g., http://123.45.67.89:8000): ").strip()
        agent = Agent(remote_url=url)
    else:
        print("Invalid choice, defaulting to Dummy.")
        agent = Agent(dummy_model=True)

    agent.run("Walk forward and find a chest")
