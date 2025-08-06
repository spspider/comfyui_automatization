import requests
import json
import os
import time
from pathlib import Path
import shutil

def run_text2video(prompt, negative_prompt, workflow_path="workflows/text_to_video_wan_api.json"):
    COMFY_URL = "http://127.0.0.1:8188"
    OUTPUT_DIR = Path("ComfyUI/output")
    RESULT_DIR = Path("result")
    RESULT_DIR.mkdir(exist_ok=True)

    # Load API-exported workflow
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Set positive and negative prompts
    if "6" in workflow:
        workflow["6"]["inputs"]["text"] = prompt
    else:
        raise ValueError("Node 6 (positive prompt) not found")
    if "7" in workflow:
        workflow["7"]["inputs"]["text"] = negative_prompt
    else:
        raise ValueError("Node 7 (negative prompt) not found")

    # Replace SaveAnimatedWEBP node with SaveWEBM
    if "28" in workflow:
        workflow["28"]["class_type"] = "SaveWEBM"
        images_link = workflow["28"]["inputs"].get("images")
        workflow["28"]["inputs"] = {
            "images": images_link,
            "filename_prefix": "ComfyUI",
            "codec": "vp9",           # must be either 'vp9' or 'av1'
            "crf": 28,                # common CRF for vp9
            "fps": 24,
            "pix_fmt": "yuv420p"
        }
    else:
        raise ValueError("Node 28 (Save node) not found")

    # Send to ComfyUI API
    response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    if response.status_code != 200:
        raise RuntimeError(f"ComfyUI error: {response.status_code}\n{response.text}")

    prompt_id = response.json()["prompt_id"]
    print(f"✅ Prompt submitted. ID: {prompt_id}")

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
        "a fox moving quickly in a beautiful winter scenery nature trees sunset tracking camera",
        "Overexposure, static, blurred details, subtitles, paintings, pictures, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, mutilated, redundant fingers, poorly painted hands, poorly painted faces, deformed, disfigured, deformed limbs, fused fingers, cluttered background, three legs, a lot of people in the background, upside down"
    )
