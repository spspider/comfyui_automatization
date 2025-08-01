import requests
import json
import os
import time
from pathlib import Path
import shutil

# Настройки
COMFY_URL = "http://localhost:8188"
WORKFLOW_PATH = "workflows/video2video_audio.json1"

# Параметры запуска
video_path = os.path.abspath("inputs/fluffy.mp4")
prompt = "A dreamy anime atmosphere with glowing particles"
negative_prompt = "low quality, blurry, distortion"

# Папки
OUTPUT_DIR = Path("c:/AI/ComfyUI_windows_portable/ComfyUI/output/")
RESULT_DIR = Path("c:/AI/comfyui_automatization/result/")
RESULT_DIR.mkdir(exist_ok=True)

# Загрузка и изменение workflow
with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
    workflow = json.load(f)

workflow["2"]["inputs"]["video"] = video_path
workflow["3"]["inputs"]["prompt"] = prompt
workflow["3"]["inputs"]["negative_prompt"] = negative_prompt

# Отправка в ComfyUI
response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
if response.status_code != 200:
    raise RuntimeError(f"❌ ComfyUI error: {response.status_code}\n{response.text}")

prompt_id = response.json()["prompt_id"]
print(f"✅ Prompt ID: {prompt_id}")

# Ожидание завершения
print("⌛ Ждём завершения...")
while True:
    r = requests.get(f"{COMFY_URL}/history/{prompt_id}")
    if r.status_code == 200:
        data = r.json()
        if prompt_id in data and "outputs" in data[prompt_id]:
            print("🎉 Генерация завершена.")
            break
    time.sleep(1)

# Поиск последних MMaudio файлов
def find_latest_mmaudio_files():
    files = list(OUTPUT_DIR.glob("MMaudio_*.mp4")) + list(OUTPUT_DIR.glob("MMaudio_*.png"))
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files[:3]  # mp4, -audio.mp4, .png

latest_files = find_latest_mmaudio_files()
if latest_files:
    for file in latest_files:
        dest = RESULT_DIR / file.name
        shutil.copy(file, dest)
        print(f"📁 Скопировано: {file.name} → {dest}")
else:
    print("⚠️ Не найдены файлы MMaudio_*")

print("✅ Все готово. Результаты в папке ./result/")
