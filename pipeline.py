
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
from utilites.utilites import reduce_audio_volume, clear_vram, sanitize_filename, create_youtube_csv, message_to_me, add_russian_stress
from workflow_run.video2audio_workflow import run_video2audio
from workflow_run.wan_2_1_t2v_gguf_api import wan_2_1_t2v_gguf_api
from utilites.argotranslate import translateTextBlocks, translate_meta
from utilites.upload_youtube import upload_video
from workflow_run.text_to_music_ace_step import run_text2music
from workflow_run.video_wan2_2_5B_ti2v import func_video_wan2_2_5B_ti2v
from utilites.utilites import merge_audio_and_video
from utilites.subtitles import burn_tts_to_video

COMFY_OUTPUT_DIR = Path(r"C:/AI/ComfyUI_windows_portable/ComfyUI/output")
RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEBUG = False
LANGUAGES = ["en", "ru"]  # Languages to generate (first is main)

from utilites.subtitles import create_full_subtitles_text, create_video_with_subtitles, clean_text_captions, burn_subtitles 

# Global variable to store chosen style
CHOSEN_STYLE = None

async def generate_story(provider="qwen"):
    global CHOSEN_STYLE
    
    # Load configuration
    try:
        with open("content_config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("⚠️ content_config.json not found, using defaults")
        config = {
            "content_preferences": {"animation_weight": 0.6, "live_action_weight": 0.4},
            "style_rotation": {
                "animation_styles": ["Pixar 3D animation style, realistic textures, cinematic lighting"],
                "live_action_styles": ["Cinematic film style, professional cinematography, dramatic lighting"]
            },
            "theme_categories": {"lifestyle": ["general content"]}
        }
    
    content_types = ["animation", "live_action"]
    animation_styles = config["style_rotation"]["animation_styles"]
    live_action_styles = config["style_rotation"]["live_action_styles"]
    theme_categories = config["theme_categories"]
    
    # Load status and rotate through content types and styles
    status_file = Path("status.json")
    if status_file.exists():
        with open(status_file, "r") as f:
            status = json.load(f)
        current_content_index = status.get("current_content_index", 0)
        current_style_index = status.get("current_style_index", 0)
        current_theme_category = status.get("current_theme_category", "lifestyle")
    else:
        current_content_index = 0
        current_style_index = 0
        current_theme_category = "lifestyle"
    
    # Select content type and style
    content_type = content_types[current_content_index]
    
    if content_type == "animation":
        chosen_style = animation_styles[current_style_index % len(animation_styles)]
    else:
        chosen_style = live_action_styles[current_style_index % len(live_action_styles)]
    
    # Rotate theme category independently
    theme_keys = list(theme_categories.keys())
    current_theme_index = status.get("current_theme_index", 0)
    current_theme_key = theme_keys[current_theme_index % len(theme_keys)]
    themes = theme_categories[current_theme_key]
    
    # Update indices for next run
    next_content_index = (current_content_index + 1) % len(content_types)
    max_styles = len(animation_styles) if content_type == "animation" else len(live_action_styles)
    next_style_index = (current_style_index + 1) % max_styles
    next_theme_index = (current_theme_index + 1) % len(theme_keys)
    
    # Save updated status
    status = {
        "current_content_index": next_content_index,
        "current_style_index": next_style_index,
        "current_theme_index": next_theme_index,
        "current_theme_category": current_theme_key
    }
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)
    
    CHOSEN_STYLE = chosen_style
    print(f"🎨 Content: {content_type} | Style: {chosen_style[:50]}... | Theme: {current_theme_key}")
    
    # Create diverse prompt based on content type
    if content_type == "animation":
        prompt = f"""
You are a viral YouTube Shorts creator. Create diverse, engaging content that avoids repetitive themes.

🎯 CONTENT VARIETY - Choose ONE theme from: {', '.join(themes)}
AVOID: AI themes, robots, technology dystopia, overused pet/coffee content. Focus on realistic, relatable content!

📈 VIRAL ELEMENTS:
- Strong hook in first 3 seconds
- Clear value proposition or entertainment
- Realistic scenarios and characters
- Surprising twist or reveal
- Call-to-action ending

REQUIREMENTS:
- NO AI themes, robots, or futuristic technology
- Focus on realistic human experiences
- Use believable scenarios and situations

STYLE: {chosen_style}

Create a 30-second video script with exactly 6 scenes (5 seconds each).
MAINTAIN visual continuity - repeat character/setting descriptions.

**VIDEO_Title:** Engaging title (avoid overused phrases)
**VIDEO_Description:** YouTube description with hook
**VIDEO_Hashtags:** 3-5 relevant trending hashtags
**Overall_Music:** Background music description (no lyrics)
**characters:** Detailed character descriptions

**[00:00-00:05]**
**Title:** Scene title
**Visual:** Detailed scene description (10+ sentences, specific details)
**Sound:** Ambient sounds/effects
**Text:** Engaging narrator text (1-3 sentences)
---
Continue for: [00:05-00:10], [00:10-00:15], [00:15-00:20], [00:20-00:25], [00:25-00:30]
Final scene must include: 'Subscribe!'
"""
    else:
        prompt = f"""
You are a viral YouTube Shorts creator. Create engaging LIVE-ACTION content.

🎯 CONTENT THEME: {current_theme_key.upper()} - Choose from: {', '.join(themes)}

📈 LIVE-ACTION VIRAL ELEMENTS:
- Real people, authentic scenarios
- Practical demonstrations or tutorials
- Before/after transformations
- Relatable situations
- Clear educational or entertainment value

REQUIREMENTS:
- NO AI themes, robots, or unrealistic technology
- Focus on genuine human experiences
- Use practical, achievable scenarios

STYLE: {chosen_style}

Create a 30-second LIVE-ACTION video script with exactly 6 scenes (5 seconds each).
Focus on REAL PEOPLE and practical content.

**VIDEO_Title:** Engaging title
**VIDEO_Description:** YouTube description
**VIDEO_Hashtags:** 3-5 relevant hashtags
**Overall_Music:** Background music description
**characters:** Real people descriptions (ages, appearance, roles)

**[00:00-00:05]**
**Title:** Scene title
**Visual:** Live-action scene description (real settings, people, actions)
**Sound:** Ambient sounds/effects
**Text:** Narrator text (1-3 sentences)
---
Continue for all 6 scenes, ending with 'Subscribe!'
"""
    
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
            "chosen_style": CHOSEN_STYLE or "realistic fur texture, smooth skin, no hard outlines, cozy atmosphere, cinematic composition, golden-hour lighting"
        }

    # Updated regex to make characters field optional and handle last scene properly
    pattern = re.compile(
        r'\*\*\[(\d{2}:\d{2})-(\d{2}:\d{2})\]\*\*\s*'
        r'(?:\*\*Title:\*\*\s*(.*?)\s*\n)?'  # Optional Title
        r'(?:\*\*characters:\*\*\s*(.*?)\s*\n)?'  # Optional characters field
        r'\*\*Visual:\*\*\s*(.*?)\s*\n'
        r'\*\*Sound:\*\*\s*(.*?)\s*\n'
        r'\*\*Text:\*\*\s*(.*?)(?=\s*(?:\*\*\[|\n\s*[^\*]|\Z))',  # Text field ends at next scene, newline with non-asterisk content, or end of string
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

def track_content_diversity():
    """Track and display content diversity statistics"""
    try:
        with open("content_history.json", "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {"videos": [], "themes": {}, "styles": {}, "content_types": {}}
    
    status = load_status()
    if status:
        current_theme = status.get("current_theme_category", "unknown")
        current_style = CHOSEN_STYLE or "unknown"
        content_type = "animation" if any(keyword in current_style.lower() 
                                        for keyword in ['animation', 'pixar', 'disney', 'cartoon']) else "live_action"
        
        # Update counters
        history["themes"][current_theme] = history["themes"].get(current_theme, 0) + 1
        history["content_types"][content_type] = history["content_types"].get(content_type, 0) + 1
        history["styles"][current_style[:30]] = history["styles"].get(current_style[:30], 0) + 1
        
        # Add to video history
        history["videos"].append({
            "timestamp": datetime.now().isoformat(),
            "theme": current_theme,
            "content_type": content_type,
            "style": current_style[:50]
        })
        
        # Keep only last 20 videos
        history["videos"] = history["videos"][-20:]
        
        # Save updated history
        with open("content_history.json", "w") as f:
            json.dump(history, f, indent=2)
        
        # Display diversity stats
        print("\n📈 CONTENT DIVERSITY STATS:")
        print(f"Themes: {dict(list(history['themes'].items())[-5:])}")
        print(f"Content Types: {history['content_types']}")
        print(f"Recent Videos: {len(history['videos'])}")
        print("-" * 50)
    
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
    
    # Determine content type from style
    content_type = "animation" if any(keyword in meta.get('chosen_style', '').lower() 
                                    for keyword in ['animation', 'pixar', 'disney', 'cartoon', 'anime', 'ghibli']) else "live_action"
    
    print(f"🎬 Generating {content_type} content with style: {meta.get('chosen_style', 'default')[:50]}...")
    
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

    # Track content diversity
    track_content_diversity()

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

    blocks = translateTextBlocks(blocks, [lang for lang in LANGUAGES if lang != "en"])  # 3. переводим текст с английского на другие языки
    
    # here we can create different languages
    original_vids = vids.copy()  # Keep original video list
    for language in LANGUAGES:
        burn_subtitles(original_vids, blocks, language)   # 2. накладываем субтитры f"{input_path.stem}_subtitled.mp4"
    # Добавляем ударения для русского языка
    for block in blocks:
        if "ru" in block["text"]:
            block["text"]["ru"] = add_russian_stress(block["text"]["ru"])
    clear_vram()
    # Generate TTS for all languages
    for language in LANGUAGES:
        for idx, blk in enumerate(blocks, 1):
            if language == "ru":
                run_f5_tts(
                    language=language,
                    gen_text=blk["text"][language],
                    output_file=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                )
            if language == "en":
                generate_audio_from_text(
                    language=language,
                    text=blk["text"][language],
                    output_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                )
            if language == "ro":
                run_speecht5_tts(
                    language=language,
                    gen_text=blk["text"][language],
                    output_file=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                    )
    clear_vram()
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP merge_audio_and_video[{timestamp}]")
    for language in LANGUAGES:
        for idx, blk in enumerate(blocks, 1):
            merge_audio_and_video(
                blocks=blocks,
                audio_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                video_path=RESULT_DIR / f"scene_{idx:02d}_audio_subtitled_{language}.mp4",
                output_path=RESULT_DIR / f"scene_{idx:02d}_merged_{language}.mp4",
                original_audio_volume=0.3,
                voice_volume=4.0
            )
    for language in LANGUAGES:
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
    
    for language in LANGUAGES:
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
    for language in LANGUAGES:
        subtitle_file = create_full_subtitles_text(blocks, language)
        subtitle_output = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.srt"
        shutil.copy(subtitle_file, subtitle_output)
        print(f"📝 Subtitle file saved to: {subtitle_output}")

    #save meta
    # Save meta to video_output directory
    ################# translate meta #################
    for language in LANGUAGES:
        if language == "en":
            translated_meta = meta
        else:
            translated_meta = translate_meta(meta, language)
        meta_file = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(translated_meta, f, ensure_ascii=False, indent=2)
    
    clear_vram()
    # Clear pipeline status after successful completion, keep style_index
    status = load_status()
    if status:
        # Keep only style-related data
        new_status = {k: v for k, v in status.items() if k == "current_style_index"}
        with open("status.json", "w") as f:
            json.dump(new_status, f, indent=2)
    
    message_to_me(f"🎬 Video generated {meta['video_title']}")
    #############END#############
async def main_test(): 
    meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
    print(f"Parsed {len(blocks)} scenes.")
    blocks = clean_text_captions(blocks)  # 2. очищаем текст от лишних символов
    blocks = translateTextBlocks(blocks, [lang for lang in LANGUAGES if lang != "en"])  # 3. переводим текст на английский
    
    # Добавляем ударения для русского языка
    for block in blocks:
        if "ru" in block["text"]:
            block["text"]["ru"] = add_russian_stress(block["text"]["ru"])
    print("Starting test pipeline...")
###### DO NOT DELETE BLOCK ABOVE ######
   
    # Generate TTS for all languages
    for language in LANGUAGES:
        for idx, blk in enumerate(blocks, 1):
            if language == "ru":
                run_f5_tts(
                    language=language,
                    gen_text=blk["text"][language],
                    output_file=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                )
            else:
                generate_audio_from_text(
                    language=language,
                    text=blk["text"][language],
                    output_path=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
                )       

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
