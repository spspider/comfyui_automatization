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
    """Sanitize a string to be safe for use as a filename."""
    # Keep only alphanumeric characters, underscores, hyphens, and dots
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Remove leading/trailing dots or spaces
    filename = filename.strip('. _')
    # Limit length to avoid issues (e.g., 100 characters)
    filename = filename[:100]
    # Ensure non-empty filename
    return filename or "default_filename" 

import csv

def create_youtube_csv(meta, video_path):
    """
    Create a CSV file with YouTube metadata for bulk upload.
    Compatible with YouTube Studio's CSV format.
    """
    csv_path = Path(video_path).with_name("youtube_metadata.csv")
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["file_name", "title", "description", "tags", "privacy"])
            writer.writerow([
                Path(video_path).name,                     # file_name
                meta.get("video_title", ""),               # title
                meta.get("video_description", ""),         # description
                meta.get("video_hashtags", "").replace(",", "|"),  # tags (YouTube allows | or ,)
                "public"                                   # privacy
            ])
        print(f"✅ YouTube CSV metadata file created: {csv_path}")
        return csv_path
    except Exception as e:
        print(f"❌ Failed to create CSV metadata file: {e}")
        return None
