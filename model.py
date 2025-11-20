import numpy as np
from PIL import Image
import sys

# Lazy imports for heavy libraries
torch = None
Qwen2VLForConditionalGeneration = None
AutoProcessor = None
process_vision_info = None

class VLM:
    def __init__(self, model_path="Qwen/Qwen2-VL-7B-Instruct", device="auto", load_in_4bit=False, dummy=False):
        self.dummy = dummy
        if self.dummy:
            print("VLM initialized in DUMMY mode. No model loaded.")
            return

        # Import heavy dependencies only when needed
        global torch, Qwen2VLForConditionalGeneration, AutoProcessor, process_vision_info
        try:
            import torch
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            from qwen_vl_utils import process_vision_info
        except ImportError as e:
            print(f"Error importing model dependencies: {e}")
            print("Please install torch, transformers, and qwen-vl-utils to use the local model.")
            sys.exit(1)

        print(f"Loading model from {model_path}...")
        # Note: 4bit loading requires bitsandbytes which might be tricky on Mac. 
        # We'll stick to default precision or float16 if possible.
        
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device != "cpu" else "auto",
            device_map=device,
            trust_remote_code=True
        )
        
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
        print("Model loaded successfully.")

    def predict(self, image: np.ndarray, instruction: str) -> str:
        if self.dummy:
            return '{"type": "press_key", "key": "w", "duration": 1.0}'

        # Convert numpy (BGR) to PIL (RGB)
        pil_image = Image.fromarray(image[..., ::-1]) # BGR to RGB

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": pil_image,
                    },
                    {"type": "text", "text": instruction},
                ],
            }
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        
        inputs = inputs.to(self.model.device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        
        return output_text[0]

class RemoteVLM:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        print(f"Initialized RemoteVLM connecting to {self.server_url}")

    def predict(self, image: np.ndarray, instruction: str) -> str:
        import requests
        import cv2
        
        # Encode image to bytes
        # Resize if too large to save bandwidth? For now, send full.
        # Actually, let's resize to max 1024px width to be safe on latency
        h, w = image.shape[:2]
        if w > 1024:
            scale = 1024 / w
            image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
            
        success, encoded_img = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("Could not encode image")
            
        files = {
            'image': ('screenshot.jpg', encoded_img.tobytes(), 'image/jpeg')
        }
        data = {
            'instruction': instruction
        }
        
        try:
            response = requests.post(f"{self.server_url}/predict", files=files, data=data, timeout=10)
            response.raise_for_status()
            return response.json().get("action", "")
        except Exception as e:
            print(f"Remote VLM Error: {e}")
            return "wait" # Default safe action

if __name__ == "__main__":
    # Test with dummy
    vlm = VLM(dummy=True)
    print(vlm.predict(np.zeros((100,100,3), dtype=np.uint8), "What do you see?"))
