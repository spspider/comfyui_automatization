from pathlib import Path
import shutil
import subprocess
import sys
import re
sys.path.append(r"C:\AI\Zonos-for-windows\.venv\Lib\site-packages")
import gc
import torch

def clear_vram():
    """Clear VRAM by collecting garbage and emptying CUDA cache."""
    gc.collect()  # Collect Python garbage
    if torch.cuda.is_available():
        torch.cuda.empty_cache()  # Clear CUDA memory cache
        torch.cuda.synchronize()  # Ensure all GPU operations are complete
    print("🧹 VRAM cleared.")

def convert_to_mp4(source_path, duration=3):
    """
    Конвертирует любой WebP/WebM/прочий видеоформат в MP4.
    Для WebP — если анимированный, FFmpeg сам читает все кадры.
    Если статичный — будет один кадр в видео продолжительностью duration.
    """
    dest = Path(source_path).with_suffix(".mp4")
    ffmpeg = r"c:\ProgramData\chocolatey\bin\ffmpeg.exe"
    try:
        # Универсальный вызов для всего: WebP, WebM и пр.
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(source_path),
        ]

        # Если это статичная WebP — зациклить на duration секунд
        if source_path.suffix.lower() == ".webp":
            # попробуем проверить, статичная ли WebP
            with open(source_path, "rb") as f:
                header = f.read(4096)
            if b"ANIM" not in header:
                cmd += ["-loop", "1", "-t", str(duration)]

        cmd += [
            "-vf", "format=yuv420p",
            "-c:v", "libx264",
            str(dest)
        ]
        subprocess.run(cmd, check=True)
        source_path.unlink()
        return dest

    except subprocess.CalledProcessError as e:
        print(f"❌ Не удалось конвертировать {source_path.name} в mp4:\n{e}")
        return None
    
def fetch_and_prepare_clip(exts=(".webm", ".mp4", ".webp")):
    files = []
    for ext in exts:
        files += list(COMFY_OUTPUT_DIR.glob(f"ComfyUI_*{ext}"))
        files += list(COMFY_OUTPUT_DIR.glob(f"wan_*{ext}"))
        files += list(COMFY_OUTPUT_DIR.glob(f"MMaudio_*{ext}"))
    if not files:
        return None
    latest = max(files, key=lambda f: f.stat().st_mtime)
    dest = RESULT_DIR / latest.name
    shutil.copy(latest, dest)
    try:
        os.remove(latest)
    except Exception as e:
        print(f"⚠️ Could not delete source file {latest}: {e}")
    return dest    

def reduce_audio_volume(video_in, video_out, volume=0.7):
        print(f"🔊 Reducing audio volume for {video_in} to {volume * 100}%")
        temp_output = Path(video_out).with_suffix(".temp.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_in),
            "-filter:a", f"volume={volume}",
            "-c:v", "copy",
            str(temp_output)
        ], check=True)
        # Replace original with processed version
        shutil.move(str(temp_output), str(video_out))
        
def sanitize_filename(filename):
    """
    Sanitize a filename by replacing invalid characters and handling edge cases.
    Removes all invalid Windows filename characters, leading/trailing spaces,
    and ensures the filename is not a reserved name.
    """
    filename = str(filename).strip()  # Remove leading/trailing whitespace
    # Replace invalid characters with underscore
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
    # Replace multiple underscores with a single one
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    # If filename is empty or invalid, provide a default
    if not filename or filename in {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}:
        filename = "default_filename"
    # Truncate to avoid Windows path length issues (max 255 chars)
    return filename[:255]        