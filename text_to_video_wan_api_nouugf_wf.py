import requests
import json
import os
import time
from pathlib import Path
import shutil
copy = False

def text_to_video_wan_api_nouugf(idx, blk, negative_text, workflow_path="workflows/text_to_video_wan_api_nouugf.json", video_seconds=5):
    positive_text = blk['visual']
    COMFY_URL = "http://127.0.0.1:8188"
    OUTPUT_DIR = Path("c:/AI/ComfyUI_windows_portable/ComfyUI/output/")
    RESULT_DIR = Path("result/")
    RESULT_DIR.mkdir(exist_ok=True)

    # Configure workflow using new input names
    FRAME_RATE = 16  # Assuming that the default frame rate is still a valid parameter
    FRAME_COUNT = video_seconds * FRAME_RATE
    
   # Load API-exported workflow
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)
        
    # Configure prompts
   # Set positive and negative text based on node availability
    if "6" in workflow:
        workflow["6"]["inputs"]["text"] = positive_text
    else:
        raise ValueError("Node 6 (CLIP Text Encode for Positive Prompt) not found.")

    if "7" in workflow:
        workflow["7"]["inputs"]["text"] = negative_text
    else:
        raise ValueError("Node 7 (CLIP Text Encode for Negative Prompt) not found.")

    if "40" in workflow:
        workflow["40"]["inputs"]["length"] = FRAME_COUNT
    else:
        raise ValueError("Node 40 (Empty Hunyuan Latent Video) for video length setting not found.")

    # FPS setting falls under different node. For example, it might look something like this:
    if "28" in workflow:
        workflow["28"]["inputs"]["fps"] = FRAME_RATE
    else:
        raise ValueError("Node 28 (SaveAnimatedWEBP) for setting fps not found.")

    # Send to ComfyUI API (corrected endpoint key!)
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    if response.status_code != 200:
        raise RuntimeError(f"ComfyUI error: {response.status_code}\n{response.text}")

    prompt_id = response.json()["prompt_id"]
    print(f"✅ Workflow submitted. ID: {prompt_id}")

    # Wait for completion
    print("⌛ Waiting for completion...")
    while True:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}")
        if r.status_code == 200:
            data = r.json()
            if prompt_id in data and "outputs" in data[prompt_id]:
                print("🎉 Generation complete.")
                break
        time.sleep(1)

    # Find latest .webm output 
    files = list(OUTPUT_DIR.glob("ComfyUI_*.webm"))
    if not files:
        print(f"❌ No .webm output found with prefix 'ComfyUI'.")
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)

    dest = RESULT_DIR / latest.name
    if copy:
        shutil.copy(latest, dest)
        os.remove(latest)
        print(f"✅ Saved output: {dest}")
        return dest
    else:
        return latest


if __name__ == "__main__":
    # Example call
    text_to_video_wan_api_nouugf(
        "a fox moving quickly in a beautiful winter scenery nature trees sunset tracking camera",
        "Overexposure, static, blurred details, subtitles, paintings, pictures, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, mutilated, redundant fingers, poorly painted hands, poorly painted faces, deformed, disfigured, deformed limbs, fused fingers, cluttered background, three legs, a lot of people in the background, upside down"
    )