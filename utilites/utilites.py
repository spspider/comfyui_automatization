from pathlib import Path
import shutil
import subprocess
import sys
import re
sys.path.append(r"C:\AI\Zonos-for-windows\.venv\Lib\site-packages")
import gc
import torch
import requests
import json

def message_to_me(message):
    """Send notification message via relay server to Telegram"""
    try:
        url = "http://192.168.1.160:1880/message"
        payload = {"message": message}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Notification sent: {message}")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
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
def merge_audio_and_video(blocks, audio_path=None, video_path=None, output_path=None, original_audio_volume=1.0, voice_volume=3.0):
    """
    Merge TTS audio (scene_XX_voice.wav) into the corresponding video (scene_XX_*.mp4).
    If the video is shorter than the audio, loop the necessary part from the end of the video to match the audio duration.
    If the video has no audio, use only TTS. If it has audio, mix it with TTS.
    
    Args:
        blocks: List of blocks (not used in current implementation)
        audio_path: Path to the TTS audio file
        video_path: Path to the input video file
        output_path: Path for the output merged file
        original_audio_volume: Volume level for the original video audio (default: 1.0)
    """
    ffmpeg = r"c:\ProgramData\chocolatey\bin\ffmpeg.exe"
    ffprobe = r"c:\ProgramData\chocolatey\bin\ffprobe.exe"

    # Get durations of video and audio
    def get_duration(file_path):
        cmd = [
            ffprobe, "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(file_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(json.loads(result.stdout)["format"]["duration"])

    video_duration = get_duration(video_path)
    audio_duration = get_duration(audio_path)
    print(f"🎥 Video duration: {video_duration}s, Audio duration: {audio_duration}s")
    
    # Check if the original video has audio
    has_audio = subprocess.run(
        [
            ffprobe, "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    ).stdout.strip() != ""

    temp_video = None
    # If audio is longer than video, create a looped video
    if audio_duration > video_duration:
        print(f"🎥 Audio ({audio_duration}s) is longer than video ({video_duration}s) — looping video.")

        temp_video = Path(output_path).with_suffix(".temp.mp4")
        repeat_count = int(audio_duration // video_duration)
        leftover = audio_duration % video_duration

        if repeat_count >= 2:  
            # Полноценный цикл видео repeat_count раз + остаток
            loop_parts = []
            for _ in range(repeat_count):
                loop_parts.append(f"file '{video_path}'")
            if leftover > 0.05:  # небольшой порог, чтобы избежать пустых обрезков
                loop_parts.append(f"file '{video_path}'\ninpoint {video_duration - leftover}\nduration {leftover}")

            list_file = temp_video.with_suffix(".txt")
            list_file.write_text("\n".join(loop_parts), encoding="utf-8")

            cmd_loop = [
                ffmpeg, "-y",
                "-f", "concat", "-safe", "0", "-i", str(list_file),
                "-c", "copy",
                str(temp_video)
            ]
            try:
                subprocess.run(cmd_loop, check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to loop video {video_path}: {e}")
                return None

            video_path = temp_video

        else:
            # Старое поведение — добавляем хвост
            loop_duration = audio_duration - video_duration
            loop_start = max(0, video_duration - loop_duration)
            if has_audio:
                cmd_loop = [
                    ffmpeg, "-y",
                    "-i", str(video_path),
                    "-filter_complex",
                    f"[0:v]trim=start={loop_start}:duration={loop_duration},setpts=PTS-STARTPTS[vloop];"
                    f"[0:v][vloop]concat=n=2:v=1:a=0[vout];"
                    f"[0:a]atrim=start={loop_start}:duration={loop_duration},asetpts=PTS-STARTPTS[aloop];"
                    f"[0:a][aloop]concat=n=2:v=0:a=1[aout]",
                    "-map", "[vout]", "-map", "[aout]",
                    "-c:v", "libx264", "-c:a", "aac", "-preset", "fast",
                    str(temp_video)
                ]
            else:
                cmd_loop = [
                    ffmpeg, "-y",
                    "-i", str(video_path),
                    "-filter_complex",
                    f"[0:v]trim=start={loop_start}:duration={loop_duration},setpts=PTS-STARTPTS[vloop];"
                    f"[0:v][vloop]concat=n=2:v=1:a=0[vout]",
                    "-map", "[vout]",
                    "-c:v", "libx264", "-preset", "fast",
                    str(temp_video)
                ]
            try:
                subprocess.run(cmd_loop, check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to loop video {video_path}: {e}")
                return None
            video_path = temp_video

    # Merge audio and video
    if has_audio:
        print(f"🎧 Scene has audio — mixing with TTS.")
        cmd = [
            ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex",
            f"[0:a]volume={original_audio_volume}[a0]; [1:a]volume={voice_volume}[a1]; [a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest", str(output_path)
        ]
    else:
        print(f"🔈 Scene has no audio — adding only TTS.")
        cmd = [
            ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest", str(output_path)
        ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to merge TTS with {video_path}: {e}")
        return None

    # Clean up temporary video file if it was created
    if temp_video and temp_video.exists():
        temp_video.unlink()

    return output_path
