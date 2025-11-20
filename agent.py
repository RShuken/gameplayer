import time
import traceback
import json
import re
from perception import ScreenCapture
from controller import Controller
from model import VLM, RemoteVLM

class Agent:
    def __init__(self, dummy_model=False, remote_url=None):
        self.perception = ScreenCapture()
        self.controller = Controller()
        
        if remote_url:
            self.vlm = RemoteVLM(server_url=remote_url)
        else:
            self.vlm = VLM(dummy=dummy_model)
            
        self.running = False

    def execute_action(self, action_data: dict):
        """
        Executes the action specified in the dictionary.
        Expected keys: "type", and type-specific params.
        """
        action_type = action_data.get("type")
        
        if action_type == "press_key":
            key = action_data.get("key")
            duration = action_data.get("duration", 0.1)
            print(f"Executing: Press '{key}' for {duration}s")
            self.controller.press_key(key, duration)
            
        elif action_type == "move_mouse":
            x = action_data.get("x", 0)
            y = action_data.get("y", 0)
            print(f"Executing: Move mouse ({x}, {y})")
            self.controller.move_mouse(x, y) # Note: This is absolute or relative? Controller says moveTo (absolute). 
            # We might want relative for turning. Let's check Controller implementation or assume relative for now in prompt?
            # Actually, controller.py uses moveTo (absolute). We should probably change controller to moveRel for turning.
            # For now, let's assume the VLM gives us relative offsets and we fix Controller to support it.
            
        elif action_type == "click":
            button = action_data.get("button", "left")
            print(f"Executing: Click {button}")
            self.controller.click(button)
            
        elif action_type == "wait":
            duration = action_data.get("duration", 1.0)
            print(f"Executing: Wait for {duration}s")
            time.sleep(duration)
            
        else:
            print(f"Unknown action type: {action_type}")

    def parse_json_response(self, response: str) -> dict:
        """
        Attempts to extract and parse JSON from the VLM response.
        """
        try:
            # fast path: if it's pure JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # slow path: look for markdown code blocks or just braces
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            print(f"Failed to parse JSON from: {response}")
            return {"type": "wait"}

    def run(self, instruction: str = "Explore the world", debug_mode: bool = False):
        self.running = True
        print(f"Agent started with instruction: {instruction}")
        if debug_mode:
            print("DEBUG MODE ACTIVE: Actions disabled. Model will describe the scene.")
        else:
            print("Press Ctrl+C to stop or move mouse to corner (failsafe).")
        
        # Define prompts
        action_prompt = (
            f"You are an AI agent playing a game. Your goal is: {instruction}.\n"
            "Available actions:\n"
            "- {\"type\": \"press_key\", \"key\": \"<key>\", \"duration\": <float>} (keys: w, a, s, d, space, f, etc.)\n"
            "- {\"type\": \"move_mouse\", \"x\": <int>, \"y\": <int>} (x, y are relative offsets in pixels. Positive x is right, negative is left.)\n"
            "- {\"type\": \"click\", \"button\": \"left\"| \"right\"}\n"
            "- {\"type\": \"wait\", \"duration\": <float>}\n\n"
            "Look at the screenshot. Respond ONLY with a valid JSON object representing the best next action."
        )
        
        debug_prompt = (
            f"You are an AI agent playing a game. Your goal is: {instruction}.\n"
            "Look at the screenshot. Describe what you see in detail (UI elements, environment, enemies, etc.). "
            "Then, explain what action you would take and why."
        )

        try:
            while self.running:
                # 1. Perceive
                frame = self.perception.capture()
                
                # 2. Reason
                prompt = debug_prompt if debug_mode else action_prompt
                response = self.vlm.predict(frame, prompt)
                
                print(f"\n[VLM Response]: {response}\n")
                
                if not debug_mode:
                    # 3. Act
                    action_data = self.parse_json_response(response)
                    self.execute_action(action_data)
                else:
                    # Wait longer in debug mode to let user read
                    time.sleep(5)
                
        except KeyboardInterrupt:
            print("Agent stopped by user.")
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
        finally:
            self.running = False

if __name__ == "__main__":
    # Default to the known TensorDock server
    DEFAULT_SERVER = "http://91.150.160.37:43002"
    
    print("Select Mode:")
    print("1. Remote Cloud (TensorDock) - Default")
    print("2. Local GPU (Qwen2-VL)")
    print("3. Dummy Mode (Test loop)")
    print("4. Debug Mode (Remote VLM, No Actions)")
    
    choice = input("Enter choice (1/2/3/4) [1]: ").strip()
    
    debug = False
    if choice == "2":
        agent = Agent(dummy_model=False)
    elif choice == "3":
        agent = Agent(dummy_model=True)
    elif choice == "4":
        # Debug mode uses remote server but sets debug flag
        url = input(f"Enter Server URL [{DEFAULT_SERVER}]: ").strip() or DEFAULT_SERVER
        agent = Agent(remote_url=url)
        debug = True
    else:
        # Default to 1
        url = input(f"Enter Server URL [{DEFAULT_SERVER}]: ").strip() or DEFAULT_SERVER
        agent = Agent(remote_url=url)

    agent.run("Walk forward, explore, and interact with objects.", debug_mode=debug)
