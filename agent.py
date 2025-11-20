import time
import traceback
import json
import re
from perception import ScreenCapture
from controller import Controller
from model import VLM, RemoteVLM
import os

PERSONAS = {
    "1": {
        "name": "Game Player",
        "instruction": "Walk forward, explore, and interact with objects."
    },
    "2": {
        "name": "Banana Finder",
        "instruction": "Scan the screen for bananas. If you see a banana, use the 'say' action with the exact message: 'BANANA FOUND, DAN LOOK THERE IS A BANNA HERE LOOK DAN LOOK BANANA!'. If you don't see one, use 'move_mouse' to look around or 'wait'."
    },
    "3": {
        "name": "Elderly Assistant",
        "instruction": "You are a helpful, patient computer tutor for an elderly person. Watch what is happening on the screen. If the user seems stuck or needs help, use the 'say' action to gently guide them. If everything is fine, just 'wait'."
    },
    "4": {
        "name": "Custom",
        "instruction": "CUSTOM" # Placeholder
    }
}

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

        elif action_type == "say":
            message = action_data.get("message", "")
            print(f"Agent says: {message}")
            # Use macOS 'say' command for TTS
            os.system(f'say "{message}"')
            
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
            "- {\"type\": \"wait\", \"duration\": <float>}\n"
            "- {\"type\": \"say\", \"message\": \"<text>\"} (Use this to speak to the user, e.g., to report findings or offer help.)\n\n"
            "Look at the screenshot. Respond ONLY with a valid JSON object representing the best next action."
        )
        
        debug_prompt = (
            f"You are an AI agent observing a screen. Your goal is: {instruction}.\\n"
            "Describe what you see in the screenshot. Then explain what you would do next."
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
                    # In debug mode, we still want to allow 'say' actions if they are explicitly returned
                    # But usually debug mode returns natural language. 
                    # However, if the VLM decides to output JSON in debug mode (which it might if instructed), we should handle it.
                    # OR, we can check if the response contains the specific banana phrase and say it manually.
                    
                    # Better approach: Try to parse JSON. If it's a 'say' action, execute it.
                    try:
                        possible_action = self.parse_json_response(response)
                        if possible_action.get("type") == "say":
                            self.execute_action(possible_action)
                    except:
                        pass

                    # Fallback: If the model mentions the specific phrase in text (but not JSON), say it anyway.
                    # This handles the case where the debug prompt causes the model to just describe the action.
                    target_phrase = "BANANA FOUND, DAN LOOK THERE IS A BANNA HERE LOOK DAN LOOK BANANA!"
                    if "BANANA FOUND, DAN LOOK" in response.upper() and target_phrase not in str(possible_action if 'possible_action' in locals() else ""):
                         self.execute_action({"type": "say", "message": target_phrase})
                        
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

    print("\nSelect Persona:")
    for key, p in PERSONAS.items():
        print(f"{key}. {p['name']}")
    
    p_choice = input("Enter choice (1-4) [1]: ").strip() or "1"
    
    if p_choice == "4":
        instruction = input("Enter custom instruction: ").strip()
    else:
        instruction = PERSONAS.get(p_choice, PERSONAS["1"])["instruction"]

    agent.run(instruction, debug_mode=debug)
