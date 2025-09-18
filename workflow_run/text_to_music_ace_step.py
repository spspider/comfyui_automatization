import requests
import json
import os
import time
from pathlib import Path
import shutil
import random
import librosa
import numpy as np
from utilites.utilites import reduce_audio_volume

def is_audio_quality_good(audio_path, threshold_noise=0.3, threshold_silence=0.8):
    """Проверяет качество аудио на наличие шума и тишины"""
    try:
        y, sr = librosa.load(audio_path, duration=10)  # Анализируем первые 10 секунд
        
        # Проверка на преобладание высокочастотного шума
        stft = librosa.stft(y)
        magnitude = np.abs(stft)
        
        # Анализ частотного спектра
        high_freq_energy = np.mean(magnitude[int(len(magnitude)*0.7):])  # Верхние 30% частот
        total_energy = np.mean(magnitude)
        
        noise_ratio = high_freq_energy / (total_energy + 1e-8)
        
        # Проверка на тишину
        rms = librosa.feature.rms(y=y)[0]
        silence_ratio = np.sum(rms < 0.01) / len(rms)
        
        print(f"🔍 Анализ аудио: шум={noise_ratio:.3f}, тишина={silence_ratio:.3f}")
        
        return noise_ratio < threshold_noise and silence_ratio < threshold_silence
    except Exception as e:
        print(f"⚠️ Ошибка анализа аудио: {e}")
        return True  # Если не можем проанализировать, считаем хорошим

def run_text2music(prompt, negative_prompt, duration=30, workflow_path="workflows/ace_step_1_t2m_api.json", output_name="output.mp3", volumelevel=0.1, max_retries=3):
    COMFY_URL = "http://127.0.0.1:8188"
    OUTPUT_DIR = Path("c:/AI/ComfyUI_windows_portable/ComfyUI/output/audio")


    for attempt in range(max_retries):
        print(f"🎵 Попытка генерации музыки {attempt + 1}/{max_retries}")
        
        # Load API-exported workflow
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        
        # Варьируем параметры для лучшего результата
        cfg_values = [6.0, 7.5, 9.0]
        shift_values = [2.5, 3.0, 3.5]
        
        workflow["14"]["inputs"]["tags"] = prompt
        workflow["17"]["inputs"]["seconds"] = duration
        workflow["52"]["inputs"]["cfg"] = cfg_values[attempt % len(cfg_values)]
        workflow["51"]["inputs"]["shift"] = shift_values[attempt % len(shift_values)]
        workflow["52"]["inputs"]["seed"] = random.randint(1, 999999999)
        
        # Усиливаем негативный промпт
        enhanced_negative = "noise, static, glitch, distortion, harsh sounds, electronic noise, digital artifacts, programmatic sounds, beeping, buzzing, mechanical sounds, robot sounds, artificial sounds, synthetic noise"
        workflow["44"]["inputs"]["tags"] = enhanced_negative

        # Send to ComfyUI API
        response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
        if response.status_code != 200:
            print(f"❌ ComfyUI error: {response.status_code}")
            continue

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
            continue
        
        latest = max(files, key=lambda p: p.stat().st_mtime)
        
        # Проверяем качество аудио
        if is_audio_quality_good(latest):
            dest = output_name if isinstance(output_name, Path) else Path(output_name)
            reduce_audio_volume(latest, dest, volume=volumelevel)
            print(f"✅ Качественная музыка сохранена: {dest}")
            return dest
        else:
            print(f"⚠️ Попытка {attempt + 1}: обнаружены машинные звуки, перегенерируем...")
            # Удаляем плохой файл
            latest.unlink()
    
    print("❌ Не удалось сгенерировать качественную музыку за {max_retries} попыток")
    return None


if __name__ == "__main__":
    # Example call
    run_text2music(
        "beautiful piano music",
        ""
    )
