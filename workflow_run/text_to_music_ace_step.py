import requests
import json
import os
import time
from pathlib import Path
import shutil
from utilites.utilites import reduce_audio_volume

def run_text2music(prompt, negative_prompt, duration, workflow_path="workflows/ace_step_1_t2m_api.json", output_name="output.mp3", volumelevel=0.1):
    COMFY_URL = "http://127.0.0.1:8188"
    OUTPUT_DIR = Path("c:/AI/ComfyUI_windows_portable/ComfyUI/output/audio")


    # Load API-exported workflow
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)
        

    workflow["14"]["inputs"]["tags"] = prompt
    workflow["17"]["inputs"]["seconds"] = duration

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

    # Find latest .mp3 output
    files = list(OUTPUT_DIR.glob("ComfyUI*.mp3"))
    if not files:
        print("❌ No .mp3 output found.")
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)

    dest = output_name if isinstance(output_name, Path) else Path(output_name)
    reduce_audio_volume(latest, dest, volume=volumelevel)
    # shutil.copy(latest, dest)
    print(f"✅ Saved output: {dest}")
    return dest


if __name__ == "__main__":
    # Example call
    run_text2music(
        "a fox moving quickly in a beautiful winter scenery nature trees sunset tracking camera",
        "Overexposure, static, blurred details, subtitles, paintings, pictures, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, mutilated, redundant fingers, poorly painted hands, poorly painted faces, deformed, disfigured, deformed limbs, fused fingers, cluttered background, three legs, a lot of people in the background, upside down"
    )
