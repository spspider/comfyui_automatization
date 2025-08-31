
import gc
import os
import re
import argparse
import asyncio
import shutil
import subprocess
import json
import math
from pathlib import Path
from datetime import datetime
from moviepy import concatenate_videoclips, VideoFileClip

from utilites.text2audioZonos import generate_audio_from_text
from utilites.upload_youtube import upload_video
from utilites.text2audiof5 import run_f5_tts, run_speecht5_tts
from provider_all import generate_response_allmy
from workflow_run.run_t2v_wan22 import run_text2video
from workflow_run.text_to_video_wan_api_nouugf_wf import text_to_video_wan_api_nouugf
from utilites.utilites import reduce_audio_volume, clear_vram, sanitize_filename, create_youtube_csv, message_to_me
from workflow_run.video2audio_workflow import run_video2audio
from workflow_run.wan_2_1_t2v_gguf_api import wan_2_1_t2v_gguf_api
from utilites.argotranslate import translateTextBlocks, translate_meta
from utilites.upload_youtube import upload_video
from workflow_run.text_to_music_ace_step import run_text2music
from workflow_run.video_wan2_2_5B_ti2v import func_video_wan2_2_5B_ti2v

COMFY_OUTPUT_DIR = Path(r"C:/AI/ComfyUI_windows_portable/ComfyUI/output")
RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEBUG = False

from utilites.subtitles import create_full_subtitles_text, create_video_with_subtitles, clean_text_captions, burn_subtitles 

# Global variable to store chosen style
CHOSEN_STYLE = None

async def generate_story(provider="qwen"):
    global CHOSEN_STYLE
    
    # Define animation styles with consistent visual elements
    styles = [
        "Pixar 3D animation style, realistic fur texture, smooth skin, no hard outlines, cozy atmosphere, cinematic composition, golden-hour lighting",
        "Studio Ghibli anime style, hand-drawn animation, soft watercolor backgrounds, detailed nature elements, warm lighting, whimsical character design",
        "Disney 2D animation style, vibrant colors, expressive character faces, dynamic poses, fairy tale atmosphere, magical lighting effects",
        "Cartoon Network style, bold outlines, flat colors, exaggerated expressions, playful character design, bright saturated colors",
        "Realistic CGI animation style, photorealistic textures, detailed lighting, cinematic camera angles, high-quality rendering",
        "Anime manga style, cel-shaded animation, dramatic lighting, expressive eyes, dynamic action poses, vibrant colors",
        "Watercolor painting style, soft brush strokes, flowing colors, artistic texture, dreamy atmosphere, hand-painted look",
        "Retro 80s synthwave style, neon colors, geometric patterns, cyberpunk aesthetic, glowing effects, nostalgic vibes",
        "Paper cutout animation style, layered paper textures, shadow effects, handcrafted appearance, stop-motion feel",
        "Oil painting style, rich textures, classical art technique, warm color palette, Renaissance-inspired lighting",
        "Comic book style, bold outlines, halftone patterns, speech bubbles, dynamic panels, superhero aesthetic",
        "Isometric 3D style, geometric precision, clean angles, modern design, architectural visualization, technical illustration",
        "Holographic projection style, translucent surfaces, rainbow light refractions, floating digital elements, futuristic transparency effects",
        "Quantum particle visualization style, energy fields, glowing orbs, particle trails, scientific visualization, molecular structures",
        "Fractal geometry style, infinite recursive patterns, mathematical precision, kaleidoscopic effects, sacred geometry, hypnotic spirals",
        "Neural network visualization style, interconnected nodes, synaptic connections, brain-like patterns, electric impulses, AI consciousness",
        "Dimensional portal style, reality tears, space-time distortions, interdimensional rifts, cosmic gateways, parallel universe glimpses",
        "Metamorphic reality style, constantly shifting forms, reality glitches, impossible geometries, Escher-like paradoxes, dream logic"
    ]
    
    # Load status and select next style sequentially
    status_file = Path("status.json")
    if status_file.exists():
        with open(status_file, "r") as f:
            status = json.load(f)
        current_style_index = status.get("current_style_index", 0)
    else:
        current_style_index = 0
    
    # Select current style and update index
    chosen_style = styles[current_style_index]
    next_index = (current_style_index + 1) % len(styles)
    
    # Save updated status
    status = {"current_style_index": next_index}
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)
    
    CHOSEN_STYLE = chosen_style
    print(f"🎨 Using style {current_style_index + 1}/{len(styles)}: {chosen_style[:50]}...")
    
    prompt = (
        "You are a viral YouTube Shorts creator. Based on trending analysis, create VIRAL content focusing on these HIGH-PERFORMING themes:\n"
        "🔥 TOP VIRAL THEMES (prioritize these):\n"
        "- DIY transformations (wall makeovers, room upgrades, crafts)\n"
        "- Pet content (dogs baking, cats cooking, pet tricks, pet challenges)\n"
        "- Coffee/food magic (coffee art, cooking fails, food transformations)\n"
        "- Quick tutorials (5-minute fixes, 30-second hacks, instant results)\n"
        "- Satisfying content (slime making, glitter transformations, ASMR crafts)\n"
        "- Cute chaos (pets helping with tasks, cooking disasters turned wins)\n\n"
        "📈 VIRAL FORMULA: Use these proven elements:\n"
        "- Start with hook: 'Watch me transform...', 'This dog does WHAT?', 'DIY hack that went viral!'\n"
        "- Include pets as helpers/characters (dogs, cats, fluffy animals)\n"
        "- Show clear before/after transformations\n"
        "- Use satisfying visual elements (mixing, pouring, revealing)\n"
        "- End with surprising twist or amazing result\n\n"
        f"STYLE: {chosen_style}\n"
        "Create a 30-second video script with exactly 6 scenes (5 seconds each).\n"
        "IMPORTANT: Maintain visual continuity - repeat character descriptions and settings in each scene.\n"
        "Include subtle visual comedy and wordplay throughout the scenario. Create original humor through: unexpected character reactions, clever visual puns, amusing misunderstandings, or witty dialogue. Avoid repeating common jokes - be creative and original with each new scenario.\n"
        "\n"
        "**VIDEO_Title:** Viral-style title (use: 'DIY', 'This Dog', 'Watch Me', '30 Seconds', 'Viral', 'Magic')\n"
        "**VIDEO_Description:** YouTube description with hook and call-to-action.\n"
        "**VIDEO_Hashtags:** #diy, #viral, #pets, #transformation, #satisfying (choose 3-5 trending ones)\n"
        "**Overall_Music:** Upbeat, energetic background music description (no lyrics).\n"
        "**characters:** Detailed character descriptions (include pets, use names).\n"
        "\n"
        "**[00:00-00:05]**\n"
        "**Title:** Scene title\n"
        "**Visual:** Detailed scene describe front view and back view, include detalization of all components in a scene be very specific (10+ sentences, repeat character details from previous scenes)\n"
        "**Sound:** Ambient sounds/effects\n"
        "**Text:** Engaging narrator text, use 1-3 sentences, dont use styles\n"
        "---\n"
        "Continue for: [00:05-00:10], [00:10-00:15], [00:15-00:20], [00:20-00:25], [00:25-00:30]\n"
        "Final scene text must include: 'Subscribe!'\n"
    )
    return await generate_response_allmy(provider, prompt)

def extract_style_from_story(story_text):
    """Extract the STYLE from story text if present"""
    style_match = re.search(r'STYLE:\s*(.*?)(?=\n|$)', story_text)
    if style_match:
        return style_match.group(1).strip()
    return None

def parse_story_blocks(story_text):
    """
    Parse story text into metadata and scenes, handling optional scene-specific characters field.
    """
    # Clean unwanted content
    story_text = re.sub(r'<think>.*?</think>', '', story_text, flags=re.DOTALL)
    story_text = re.sub(r'^.*?#######.*?\n', '', story_text, flags=re.DOTALL)
    story_text = re.sub(r'that story generated\s*$', '', story_text, flags=re.DOTALL)
    story_text = story_text.strip()
    print(f"Parsed story text: {story_text[:100]}...")  # Debugging output, show first 100 chars
    
    # Extract style from story text
    extracted_style = extract_style_from_story(story_text)
    if extracted_style:
        global CHOSEN_STYLE
        CHOSEN_STYLE = extracted_style
    
    meta = {}
    # Parse metadata
    meta_match = re.search(
        r'\*\*VIDEO_Title:\*\*\s*(.*?)\s*\n'
        r'\*\*VIDEO_Description:\*\*\s*(.*?)\s*\n'
        r'\*\*VIDEO_Hashtags:\*\*\s*(.*?)\s*\n'
        r'\*\*Overall_Music:\*\*\s*(.*?)\s*\n'
        r'\*\*characters:\*\*\s*(.*?)\s*(?=\n\*\*\[\d{2}:\d{2}-\d{2}:\d{2}\]\*\*|\Z)',
        story_text,
        re.DOTALL
    )
    if meta_match:
        meta = {
            "video_title": meta_match.group(1).strip(),
            "video_description": meta_match.group(2).strip(),
            "video_hashtags": meta_match.group(3).strip().lower(),
            "overall_music": meta_match.group(4).strip(),
            "characters": meta_match.group(5).strip(),
            "chosen_style": CHOSEN_STYLE or "Pixar 3D animation style, realistic fur texture, smooth skin, no hard outlines, cozy atmosphere, cinematic composition, golden-hour lighting"
        }

    # Updated regex to make characters field optional and handle last scene properly
    pattern = re.compile(
        r'\*\*\[(\d{2}:\d{2})-(\d{2}:\d{2})\]\*\*\s*'
        r'(?:\*\*Title:\*\*\s*(.*?)\s*\n)?'  # Optional Title
        r'(?:\*\*characters:\*\*\s*(.*?)\s*\n)?'  # Optional characters field
        r'\*\*Visual:\*\*\s*(.*?)\s*\n'
        r'\*\*Sound:\*\*\s*(.*?)\s*\n'
        r'\*\*Text:\*\*\s*(.*?)(?=\s*(?:\*\*\[|\Z))',  # Text field ends at next scene or end of string
        re.DOTALL
    )

    scenes = []
    for match in pattern.finditer(story_text):
        start_str, end_str, title, characters, visual, sound, text = match.groups()
        def to_sec(t):
            minutes, seconds = map(int, t.split(":"))
            return minutes * 60 + seconds
        duration = to_sec(end_str) - to_sec(start_str)
        scenes.append({
            "title": title.strip() if title else "",
            "characters": characters.strip() if characters else "",
            "visual": visual.strip(),
            "sound": sound.strip(),
            "text": text.strip(),
            "duration": duration
        })
    
    # Print metadata and scenes
    print(f"🎬 Title: {meta['video_title']}")
    print(f"📝 Description: {meta['video_description']}")
    print(f"🏷️ Hashtags: {meta['video_hashtags']}")
    print(f"🎵 Overall Music: {meta['overall_music']}")
    print(f"👥 Characters: {meta['characters']}")
    print(f"⏱️ Duration: {sum(scene['duration'] for scene in scenes)} seconds")
    

    
    for idx, blk in enumerate(scenes, 1):
        print(f"[Scene {idx}]")
        print(f"  Title: {blk.get('title') or 'No Title'}")
        print(f"  Characters: {blk.get('characters') or 'No Characters'}")
        print(f"  Visual: {blk.get('visual')}")
        print(f"  Sound: {blk.get('sound')}")
        print(f"  Text: {blk.get('text')}")
        print(f"  Duration: {blk.get('duration')}")
        print("-" * 40)
    
    print(f"Parsed {len(scenes)} scenes.")
    return meta, scenes



def update_blocks_with_real_duration(blocks):
    """
    Update 'duration' (in seconds) and add 'duration_ms' (in milliseconds)
    from actual video file duration.
    """
    for idx, blk in enumerate(blocks, 1):
        video_path = RESULT_DIR / f"scene_{idx:02d}_video.webm"
        if video_path.exists():
            try:
                clip = VideoFileClip(str(video_path))
                duration_sec = clip.duration
                blk['duration'] = duration_sec
                clip.close()
            except Exception as e:
                print(f"⚠️ Could not get duration for {video_path}: {e}")
    return blocks

from datetime import datetime

def save_status(step, scene_idx=None, total_scenes=None):
    """Save current pipeline status while preserving existing data"""
    # Load existing status to preserve other fields
    try:
        with open("status.json", "r") as f:
            status = json.load(f)
    except FileNotFoundError:
        status = {}
    
    # Update pipeline-specific fields
    status.update({
        "step": step,
        "scene_idx": scene_idx,
        "total_scenes": total_scenes,
        "timestamp": datetime.now().isoformat()
    })
    
    with open("status.json", "w") as f:
        json.dump(status, f, indent=2)

def load_status():
    """Load pipeline status"""
    try:
        with open("status.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    
def generate_videos(blocks, meta, negative_prompt="low quality, distorted, static"):
    video_paths = []
    status = load_status()
    start_idx = 1
    
    # Check if resuming from previous run
    if status and status.get("step") == "generate_videos":
        start_idx = status.get("scene_idx", 1) + 1
        print(f"🔄 Resuming video generation from scene {start_idx}")
        # Load existing videos
        for i in range(1, start_idx):
            existing_video = RESULT_DIR / f"scene_{i:02d}_video.mp4"
            if existing_video.exists():
                video_paths.append(str(existing_video))
    
    save_status("generate_videos", 0, len(blocks))
    
    for idx, blk in enumerate(blocks, 1):
        if idx < start_idx:
            continue
            
        print(f"[Scene {idx}] Generating: {blk['title']}")
        duration = blk.get('duration', 10)
        if not isinstance(duration, int) or duration > 10 or duration <= 0:
            duration = 10
            
        timestamp = datetime.now().strftime("%H:%M")
        print(f"⌛ Waiting for completion... [{timestamp}]")
        positive_prompt = meta['characters'] + "\n" + blk['visual']
        additional_style = f"STYLE: {meta.get('chosen_style', 'Pixar 3D animation style, realistic fur texture, smooth skin, no hard outlines, cozy atmosphere, cinematic composition, golden-hour lighting')}\n"

        clip = func_video_wan2_2_5B_ti2v(additional_style +" PROMPT:"+ positive_prompt,  video_seconds=5) # override duration for testing purposes
        #clip = wan_2_1_t2v_gguf_api(additional_style +" PROMPT:"+ positive_prompt,  video_seconds=5) # override duration for testing purposes
        # clip = text_to_video_wan_api_nouugf(blk, negative_prompt, video_seconds=duration)
        # clip = run_text2video(blk['visual'])
        if clip:
            new_name = RESULT_DIR / f"scene_{idx:02d}_video.mp4"  # Format index as 2-digit number
            shutil.move(Path(clip), str(new_name))  # Rename the file
            # os.unlink(clip)  # Remove the original file
            video_paths.append(str(new_name))
            print(f"✅ Video for scene {idx} saved as: {new_name}")
            save_status("generate_videos", idx, len(blocks))  # Save progress after each scene
        else:
            print(f"⚠️ No clip found for scene {idx}")
        clear_vram()
    
    save_status("generate_videos_complete", len(blocks), len(blocks))
    return video_paths

def each_audio_scene(video_path, prompt, negative_prompt="low quality, noise, music, song", idx=1, newname=None, volumelevel=0.7):
        print(f"🔊 Adding audio to {video_path}")
        audio_clip = run_video2audio(video_path=video_path, prompt=prompt, negative_prompt=negative_prompt)
        if audio_clip:
            newname = newname or (RESULT_DIR / f"scene_{idx:02d}_audio.mp4")
            reduce_audio_volume(audio_clip, newname, volume=volumelevel)
            try:
                os.remove(audio_clip)
            except Exception as e:
                print(f"⚠️ Could not delete original audio file {audio_clip}: {e}")
            newname = str(newname)
        else:
            print(f"⚠️ No audio clip found for scene {idx}, using original.")
            newname = str(video_path)
        clear_vram()
        return newname

def add_audio_to_scenes(video_paths, blocks, negative_prompt="low quality, noise, music, speaking, chatting, lyrics, singing, human voice, vocals, words, talking"):

    audio_video_paths = []
    for idx, (video_path, blk) in enumerate(zip(video_paths, blocks), 1):
        newname = each_audio_scene(video_path, blk['sound'], negative_prompt, idx, newname=RESULT_DIR / f"scene_{idx:02d}_audio.mp4")
        audio_video_paths.append(newname)

    return audio_video_paths




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
    return output_path

    
async def get_story_blocks_with_retries(provider, result_dir, max_attempts=3):
    """Try to generate and parse story blocks, retrying if parsing fails."""
    for attempt in range(max_attempts):
        try:
            story = await generate_story(provider=provider)
            print("\n--- Scenario ---\n", story)
            # Save story to result folder as txt
            story_file = result_dir / "story.txt"
            try:
                with open(story_file, "w", encoding="utf-8") as f:
                    f.write(story)
                meta, blocks = parse_story_blocks((result_dir / "story.txt").read_text(encoding="utf-8"))
                if meta and blocks:  # Ensure valid output
                    return meta, blocks
                else:
                    print(f"⚠️ Attempt {attempt + 1}: Parsed output is empty or invalid.")
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1}: Failed to parse story: {e}")
                continue  # Retry on parsing failure

        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1}: Failed to generate story: {e}")
            continue  # Retry on story generation failure

    print(f"❌ Failed to generate or parse structured output after {max_attempts} attempts.")
    return None, []

def clean_comfy_output(DIR=COMFY_OUTPUT_DIR):
    """Remove all files from ComfyUI output directory"""
    for file in DIR.glob("*"):
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

def generate_combined_tts_audio(blocks, output_path):
    """
    Joins all blocks' text into a single narration for entire video, preserving timing info.
    Returns the list of durations (seconds) for each block, and path to full audio.
    """
 

    full_text = "\n".join([blk['text'] for blk in blocks])
    generate_audio_from_text(text=full_text, output_path=output_path)
    return output_path






def list_files_in_result(pattern, result_dir=None):
    result_dir = Path(r"C:/AI/comfyui_automatization/"+result_dir)
    return sorted([file for file in result_dir.glob(pattern) if file.is_file()])    

async def main_production():
    clean_comfy_output(COMFY_OUTPUT_DIR)  
    video_output_dir = Path("video_output")
    video_output_dir.mkdir(exist_ok=True)

    # Check if resuming from previous run
    status = load_status()
    if status and status.get("step") == "generate_videos":
        print(f"🔄 Resuming from previous run at step: {status['step']}, scene: {status.get('scene_idx', 'N/A')}")
        # Load existing story and blocks
        meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
    else:
        if DEBUG:
            print("DEBUG mode: skip requesting new blocks.")
            meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
        else:
            clean_comfy_output(RESULT_DIR)  
            meta, blocks = await get_story_blocks_with_retries("qwen", RESULT_DIR)
        if not blocks:
            return

    print(f"Parsed {len(blocks)} scenes.")
    
    vids = generate_videos(blocks,meta) # generate videos from blocks
    vids = list_files_in_result("scene_*_video.*","result") 
    blocks = update_blocks_with_real_duration(blocks)  # 1. обновляем длительность сцен
    blocks = clean_text_captions(blocks)  # 2. очищаем текст от лишних символов
    clear_vram()
    vids = add_audio_to_scenes(vids, blocks)  # 2. накладываем аудио только звуки scene_{idx:02d}_audio.mp4"
    
    vids = list_files_in_result("scene_*_audio.mp4","result") 

    blocks = translateTextBlocks(blocks, ["ru","ro"])  # 3. переводим текст на английский
    # here we can create different languages
    original_vids = vids.copy()  # Keep original video list
    for language in ["en", "ro", "ru"]:
        burn_subtitles(original_vids, blocks, language)   # 2. накладываем субтитры f"{input_path.stem}_subtitled.mp4"
    clear_vram()
    ####################TTS for RU########################
    language = "ru"  # Change to "ru" or "ro" for other languages
    for idx, blk in enumerate(blocks, 1):
        run_f5_tts(
            language=language,
            gen_text=blk["text"][language],
            output_file=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
        )
    ####################TTS for EN########################
    language = "en"  # Change to "ru" or "ro" for other languages
    for idx, blk in enumerate(blocks, 1):
        generate_audio_from_text(
            language=language,
            text=blk["text"][language],
            output_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
        )
    ####################TTS for EN########################
    language = "ro"  # Change to "ru" or "ro" for other languages
    for idx, blk in enumerate(blocks, 1):
        generate_audio_from_text(
            language=language,
            text=blk["text"][language],
            output_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
        )
    ####################################END TTS#############       
    clear_vram()
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP merge_audio_and_video[{timestamp}]")
    for language in ["en", "ro", "ru"]:
        for idx, blk in enumerate(blocks, 1):
            merge_audio_and_video(
                blocks=blocks,
                audio_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                video_path=RESULT_DIR / f"scene_{idx:02d}_audio_subtitled_{language}.mp4",
                output_path=RESULT_DIR / f"scene_{idx:02d}_merged_{language}.mp4",
                original_audio_volume=0.3,
                voice_volume=4.0
            )
    for language in ["en", "ro", "ru"]:
        vids = list_files_in_result(f"scene_*_merged_{language}.mp4","result") 
        video = combine_videos(vids, f"final_movie_{language}", output_path=Path("result/"))
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP each_audio_scene [{timestamp}]")
    ####generate music
    clear_vram()
    generated_music = run_text2music(prompt=meta["overall_music"], 
                                     negative_prompt="low quality, noise, static, blurred details, subtitles, paintings, pictures, lyrics, text", 
                                     duration=VideoFileClip(str(RESULT_DIR/"final_movie_en.mp4")).duration,
                                     output_name=RESULT_DIR / "final_movie_music.mp4")
    
    for language in ["en", "ro", "ru"]:
        output_path=f"video_output/{sanitize_filename(meta['video_title'])}_{language}"
        merge_audio_and_video(
            blocks=blocks,
            audio_path=RESULT_DIR / "final_movie_music.mp4",
            video_path=RESULT_DIR / f"final_movie_{language}.mp4",
            output_path=f"{output_path}.mp4",
            original_audio_volume=0.2,  # Adjust volume level as needed,
            voice_volume=1.0
        )
        # create_youtube_csv(meta, output_path)
    
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP [{timestamp}]")
    for language in ["en", "ro", "ru"]:
        subtitle_file = create_full_subtitles_text(blocks, language)
        subtitle_output = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.srt"
        shutil.copy(subtitle_file, subtitle_output)
        print(f"📝 Subtitle file saved to: {subtitle_output}")

    #save meta
    # Save meta to video_output directory
    ################# translate meta #################
    for language in ["en", "ro", "ru"]:
        if language == "en":
            translated_meta = meta
        else:
            translated_meta = translate_meta(meta, language)
        meta_file = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(translated_meta, f, ensure_ascii=False, indent=2)
    ###### UPLOAD VIDEOS TO YOUTUBE ######
    # for language in ["en", "ro", "ru"]:
    #     meta_file = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.json"
    #     with open(meta_file, "r", encoding="utf-8") as f:
    #         translated_meta = json.load(f)
        
    #     video_file = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.mp4"
    #     upload_video(
    #         file=str(video_file),
    #         title=translated_meta["video_title"],
    #         description=translated_meta["video_description"],
    #         tags=translated_meta["video_hashtags"].split(", "),
    #         language=language,
    #         privacyStatus="public"
    #     )
    # ############### move uploaded videos to folder uploaded_videos ###############
    # uploaded_dir = Path("uploaded_videos")
    # uploaded_dir.mkdir(exist_ok=True)
    
    # for language in ["en", "ro", "ru"]:
    #     video_file = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.mp4"
    #     json_file = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.json"
        
    #     if video_file.exists():
    #         shutil.move(str(video_file), str(uploaded_dir / video_file.name))
    #     if json_file.exists():
    #         shutil.move(str(json_file), str(uploaded_dir / json_file.name))
    
    clear_vram()
    # Clear pipeline status after successful completion, keep style_index
    status = load_status()
    if status:
        # Keep only style-related data
        new_status = {k: v for k, v in status.items() if k == "current_style_index"}
        with open("status.json", "w") as f:
            json.dump(new_status, f, indent=2)
    
    message_to_me("🎬 Video generation pipeline completed successfully!")
    #############END#############
async def main_test(): 
    meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
    print(f"Parsed {len(blocks)} scenes.")
    blocks = clean_text_captions(blocks)  # 2. очищаем текст от лишних символов
    blocks = translateTextBlocks(blocks, ["ru","ro"])  # 3. переводим текст на английский
    print("Starting test pipeline...")
    message_to_me(f"🎬 Video generated {meta['video_title']}")
###### DO NOT DELETE BLOCK ABOVE ######
    return
    ####################TTS for RU########################
    language = "ru"  # Change to "ru" or "ro" for other languages
    for idx, blk in enumerate(blocks, 1):
        run_f5_tts(
            language=language,
            gen_text=blk["text"][language],
            output_file=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
        )
    ####################TTS for EN########################
    language = "en"  # Change to "ru" or "ro" for other languages
    for idx, blk in enumerate(blocks, 1):
        generate_audio_from_text(
            language=language,
            text=blk["text"][language],
            output_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
        )
    ####################TTS for EN########################
    language = "ro"  # Change to "ru" or "ro" for other languages
    for idx, blk in enumerate(blocks, 1):
        generate_audio_from_text(
            language=language,
            text=blk["text"][language],
            output_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
        )
    ####################################END TTS#############       

    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP merge_audio_and_video[{timestamp}]")
    for language in ["en", "ro", "ru"]:
        for idx, blk in enumerate(blocks, 1):
            merge_audio_and_video(
                blocks=blocks,
                audio_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                video_path=RESULT_DIR / f"scene_{idx:02d}_audio_subtitled_{language}.mp4",
                output_path=RESULT_DIR / f"scene_{idx:02d}_merged_{language}.mp4",
                original_audio_volume=0.3,
                voice_volume=3.0
            )
    for language in ["en", "ro", "ru"]:
        vids = list_files_in_result(f"scene_*_merged_{language}.mp4","result") 
        video = combine_videos(vids, f"final_movie_{language}", output_path=Path("result/"))
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP each_audio_scene [{timestamp}]")
    ####generate music
    generated_music = run_text2music(prompt=meta["overall_music"], 
                                     negative_prompt="low quality, noise, static, blurred details, subtitles, paintings, pictures, lyrics, text", 
                                     duration=VideoFileClip(str(RESULT_DIR/"final_movie_en.mp4")).duration,
                                     output_name=RESULT_DIR / "final_movie_music.mp4")
    
    for language in ["en", "ro", "ru"]:
        output_path=f"video_output/{sanitize_filename(meta['video_title'])}_{language}"
        merge_audio_and_video(
            blocks=blocks,
            audio_path=RESULT_DIR / "final_movie_music.mp4",
            video_path=RESULT_DIR / f"final_movie_{language}.mp4",
            output_path=f"{output_path}.mp4",
            original_audio_volume=0.2,  # Adjust volume level as needed,
            voice_volume=1.0
        )
        # create_youtube_csv(meta, output_path)
    
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP [{timestamp}]")
    for language in ["en", "ro", "ru"]:
        subtitle_file = create_full_subtitles_text(blocks, language)
        subtitle_output = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.srt"
        shutil.copy(subtitle_file, subtitle_output)
        print(f"📝 Subtitle file saved to: {subtitle_output}")

    #save meta
    # Save meta to video_output directory
    ################# translate meta #################
    for language in ["en", "ro", "ru"]:
        if language == "en":
            translated_meta = meta
        else:
            translated_meta = translate_meta(meta, language)
        meta_file = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(translated_meta, f, ensure_ascii=False, indent=2)

DEBUG = False    
if __name__ == "__main__":
    if DEBUG:
        print("Running in DEBUG mode...")
        asyncio.run(main_test())
    else:
        print("Running in PRODUCTION mode...")
        while True:
            asyncio.run(main_production())
