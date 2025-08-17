import subprocess
import os

# Словарь с путями к языковым пакетам
LANGUAGE_MODELS = {
    "ru": {
        # "ckpt_file": r"C:\Users\spspi\.cache\huggingface\hub\models--Misha24-10--F5-TTS_RUSSIAN\snapshots\4f5ee5def0435265fe6ecf2143df2ef26d926b62\F5TTS_v1_Base\model_240000_inference.safetensors",
        "ckpt_file": r"c:\Users\spspi\.cache\huggingface\hub\models--Misha24-10--F5-TTS_RUSSIAN\snapshots\4f5ee5def0435265fe6ecf2143df2ef26d926b62\F5TTS_v1_Base_accent_tune\model_20000_inference.safetensors",
        "vocab_file": r"C:\Users\spspi\.cache\huggingface\hub\models--Misha24-10--F5-TTS_RUSSIAN\snapshots\4f5ee5def0435265fe6ecf2143df2ef26d926b62\F5TTS_v1_Base\vocab.txt",
        "model": "F5TTS_v1_Base",
        "ref_audio": r"C:\AI\comfyui_automatization\ref_audio\russian_female_1.wav",  # Замени на русский референс
        "ref_text": "Серьезно? Не, я не хочу. У меня вообще это... Ну, жутко интересно, Гент, я волосы закорю, конечно. Так, хорошо. А что можно делать этим станком?"
    },
    "en": {
        "ckpt_file": r"C:\Users\spspi\.cache\huggingface\hub\models--SWivid--F5-TTS\snapshots\84e5a410d9cead4de2f847e7c9369a6440bdfaca\F5TTS_v1_Base\model_1250000.safetensors",
        "vocab_file": r"C:\Users\spspi\.cache\huggingface\hub\models--SWivid--F5-TTS\snapshots\84e5a410d9cead4de2f847e7c9369a6440bdfaca\F5TTS_v1_Base\vocab.txt",
        "model": "F5TTS_v1_Base",
        "ref_audio": r"C:\AI\comfyui_automatization\ref_audio\female_en.wav",
        "ref_text": "Victory tastes syrupy! Join uslick the plate, totally worth it. Subscribe now!"
    }
}

def run_f5_tts(language, gen_text, output_file, ref_audio=None, ref_text=None):
    """
    Запускает F5-TTS для генерации речи с указанным языком.
    
    Args:
        language (str): Язык модели ('ru' или 'en')
        gen_text (str): Текст для генерации
        output_file (str): Имя выходного файла (например, 'output.wav')
        ref_audio (str, optional): Путь к референсному аудио
        ref_text (str, optional): Текст референсного аудио
        output_dir (str, optional): Папка для сохранения результата
    """
    if language not in LANGUAGE_MODELS:
        raise ValueError(f"Язык {language} не поддерживается. Доступные языки: {list(LANGUAGE_MODELS.keys())}")

    model_info = LANGUAGE_MODELS[language]
    infer_cli_path = r"C:\AI\F5-TTS\src\f5_tts\infer\infer_cli.py"
    
    # Базовая команда
    cmd = [
        "python", infer_cli_path,
        "--model", model_info["model"],
        "--ckpt_file", model_info["ckpt_file"],
        "--vocab_file", model_info["vocab_file"],
        "--gen_text", gen_text,
        "--output_file", output_file
    ]
    
    # Добавляем референсное аудио и текст, если указаны
    if ref_audio:
        cmd.extend(["--ref_audio", ref_audio])
    else:
        cmd.extend(["--ref_audio", model_info["ref_audio"]])
    if ref_text:
        cmd.extend(["--ref_text", ref_text])
    else:
        cmd.extend(["--ref_text", model_info["ref_text"]])
    
    # Выполнение команды
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("F5-TTS output:", result.stdout)
        return output_file
    except subprocess.CalledProcessError as e:
        print("Error running F5-TTS:", e.stderr)
        raise

async def main():
    # Пример вызова для русского
    output_path = run_f5_tts(
        language="ru",
        gen_text="Текст для генерации на русском с удар+ениями",
        output_file=r"C:\AI\comfyui_automatization\result\output_ru.wav",
        ref_audio=r"C:\AI\comfyui_automatization\ref_audio\russian_female_1.wav",  # Замени на русский референс
        ref_text="Серьезно? Не, я не хочу. У меня вообще это... Ну, жутко интересно, Гент, я волосы закорю, конечно. Так, хорошо. А что можно делать этим станком?"
    )
    print(f"Generated audio saved to: {output_path}")
    
    # Пример вызова для английского
    output_path = run_f5_tts(
        language="en",
        gen_text="Text for generation in English",
        output_file=r"C:\AI\comfyui_automatization\result\output_en.wav",
        ref_audio=r"C:\AI\comfyui_automatization\ref_audio\female_en.wav",
        ref_text="Victory tastes syrupy! Join uslick the plate, totally worth it. Subscribe now!"
    )
    print(f"Generated audio saved to: {output_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())