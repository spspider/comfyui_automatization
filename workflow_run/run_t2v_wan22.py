import requests
import json
import os
import time
from pathlib import Path
import shutil
from datetime import datetime

def run_text2video(prompt, negative_prompt =None, workflow_path="workflows/want2v_2.2_00001_mp4.json", video_seconds=5):
    COMFY_URL = "http://127.0.0.1:8188"
    OUTPUT_DIR = Path("c:/AI/ComfyUI_windows_portable/ComfyUI/output/")
    RESULT_DIR = Path("c:/AI/comfyui_automatization/result/")
    RESULT_DIR.mkdir(exist_ok=True)
    
    FRAME_RATE = 24  # Assuming that the default frame rate is still a valid parameter
    FRAME_COUNT = video_seconds * FRAME_RATE
    # Load API-exported workflow
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)
        
    filename_prefix = workflow["57"]["inputs"].get("filename_prefix", "wan")
    # Set positive and negative prompts
    if "6" in workflow:
        workflow["6"]["inputs"]["text"] = prompt
    else:
        raise ValueError("Node 6 (positive prompt) not found")
    if "89" in workflow:
        workflow["89"]["inputs"]["length"] = FRAME_COUNT  # Assuming 66 frames for 5 seconds at 16 FPS


    # Send to ComfyUI API
    response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    if response.status_code != 200:
        raise RuntimeError(f"ComfyUI error: {response.status_code}\n{response.text}")

    prompt_id = response.json()["prompt_id"]
    print(f"✅ Prompt submitted. ID: {prompt_id}")

    # Wait for completion
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M")
    print(f"⌛ Waiting for completion... [{timestamp}]")
    while True:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}")
        if r.status_code == 200:
            data = r.json()
            if prompt_id in data and "outputs" in data[prompt_id]:
                print("🎉 Generation complete.")
                break
        time.sleep(1)

    # Find latest .webm output
    files = list(OUTPUT_DIR.glob(f"{filename_prefix}_*.mp4"))
    if not files:
        print("❌ No .webm output found.")
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)

    dest = RESULT_DIR / latest.name
    shutil.copy(latest, dest)
    print(f"✅ Saved output: {dest}")
    return dest


if __name__ == "__main__":
    # Example call
    run_text2video(
        "A close-up of a young woman smiling gent ly in the rain, raindrops glistening on her face and eyelashes. The video captures the delicate details of her expression and the water droplets, with soft light reflecting of her skin in the rainy atmosphere."
    )
