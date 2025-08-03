# video2audio_workflow.py
import requests
import json
import os
import time
from pathlib import Path
import shutil
copy = False

def run_video2audio(video_path, prompt, negative_prompt, workflow_path="workflows/video2video_audio.json"):
    COMFY_URL = "http://127.0.0.1:8188"
    OUTPUT_DIR = Path("c:/AI/ComfyUI_windows_portable/ComfyUI/output/")
    RESULT_DIR = Path("c:/AI/comfyui_automatization/result/")
    RESULT_DIR.mkdir(exist_ok=True)

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    workflow["2"]["inputs"]["video"] = os.path.abspath(video_path)
    workflow["3"]["inputs"]["prompt"] = prompt
    workflow["3"]["inputs"]["negative_prompt"] = negative_prompt

    response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
    if response.status_code != 200:
        raise RuntimeError(f"ComfyUI error: {response.status_code}\n{response.text}")

    prompt_id = response.json()["prompt_id"]
    print(f"Prompt ID: {prompt_id}")

    while True:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}")
        if r.status_code == 200:
            data = r.json()
            if prompt_id in data and "outputs" in data[prompt_id]:
                break
        time.sleep(1)
    if copy:
        files = list(OUTPUT_DIR.glob("MMaudio_*.mp4")) + list(OUTPUT_DIR.glob("MMaudio_*.png"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        for file in files[:3]:
            dest = RESULT_DIR / file.name
            shutil.copy(file, dest)
            print(f"Скопировано: {file.name} → {dest}")
    else:
        files = list(OUTPUT_DIR.glob("MMaudio_*.mp4"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0] 
    # return RESULT_DIR / files[0].name