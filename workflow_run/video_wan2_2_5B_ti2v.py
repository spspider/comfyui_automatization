import requests
import json
import os
import time
from pathlib import Path
import shutil

def func_video_wan2_2_5B_ti2v(prompt, negative_prompt=None, workflow_path="workflows/video_wan2_2_5B_ti2v.json", video_seconds=5):
    COMFY_URL = "http://127.0.0.1:8188"
    OUTPUT_DIR = Path("c:/AI/ComfyUI_windows_portable/ComfyUI/output/")
    RESULT_DIR = Path("result")
    RESULT_DIR.mkdir(exist_ok=True)


    # Load API-exported workflow
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    frame_rate = workflow["48"]["inputs"].get("fps", 16)
    frame_count = video_seconds * frame_rate

    # Set positive and negative prompts

    workflow["6"]["inputs"]["text"] = prompt
    workflow["55"]["inputs"]["length"] = frame_count

    # Get filename_prefix from save node
    filename_prefix = workflow["58"]["inputs"].get("filename_prefix", "wan")
    # Send to ComfyUI API
    response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    if response.status_code != 200:
        raise RuntimeError(f"ComfyUI error: {response.status_code}\n{response.text}")

    prompt_id = response.json()["prompt_id"]
    # prompt_id = "1234567890"  # Placeholder for prompt ID, replace with actual ID from your workflow
    print(f"✅ Prompt submitted. ID: {prompt_id}")

    # Wait for completion
    # print("⌛ Waiting for completion...")
    while True:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}")
        if r.status_code == 200:
            data = r.json()
            if prompt_id in data and "outputs" in data[prompt_id]:
                print("🎉 Generation complete.")
                break
        time.sleep(1)

    # Find latest .mp4 output (VHS_VideoCombine outputs mp4 with prefix)
    files = list(OUTPUT_DIR.glob(f"{filename_prefix}_*.mp4"))
    if not files:
        print(f"❌ No .mp4 output found with prefix {filename_prefix}.")
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)

    dest = RESULT_DIR / latest.name
    shutil.copy(latest, dest)
    print(f"✅ Saved output: {dest}")
    return dest


if __name__ == "__main__":
    # Example call
    func_video_wan2_2_5B_ti2v(
        "a fox moving quickly in a beautiful winter scenery nature trees sunset tracking camera",
        "Overexposure, static, blurred details, subtitles, paintings, pictures, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, mutilated, redundant fingers, poorly painted hands, poorly painted faces, deformed, disfigured, deformed limbs, fused fingers, cluttered background, three legs, a lot of people in the background, upside down"
    )
