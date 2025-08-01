

import sys
sys.path.append(r"C:\AI\Zonos-for-windows\.venv\Lib\site-packages")
sys.path.append(r"C:\AI\Zonos-for-windows")
import torchaudio

import torch
import torchaudio
from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from zonos.utils import DEFAULT_DEVICE as device

speaker_audio_path=r"C:\AI\Zonos-for-windows\assets\exampleaudio.mp3"

def generate_audio_from_text(text, speaker_audio_path=None, language="en-us", output_path="sample.wav"):
    print("📦 Загрузка модели...")
    model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-transformer", device=device)

    speaker = None
    if speaker_audio_path:
        print(f"👤 Использование голоса из файла: {speaker_audio_path}")
        wav, sampling_rate = torchaudio.load(speaker_audio_path)
        speaker = model.make_speaker_embedding(wav, sampling_rate).to(device)
    else:
        print("⚠️ Нет аудиофайла для клонирования голоса, будет использован дефолтный голос.")

    cond_dict = make_cond_dict(text=text, speaker=speaker, language=language)
    conditioning = model.prepare_conditioning(cond_dict)

    print("🎙️ Генерация аудиокодов...")
    codes = model.generate(conditioning)

    print(f"💾 Сохранение результата в {output_path}...")
    wavs = model.autoencoder.decode(codes).cpu()
    torchaudio.save(output_path, wavs[0], model.autoencoder.sampling_rate)
    print("✅ Готово.")
    
    

if __name__ == "__main__":
    generate_audio_from_text(
        text="Hello world, this is a test of Zonos voice synthesis!",
        speaker_audio_path=None,  # можно None
        language="en-us",
        output_path="output.wav"
    )