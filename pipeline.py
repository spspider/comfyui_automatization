
import os
import re
import argparse
import asyncio
import shutil
import subprocess
from pathlib import Path
from moviepy import concatenate_videoclips, VideoFileClip

from provider_all import generate_response_allmy
from text2video_workflow import run_text2video
from video2audio_workflow import run_video2audio
import pprint

COMFY_OUTPUT_DIR = Path(r"C:/AI/ComfyUI_windows_portable/ComfyUI/output")
RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

async def generate_story(provider="DeepSeek-r1"):
    prompt = (
        "You are a viral video content creator. Generate a complete and structured script for a 1-minute video.\n"
        "Respond using the exact format below for each scene:\n"
        "\n"
        "**[00:00-00:05]**\n"
        "**Title:** Opening Hook\n"
        "**Visual:** Describe the scene.\n"
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
    if not files:
        return None
    latest = max(files, key=lambda f: f.stat().st_mtime)
    dest = RESULT_DIR / latest.name
    shutil.copy(latest, dest)
    return dest

def generate_videos(blocks, negative_prompt="low quality, distorted, static"):
    video_paths = []
    for idx, blk in enumerate(blocks, 1):
        print(f"[Scene {idx}] Generating: {blk['title']}")
        run_text2video(blk['visual'], negative_prompt)
        clip = fetch_and_prepare_clip()
        if clip:
            ordered = RESULT_DIR / f"scene_{idx:02d}{clip.suffix}"
            clip.rename(ordered)
            video_paths.append(str(ordered))
        else:
            print(f"⚠️ No clip found for scene {idx}")
    return video_paths

def add_audio_to_scenes(video_paths, negative_prompt="low quality, noise"):
    audio_video_paths = []
    for path in video_paths:
        print(f"Adding audio to {path}")
        run_video2audio(video_path=path, prompt="", negative_prompt=negative_prompt)
        clip = fetch_and_prepare_clip(exts=(".mp4",))
        if clip:
            newname = RESULT_DIR / (Path(path).stem + "_audio" + clip.suffix)
            clip.rename(newname)
            audio_video_paths.append(str(newname))
        else:
            audio_video_paths.append(path)
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


    # blocks = await get_story_blocks_with_retries(args.provider, RESULT_DIR)
    blocks = (parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8")))
    if not blocks:
        return

    print(f"Parsed {len(blocks)} scenes.")
    pprint.pprint(blocks, sort_dicts=False, indent=2)
    vids = generate_videos(blocks)
    # if args.use_audio:
    #     vids = add_audio_to_scenes(vids)
    # combine_videos(vids)

if __name__ == '__main__':
    asyncio.run(main())
    # add_audio_to_scenes()