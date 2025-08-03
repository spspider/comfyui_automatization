
import gc
import os
import re
import argparse
import asyncio
import shutil
import subprocess
from pathlib import Path
from moviepy import concatenate_videoclips, VideoFileClip
from utilites.text2audioZonos import generate_audio_from_text

from provider_all import generate_response_allmy
from text_to_video_wan_api_nouugf_wf import text_to_video_wan_api_nouugf
from video2audio_workflow import run_video2audio
from wan_2_1_t2v_gguf_api import wan_2_1_t2v_gguf_api

COMFY_OUTPUT_DIR = Path(r"C:/AI/ComfyUI_windows_portable/ComfyUI/output")
RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEBUG = 'audio'

from subtitles import format_time, generate_subtitles, ffmpeg_safe_path, burn_subtitles

async def generate_story(provider="qwen"):
    prompt = (
        "You are a viral video content creator. Generate a mostly trending video scene, which is best of the popular right now, in 2025 complete and structured script for a 1-minute video.\n"
        "Start with a short title, a short YouTube-ready description, and relevant hashtags.\n"
        "Respond using the exact format below for each scene:\n"
        "\n"
        "**VIDEO_Title:** The Coffee Cup That Stole the Internet**\n"
        "**VIDEO_Description:** A hilarious story about a mischievous coffee cup causing chaos in the office.\n"
        "**VIDEO_Hashtags:** #Comedy #CoffeeChaos #OfficeLife\n"
        "\n"
        "**[00:00-00:05]**\n"
        "**Title:** Opening Hook\n"
        "**Visual:** Describe the scene. Describe as much detail as possible. at least 5-10 sentences including background and foreground.\n"
        "**Sound:** Describe the sound or music.\n"
        "**Text:** On-screen text or captions (if any).\n"
        "---\n"
        "Repeat this for each 5-10 second segment of the 30 seconds story.\n"
        "Ensure all timestamps are accurate and the output matches this exact format."
    )
    return await generate_response_allmy(provider, prompt)

def parse_story_blocks(story_text):
    meta = {}
    meta_match = re.search(
        r'\*\*VIDEO_Title:\*\*\s*(.*?)\s*\*\*VIDEO_Description:\*\*\s*(.*?)\s*\*{2}VIDEO_Hashtags:\*\*\s*(.*?)\s*',
        story_text,
        re.DOTALL
    )
    if meta_match:
        meta = {
            "video_title": meta_match.group(1).strip(),
            "video_description": meta_match.group(2).strip(),
            "video_hashtags": meta_match.group(3).strip()
        }

    pattern = re.compile(
        r'\*\*\[(\d{2}:\d{2})-(\d{2}:\d{2})\]\*\*\s*'
        r'\*\*Title:\*\*\s*(.*?)\s*'
        r'\*\*Visual:\*\*\s*(.*?)\s*'
        r'\*\*Sound:\*\*\s*(.*?)\s*'
        r'\*\*Text:\*\*\s*(.*?)(?=\n\*\*\[\d{2}:\d{2}-\d{2}:\d{2}\]\*\*|\Z)',
        re.DOTALL
    )

    scenes = []
    for match in pattern.findall(story_text):
        start_str, end_str, title, visual, sound, text = match
        def to_sec(t): 
            minutes, seconds = map(int, t.split(":"))
            return minutes * 60 + seconds
        duration = to_sec(end_str) - to_sec(start_str)
        scenes.append({
            "title": title.strip(),
            "visual": visual.strip(),
            "sound": sound.strip(),
            "text": text.strip(),
            "duration": duration
        })

    return meta, scenes


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

def update_blocks_with_real_duration(blocks):
    """
    Update the 'duration' becouse actual duration is differ from the one in blocks
    """
    for idx, blk in enumerate(blocks, 1):
        video_path = RESULT_DIR / f"scene_{idx:02d}.webm"
        if video_path.exists():
            try:
                # Open the video and get its duration
                clip = VideoFileClip(str(video_path))
                blk['duration'] = clip.duration
                # Close the video to free up resources
                clip.close()
            except Exception as e:
                print(f"⚠️ Could not get duration for {video_path}: {e}")
    return blocks

    
def generate_videos(blocks, negative_prompt="low quality, distorted, static"):
    video_paths = []
    for idx, blk in enumerate(blocks, 1):
        print(f"[Scene {idx}] Generating: {blk['title']}")
        duration = blk.get('duration', 10)
        if not isinstance(duration, int) or duration > 10 or duration <= 0:
            duration = 10
        # clip = wan_2_1_t2v_gguf_api(blk['visual'], negative_prompt, video_seconds=duration)
        
        clip = text_to_video_wan_api_nouugf(idx, blk, negative_prompt, video_seconds=duration)
        if clip:
            new_name = RESULT_DIR / f"scene_{idx:02d}_video.webm"  # Format index as 2-digit number
            shutil.move(Path(clip), str(new_name))  # Rename the file
            shutil.remove(clip)  # Remove the original file
            video_paths.append(str(new_name))  # Add the new path to the list
        else:
            print(f"⚠️ No clip found for scene {idx}")
    return video_paths

def add_audio_to_scenes(video_paths, blocks, negative_prompt="low quality, noise"):
    audio_video_paths = []
    for idx, (video_path, blk) in enumerate(zip(video_paths, blocks), 1):
        print(f"🔊 Adding audio to {video_path}")
        audio_clip = run_video2audio(video_path=video_path, prompt=blk['sound'], negative_prompt=negative_prompt)
        # audio_clip = fetch_and_prepare_clip(exts=(".mp4",))
        if audio_clip:
            newname = RESULT_DIR / f"scene_{idx:02d}_audio.mp4"
            shutil.move(Path(audio_clip), str(newname))
            shutil.remove(audio_clip)
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
        meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
        print(f"🎬 Title: {meta['video_title']}")
        print(f"📝 Description: {meta['video_description']}")
        print(f"🏷️ Hashtags: {meta['video_hashtags']}")
        if blocks:
            return blocks
        print("⚠️ Parsing failed. Retrying with new prompt...")
    print(f"❌ Failed to parse structured output after {max_attempts} attempts.")
    return None

def clean_comfy_output():
    """Remove all files from ComfyUI output directory"""
    for file in COMFY_OUTPUT_DIR.glob("*"):
        try:
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)
        except Exception as e:
            print(f"⚠️ Could not delete {file}: {e}") 
            
def burn_tts_to_video(video_paths, blocks):
    """
    Merge TTS audio (scene_XX_voice.wav) into the corresponding video (scene_XX_*.mp4).
    Returns a list of updated video paths.
    """
    updated_videos = []
    ffmpeg = r"c:\ProgramData\chocolatey\bin\ffmpeg.exe"

    for idx, video_path in enumerate(video_paths, 1):
        video_path = Path(video_path)
        tts_audio = RESULT_DIR / f"scene_{idx:02d}_voice.wav"
        if not tts_audio.exists():
            print(f"⚠️ TTS audio not found for scene {idx}: {tts_audio}")
            updated_videos.append(str(video_path))
            continue

        output_path = RESULT_DIR / f"scene_{idx:02d}_tts_berned.mp4"
        cmd = [
            ffmpeg, "-y",
            "-i", Path(video_path),
            "-i", Path(tts_audio),
            "-filter_complex",
            "[0:a]volume=0.6[a0]; [1:a]volume=1.0[a1]; [a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            str(output_path)
        ]
        try:
            subprocess.run(cmd, check=True)
            updated_videos.append(str(output_path))
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to merge TTS with {video_path.name}: {e}")
            updated_videos.append(str(video_path))
        # finally:
        #     # Clean up the original video file if needed
        #     if video_path.exists():
        #         try:
        #             video_path.unlink()
        #         except Exception as e:
        #             print(f"⚠️ Could not delete original video {video_path}: {e}")
    return updated_videos

def list_files_in_result(pattern, result_dir=None):
    result_dir = Path(r"C:/AI/comfyui_automatization/"+result_dir)
    return sorted([file for file in result_dir.glob(pattern) if file.is_file()])    

async def main():
    clean_comfy_output()   
    if DEBUG:
        print("DEBUG mode: skip requesting new blocks.")
        meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
    else:
        meta, blocks = await get_story_blocks_with_retries(args.provider, RESULT_DIR)
    print(f"🎬 Title: {meta['video_title']}")
    print(f"📝 Description: {meta['video_description']}")
    print(f"🏷️ Hashtags: {meta['video_hashtags']}")
    if not blocks:
        return

    # for idx, blk in enumerate(blocks, 1):
    #     print(f"[Scene {idx}]")
    #     print(f"  Title: {blk.get('title')}")
    #     print(f"  Visual: {blk.get('visual')}")
    #     print(f"  Sound: {blk.get('sound')}")
    #     print(f"  Text: {blk.get('text')}")
    #     print("-" * 40)
        
    print(f"Parsed {len(blocks)} scenes.")
    if DEBUG:
        print("DEBUG mode: skip creating videos.")
        vids = list_files_in_result("scene_*_video.webm","result") 
        # for vid in vids:
        #     print(vid)
        # for idx, blk in enumerate(blocks, 1):
        #     generate_audio_from_text(blk["text"], output_path=f"result/scene_{idx:02d}_voice.wav")
        # vids = add_audio_to_scenes(vids, blocks)
        # burn_tts_to_video(vids, blocks)  # 3. накладываем TTS на видео
    else:

        pass
        # vids = generate_videos(blocks)
        # vids = burn_subtitles(vids, blocks)   # 2. накладываем субтитры
    vids = list_files_in_result("scene_*_tts_berned.mp4","result")    
    combine_videos(vids)

if __name__ == '__main__':
    asyncio.run(main())
