import io
import base64
import torch
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

app = FastAPI(title="Lumine Agent Brain")

# Global model variables
model = None
processor = None

@app.on_event("startup")
async def load_model():
    global model, processor
    print("Loading Qwen2-VL model... This may take a while.")
    model_path = "Qwen/Qwen2-VL-7B-Instruct"
    
    # Load model - assuming CUDA is available on the cloud GPU
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
    print("Model loaded successfully!")

@app.get("/health")
def health_check():
    return {"status": "ready" if model else "loading"}

@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    instruction: str = Form(...)
):
    if not model:
        return JSONResponse(status_code=503, content={"error": "Model not loaded yet"})

    try:
        # Read image
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Prepare messages
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

        # Inference
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
        
        inputs = inputs.to(model.device)

        generated_ids = model.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        
        return {"action": output_text[0]}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    # Run with: uvicorn server:app --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
