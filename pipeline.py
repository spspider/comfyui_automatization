
import os
import re
import argparse
import asyncio
import shutil
import subprocess
from pathlib import Path
from moviepy import concatenate_videoclips, VideoFileClip

from provider_all import generate_response_allmy
from text2video_wan2_1 import run_text2video
from video2audio_workflow import run_video2audio
import pprint
from tempfile import NamedTemporaryFile

COMFY_OUTPUT_DIR = Path(r"C:/AI/ComfyUI_windows_portable/ComfyUI/output")
RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

from subtitles import format_time, generate_subtitles, ffmpeg_safe_path, burn_subtitles

async def generate_story(provider="DeepSeek-r1"):
    prompt = (
        "You are a viral video content creator. Generate a mostly trending video scene, which is best of the popular right now, in 2025 complete and structured script for a 1-minute video.\n"
        "Respond using the exact format below for each scene:\n"
        "\n"
        "**[00:00-00:05]**\n"
        "**Title:** Opening Hook\n"
        "**Visual:** Describe the scene. Describe as much detail as possible.\n"
        "**Sound:** Describe the sound or music.\n"
        "**Text:** On-screen text or captions (if any).\n"
        "---\n"
        "Repeat this for each 5-15 second segment of the 1-minute story.\n"
        "Ensure all timestamps are accurate and the output matches this exact format."
    )
    return await generate_response_allmy(provider, prompt)

def parse_story_blocks(story_text):
    pattern = re.compile(
        r"\*\*\[(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\]\*\*\s*"  # timestamps
        r"\*\*Title:\*\*\s*(.*?)\s*"  # title
        r"\*\*Visual:\*\*\s*(.*?)\s*"  # visual
        r"\*\*Sound:\*\*\s*(.*?)\s*"  # sound
        r"\*\*Text:\*\*\s*(.*?)\s*"  # text
        r"---",
        re.DOTALL
    )
    blocks = []
    for match in pattern.findall(story_text):
        start_str, end_str, title, visual, sound, text = match
        def to_sec(t): return int(t.split(":")[0]) * 60 + int(t.split(":")[1])
        duration = to_sec(end_str) - to_sec(start_str)
        blocks.append({
            "title": title.strip(),
            "visual": visual.strip(),
            "sound": sound.strip(),
            "text": text.strip(),
            "duration": duration
        })
    return blocks

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



    
def generate_videos(blocks, negative_prompt="low quality, distorted, static"):
    video_paths = []
    for idx, blk in enumerate(blocks, 1):
        print(f"[Scene {idx}] Generating: {blk['title']}")
        duration = blk.get('duration', 10)
        if not isinstance(duration, int) or duration > 10 or duration <= 0:
            duration = 10
        run_text2video(blk['visual'], negative_prompt, video_seconds=duration)
        clip = fetch_and_prepare_clip()
        if clip:
            video_paths.append(str(clip))
        #    converted = convert_to_mp4(clip)
        #     if converted:
        #         ordered = RESULT_DIR / f"scene_{idx:02d}.mp4"
        #         shutil.move(str(converted), str(ordered))
        #         video_paths.append(str(ordered))
        #     else:
        #         print(f"⚠️ Failed to convert video for scene {idx}")
        # else:
        #     print(f"⚠️ No clip found for scene {idx}")
    return video_paths

def add_audio_to_scenes(video_paths, blocks, negative_prompt="low quality, noise"):
    audio_video_paths = []
    for idx, (video_path, blk) in enumerate(zip(video_paths, blocks), 1):
        print(f"🔊 Adding audio to {video_path}")
        run_video2audio(video_path=video_path, prompt=blk['sound'], negative_prompt=negative_prompt)
        audio_clip = fetch_and_prepare_clip(exts=(".mp4",))
        if audio_clip:
            newname = RESULT_DIR / f"scene_{idx:02d}_audio.mp4"
            shutil.move(str(audio_clip), str(newname))
            audio_video_paths.append(str(newname))
        else:
            print(f"⚠️ No audio clip found for scene {idx}, using original.")
            audio_video_paths.append(video_path)
    return audio_video_paths

def combine_videos(video_list, output_path="final_movie.mp4"):
    if not video_list:
        print("❌ No videos to combine. Exiting.")
        return
    clips = [VideoFileClip(v) for v in video_list]
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, codec="libx264")
    print(f"🎞️ Final movie saved to {output_path}")
    
async def get_story_blocks_with_retries(provider, result_dir, max_attempts=3):
    """Try to generate and parse story blocks, retrying if parsing fails."""
    for attempt in range(max_attempts):
        story = await generate_story(provider=provider)
        print("\n--- Scenario ---\n", story)
        # Save story to result folder as txt
        story_file = result_dir / "story.txt"
        with open(story_file, "w", encoding="utf-8") as f:
            f.write(story)
        blocks = parse_story_blocks(story)
        if blocks:
            return blocks
        print("⚠️ Parsing failed. Retrying with new prompt...")
    print(f"❌ Failed to parse structured output after {max_attempts} attempts.")
    return None

async def main():
    p = argparse.ArgumentParser()
    p.add_argument('--provider', default='DeepSeek-r1')
    p.add_argument('--use_audio', action='store_true')
    args = p.parse_args()

    blocks = await get_story_blocks_with_retries(args.provider, RESULT_DIR)
    # blocks = (parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8")))
    if not blocks:
        return

    print(f"Parsed {len(blocks)} scenes.")
    pprint.pprint(blocks, sort_dicts=False, indent=2)
    vids = generate_videos(blocks)
    vids = burn_subtitles(vids, blocks)   # 2. накладываем субтитры
    vids = add_audio_to_scenes(vids, blocks)
    combine_videos(vids)

if __name__ == '__main__':
    asyncio.run(main())
