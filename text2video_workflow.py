
import requests
import json
import os
import time
from pathlib import Path
import shutil

def run_text2video(prompt, negative_prompt, workflow_path="workflows/text_to_video_wan_api.json"):
    COMFY_URL = "http://127.0.0.1:8188"
    RESULT_DIR = Path("result")
    RESULT_DIR.mkdir(exist_ok=True)

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Set prompts in workflow using correct node numbers and keys
    if "6" in workflow:
        workflow["6"]["inputs"]["text"] = prompt
    else:
        raise ValueError("Node 6 (positive prompt) not found")

    if "7" in workflow:
        workflow["7"]["inputs"]["text"] = negative_prompt
    else:
        raise ValueError("Node 7 (negative prompt) not found")

    response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    if response.status_code != 200:
        raise RuntimeError(f"ComfyUI error: {response.status_code}\n{response.text}")

    prompt_id = response.json()["prompt_id"]
    print(f"Prompt ID: {prompt_id}")

    # Wait for completion
    while True:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}")
        if r.status_code == 200:
            data = r.json()
            if prompt_id in data and "outputs" in data[prompt_id]:
                break
        time.sleep(1)

    # def find_latest_output_file(prefix="ComfyUI", exts=(".webm", ".webp")):
    #     output_dir = Path("output")
    #     files = []
    #     for ext in exts:
    #         files += list(output_dir.glob(f"{prefix}_*.{ext[1:]}"))
    #     files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    #     return files[0] if files else None

    # # Find the latest .webm or .webp file
    # latest_file = find_latest_output_file()

    # if latest_file:
    #     dest = Path("result") / latest_file.name
    #     dest.parent.mkdir(exist_ok=True)
    #     shutil.copy(latest_file, dest)
    #     print(f"✅ Скопировано: {latest_file.name} → {dest}")
    # else:
    #     print("❌ Не найден сгенерированный файл.")
        
if __name__ == "__main__":
    run_text2video("a fox moving quickly in a beautiful winter scenery nature trees sunset tracking camera", "Overexposure, static, blurred details, subtitles, paintings, pictures, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, mutilated, redundant fingers, poorly painted hands, poorly painted faces, deformed, disfigured, deformed limbs, fused fingers, cluttered background, three legs, a lot of people in the background, upside down")
