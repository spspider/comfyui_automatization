import requests
import json
import time
import os
import shutil
from pathlib import Path

COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_FILE = "workflows/image_to_video_wan_480p_api.json"

# --- Настройки ---
positive_prompt = "a beautiful fantasy city at sunrise, cinematic, 4k"
negative_prompt = "low quality, blurry, deformed"
image_path = os.path.abspath("inputs/new_input.png")

# --- Загрузка ---
with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
    workflow_dict = json.load(f)

# --- Модификация узлов ---
if "6" in workflow_dict:
    workflow_dict["6"]["inputs"]["text"] = positive_prompt
else:
    raise ValueError("Node 6 (positive prompt) not found")

if "7" in workflow_dict:
    workflow_dict["7"]["inputs"]["text"] = negative_prompt
else:
    raise ValueError("Node 7 (negative prompt) not found")

if "52" in workflow_dict:
    workflow_dict["52"]["inputs"]["image"] = image_path
else:
    raise ValueError("Node 52 (LoadImage) not found")

# --- Отправка в API ---
response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow_dict})
if response.status_code != 200:
    raise RuntimeError(f"ComfyUI error: {response.text}")

prompt_id = response.json()["prompt_id"]
print(f"✅ Workflow отправлен. Prompt ID: {prompt_id}")

# --- Ожидание завершения ---
print("⌛ Ожидание завершения...")
while True:
    resp = requests.get(f"{COMFY_URL}/history/{prompt_id}")
    if resp.status_code == 200:
        data = resp.json()
        if prompt_id in data and "outputs" in data[prompt_id]:
            print("🎉 Генерация завершена.")
            break
    time.sleep(1)

    
def find_latest_output_file(prefix="ComfyUI", exts=(".webm", ".webp")):
    output_dir = Path("output")
    files = sorted(
        output_dir.glob(f"{prefix}_*.{exts[0][1:]}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return files[0] if files else None

# Найдём последний .webm или .webp файл
latest_file = find_latest_output_file()

if latest_file:
    dest = Path("result") / latest_file.name  # или просто Path(".") — текущая папка
    dest.parent.mkdir(exist_ok=True)
    shutil.copy(latest_file, dest)
    print(f"✅ Скопировано: {latest_file.name} → {dest}")
else:
    print("❌ Не найден сгенерированный файл.")