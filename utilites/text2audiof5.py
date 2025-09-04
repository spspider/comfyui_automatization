import subprocess
import os
import shutil
import torch
import torchaudio
import soundfile as sf
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from speechbrain.inference import EncoderClassifier
from huggingface_hub import hf_hub_download, snapshot_download

# Словарь с путями к языковым пакетам
LANGUAGE_MODELS = {
    "ru": {
        "type": "f5-tts",
        "ckpt_file": r"C:\Users\spspi\.cache\huggingface\hub\models--Misha24-10--F5-TTS_RUSSIAN\snapshots\4f5ee5def0435265fe6ecf2143df2ef26d926b62\F5TTS_v1_Base_accent_tune\model_20000_inference.safetensors",
        "vocab_file": r"C:\Users\spspi\.cache\huggingface\hub\models--Misha24-10--F5-TTS_RUSSIAN\snapshots\4f5ee5def0435265fe6ecf2143df2ef26d926b62\F5TTS_v1_Base\vocab.txt",
        "model": "F5TTS_v1_Base",
        "ref_audio": r"C:\AI\comfyui_automatization\ref_audio\russian_female_1.wav",
        "ref_text": "Серьезно? Не, я не хочу. У меня вообще это... Ну, жутко интересно, Гент, я волосы закорю, конечно. Так, хорошо. А что можно делать этим станком?"
    },
    "en": {
        "type": "f5-tts",
        "ckpt_file": r"C:\Users\spspi\.cache\huggingface\hub\models--SWivid--F5-TTS\snapshots\84e5a410d9cead4de2f847e7c9369a6440bdfaca\F5TTS_v1_Base\model_1250000.safetensors",
        "vocab_file": r"C:\Users\spspi\.cache\huggingface\hub\models--SWivid--F5-TTS\snapshots\84e5a410d9cead4de2f847e7c9369a6440bdfaca\F5TTS_v1_Base\vocab.txt",
        "model": "F5TTS_v1_Base",
        "ref_audio": r"C:\AI\comfyui_automatization\ref_audio\female_en.wav",
        "ref_text": "Victory tastes syrupy! Join uslick the plate, totally worth it. Subscribe now!"
    },
    "ro": {
        "type": "speecht5",
        "model_dir": r"C:\AI\comfyui_automatization\models\SpeechT5_ro",
        "ref_audio": r"C:\AI\comfyui_automatization\ref_audio\female_ro.wav",
        "ref_text": "Engineering mic dejun, pui-stil! Piramida de fier Waffle, echilibru ou-celent!",
        "wav_name": r"C:\AI\comfyui_automatization\ref_audio\female_ro.wav",
        "repo_id": "ionut-visan/SpeechT5_ro"
        
    }
}

# Определение устройства
USE_CUDA = torch.cuda.is_available()
DEVICE = torch.device("cuda" if USE_CUDA else "cpu")

def ensure_model_download(repo_id, local_dir, required_files=None):
    """
    Проверяет наличие модели в local_dir и загружает её, если отсутствует.
    
    Args:
        repo_id (str): Идентификатор репозитория на Hugging Face
        local_dir (str): Локальная папка для хранения модели
        required_files (list, optional): Список необходимых файлов для проверки
    """
    if required_files is None:
        required_files = ["model.safetensors", "config.json"]
    
    # Проверяем наличие всех необходимых файлов
    all_files_present = all(os.path.exists(os.path.join(local_dir, f)) for f in required_files)
    
    if not all_files_present:
        print(f"Downloading {repo_id} to {local_dir}...")
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            allow_patterns=required_files + ["*.wav"]  # Разрешаем также WAV-файлы для ref_audio
        )
        print(f"Downloaded {repo_id} to {local_dir}")
    else:
        print(f"Model {repo_id} already exists in {local_dir}")

def run_f5_tts(language, gen_text, output_file, ref_audio=None, ref_text=None):
    """
    Запускает F5-TTS для генерации речи с указанным языком.
    
    Args:
        language (str): Язык модели ('ru' или 'en')
        gen_text (str): Текст для генерации
        output_file (str): Полный путь к выходному файлу
        ref_audio (str, optional): Путь к референсному аудио
        ref_text (str, optional): Текст референсного аудио
    """
    if language not in LANGUAGE_MODELS:
        raise ValueError(f"Язык {language} не поддерживается. Доступные языки: {list(LANGUAGE_MODELS.keys())}")

    model_info = LANGUAGE_MODELS[language]
    if model_info["type"] != "f5-tts":
        raise ValueError(f"Язык {language} использует SpeechT5, используйте run_speecht5_tts вместо run_f5_tts")

    infer_cli_path = r"C:\AI\F5-TTS\src\f5_tts\infer\infer_cli.py"
    output_dir = os.path.dirname(output_file) or r"C:\AI\comfyui_automatization\result"
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "python", infer_cli_path,
        "--model", model_info["model"],
        "--ckpt_file", model_info["ckpt_file"],
        "--vocab_file", model_info["vocab_file"],
        "--gen_text", gen_text,
        "--output_dir", output_dir,
        "--output_file", os.path.basename(output_file)
    ]
    
    cmd.extend(["--ref_audio", ref_audio if ref_audio else model_info["ref_audio"]])
    cmd.extend(["--ref_text", ref_text if ref_text else model_info["ref_text"]])
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("F5-TTS output:", result.stdout)
        return output_file
    except subprocess.CalledProcessError as e:
        print("Error running F5-TTS:", e.stderr)
        raise

def run_speecht5_tts(language, gen_text, output_file, ref_audio=None, ref_text=None):
    """
    Запускает SpeechT5 для генерации речи на румынском языке.
    
    Args:
        language (str): Язык модели ('ro')
        gen_text (str): Текст для генерации
        output_file (str): Полный путь к выходному файлу
        ref_audio (str, optional): Путь к референсному аудио
        ref_text (str, optional): Текст референсного аудио
    """
    if language not in LANGUAGE_MODELS:
        raise ValueError(f"Язык {language} не поддерживается. Доступные языки: {list(LANGUAGE_MODELS.keys())}")

    model_info = LANGUAGE_MODELS[language]
    if model_info["type"] != "speecht5":
        raise ValueError(f"Язык {language} использует F5-TTS, используйте run_f5_tts вместо run_speecht5_tts")

    # Убедимся, что выходная папка существует
    output_dir = os.path.dirname(output_file) or r"C:\AI\comfyui_automatization\result"
    os.makedirs(output_dir, exist_ok=True)

    # Загружаем модели SpeechT5 и vocoder, если они отсутствуют
    model_dir = model_info.get("model_dir", model_info["repo_id"])
    vocoder_dir = r"C:\AI\comfyui_automatization\models\speecht5_hifigan"
    
    # Автоматическая загрузка SpeechT5_ro
    ensure_model_download(
        repo_id=model_info["repo_id"],
        local_dir=model_dir,
        required_files=["model.safetensors", "config.json", "preprocessor_config.json", "tokenizer_config.json", "spm_char.model"]
    )
    # Автоматическая загрузка speecht5_hifigan
    ensure_model_download(
        repo_id="microsoft/speecht5_hifigan",
        local_dir=vocoder_dir,
        required_files=["pytorch_model.bin", "config.json"]
    )


    # Загружаем референсное аудио
    ref_audio = ref_audio if ref_audio else model_info["ref_audio"]
    ref_text = ref_text if ref_text else model_info["ref_text"]
    
    # Если ref_audio не существует, скачиваем
    if not os.path.exists(ref_audio):
        cached_path = hf_hub_download(repo_id=model_info["repo_id"], filename=model_info["wav_name"])
        ref_audio = os.path.join(model_info["model_dir"], model_info["wav_name"])
        os.makedirs(os.path.dirname(ref_audio), exist_ok=True)
        shutil.copy(cached_path, ref_audio)
    print(f"Voice sample available at: {ref_audio}")
    # Загружаем модели
    print("Loading SpeechT5 models...")
    processor = SpeechT5Processor.from_pretrained(model_info["repo_id"])
    model = SpeechT5ForTextToSpeech.from_pretrained(model_info["repo_id"]).to(DEVICE).eval()
    vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(DEVICE)
    speaker_encoder = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-xvect-voxceleb",
        run_opts={"device": DEVICE},
        savedir="/tmp/speechbrain/spkrec-xvect-voxceleb"
    )


    # Предобработка референсного аудио
    waveform, sr = torchaudio.load(ref_audio)
    if sr != 16000:
        waveform = torchaudio.transforms.Resample(sr, 16000)(waveform)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    waveform = waveform / waveform.abs().max()

    with torch.no_grad():
        speaker_embedding = speaker_encoder.encode_batch(waveform)
        speaker_embedding = torch.nn.functional.normalize(speaker_embedding, dim=2)
        speaker_embedding = speaker_embedding.squeeze(0).squeeze(0).unsqueeze(0)

    # Генерация речи
    inputs = processor(text=gen_text, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        generated_waveform = model.generate_speech(
            input_ids=inputs["input_ids"],
            speaker_embeddings=speaker_embedding.to(DEVICE),
            vocoder=vocoder
        )

    # Сохранение результата
    sf.write(output_file, generated_waveform.cpu().numpy(), 16000, subtype="PCM_16")
    print(f"Speech generated and saved to '{output_file}'")
    return output_file

async def main():
    # Пример для русского
    # output_path = run_f5_tts(
    #     language="ru",
    #     gen_text="Текст для генерации на русском с удар+ениями",
    #     output_file=r"C:\AI\comfyui_automatization\result\output_ru.wav"
    # )
    # print(f"Generated audio saved to: {output_path}")
    
    # # # Пример для английского
    # output_path = run_f5_tts(
    #     language="en",
    #     gen_text="Text for generation in English",
    #     output_file=r"C:\AI\comfyui_automatization\result\output_en.wav"
    # )
    # print(f"Generated audio saved to: {output_path}")

    # Пример для румынского
    output_path = run_speecht5_tts(
        language="ro",
        gen_text="Salut! Acesta este un test generat. ",
        output_file=r"C:\AI\comfyui_automatization\result\output_ro.wav"
    )
    print(f"Generated audio saved to: {output_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())