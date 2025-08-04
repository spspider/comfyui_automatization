
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

DEBUG = False#'audio'

from subtitles import format_time, generate_subtitles, ffmpeg_safe_path, burn_subtitles

async def generate_story(provider="qwen"):
    prompt = (
        "You are a viral video content creator. Generate a mostly trending video scene, which is best of the popular right now, mini vlogs, food challenges, DIY projects, dances, pet tricks, and transformation videos. Write a complete and structured script for a 30 second video.\n"
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
        
    print(f"🎬 Title: {meta['video_title']}")
    print(f"📝 Description: {meta['video_description']}")
    print(f"🏷️ Hashtags: {meta['video_hashtags']}")
    print(f"⏱️ Duration: {sum(scene['duration'] for scene in scenes)} seconds")
    
    # Save meta to video_output directory
    video_output_dir = Path("video_output")
    video_output_dir.mkdir(exist_ok=True)
    meta_file = video_output_dir / "meta.json"
    import json
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    for idx, blk in enumerate(scenes, 1):
        print(f"[Scene {idx}]")
        print(f"  Title: {blk.get('title')}")
        print(f"  Visual: {blk.get('visual')}")
        print(f"  Sound: {blk.get('sound')}")
        print(f"  Text: {blk.get('text')}")
        print(f"  Duration: {blk.get('duration')}")
        print("-" * 40)
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
        
        clip = text_to_video_wan_api_nouugf(blk, negative_prompt, video_seconds=duration)
        if clip:
            new_name = RESULT_DIR / f"scene_{idx:02d}_video.webm"  # Format index as 2-digit number
            shutil.move(Path(clip), str(new_name))  # Rename the file
            # os.unlink(clip)  # Remove the original file
            video_paths.append(str(new_name))
            print(f"✅ Video for scene {idx} saved as: {new_name}")
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
            reduce_audio_volume(audio_clip, newname, volume=0.7)
            try:
                os.remove(audio_clip)
            except Exception as e:
                print(f"⚠️ Could not delete original audio file {audio_clip}: {e}")
            audio_video_paths.append(str(newname))
        else:
            print(f"⚠️ No audio clip found for scene {idx}, using original.")
            audio_video_paths.append(video_path)
        
    return audio_video_paths

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
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def combine_videos(video_list, video_title="final_movie", output_path=RESULT_DIR):
    if not video_list:
        print("❌ No videos to combine. Exiting.")
        return
    safe_title = sanitize_filename(video_title)
    output_path = output_path / f"{safe_title}.mp4"
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
        return meta, blocks
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
    If the video has no audio, use only TTS.
    """
    updated_videos = []
    ffmpeg = r"c:\ProgramData\chocolatey\bin\ffmpeg.exe"

    for idx, video_path in enumerate(video_paths, 1):
        video_path = Path(video_path)
        tts_audio = RESULT_DIR / f"scene_{idx:02d}_voice.wav"
        output_path = RESULT_DIR / f"scene_{idx:02d}_tts.mp4"

        if not tts_audio.exists():
            print(f"⚠️ TTS audio not found for scene {idx}: {tts_audio}")
            updated_videos.append(str(video_path))
            continue

        # Check if video has audio
        probe_cmd = [
            ffmpeg, "-i", str(video_path),
            "-hide_banner", "-loglevel", "error", "-show_streams", "-select_streams", "a", "-of", "default=noprint_wrappers=1:nokey=1"
        ]
        has_audio = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "default=noprint_wrappers=1:nokey=1",
             str(video_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).stdout.decode().strip() != ""

        if has_audio:
            print(f"🎧 Scene {idx} has audio — mixing with TTS.")
            cmd = [
                ffmpeg, "-y",
                "-i", Path(video_path),
                "-i", Path(tts_audio),
                "-filter_complex",
                "[0:a]volume=0.6[a0]; [1:a]volume=1.0[a1]; [a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-shortest",
                Path(output_path)
            ]
        else:
            print(f"🔈 Scene {idx} has no audio — adding only TTS.")
            cmd = [
                ffmpeg, "-y",
                "-i", Path(video_path),
                "-i", Path(tts_audio),
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-shortest",
                Path(output_path)
            ]

        try:
            subprocess.run(cmd, check=True)
            updated_videos.append(str(output_path))
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to merge TTS with {video_path.name}: {e}")
            updated_videos.append(str(video_path))
    return updated_videos


def list_files_in_result(pattern, result_dir=None):
    result_dir = Path(r"C:/AI/comfyui_automatization/"+result_dir)
    return sorted([file for file in result_dir.glob(pattern) if file.is_file()])    

async def main():
    clean_comfy_output()   
    DEBUG = True
    if DEBUG:
        print("DEBUG mode: skip requesting new blocks.")
        meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
    else:
        meta, blocks = await get_story_blocks_with_retries("qwen", RESULT_DIR)
    if not blocks:
        return

       
    print(f"Parsed {len(blocks)} scenes.")

    vids = generate_videos(blocks) # generate videos from blocks

    vids = list_files_in_result("scene_*_video.webm","result") 
    blocks = update_blocks_with_real_duration(blocks)  # 1. обновляем длительность сцен

    vids = add_audio_to_scenes(vids, blocks)  # 2. накладываем аудио только звуки scene_{idx:02d}_audio.mp4"

    vids = list_files_in_result("scene_*_audio.mp4","result") 
    vids = burn_subtitles(vids, blocks)   # 2. накладываем субтитры f"{input_path.stem}_subtitled.mp4"
   
    vids = list_files_in_result("scene_*_audio_subtitled.mp4","result") 
    for idx, blk in enumerate(blocks, 1):
        generate_audio_from_text(blk["text"], output_path=f"result/scene_{idx:02d}_voice.wav")
    
    vids = list_files_in_result("scene_*_audio_subtitled.mp4","result") 
    burn_tts_to_video(vids, blocks)  # 3. накладываем TTS на видео

    vids = list_files_in_result("scene_*_tts.mp4","result")    
    combine_videos(vids, meta['video_title'], "video_output")
    

if __name__ == '__main__':
    asyncio.run(main())
