
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

from utilites.text2audiof5 import run_f5_tts, run_speecht5_tts
from provider_all import generate_response_allmy
from workflow_run.run_t2v_wan22 import run_text2video
from workflow_run.text_to_video_wan_api_nouugf_wf import text_to_video_wan_api_nouugf
from utilites.utilites import reduce_audio_volume, clear_vram, sanitize_filename, create_youtube_csv
from workflow_run.video2audio_workflow import run_video2audio
from workflow_run.wan_2_1_t2v_gguf_api import wan_2_1_t2v_gguf_api
from utilites.argotranslate import translateTextBlocks
from workflow_run.text_to_music_ace_step import run_text2music

COMFY_OUTPUT_DIR = Path(r"C:/AI/ComfyUI_windows_portable/ComfyUI/output")
RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEBUG = False

from utilites.subtitles import create_full_subtitles_text, create_video_with_subtitles, clean_text_captions, burn_subtitles 

async def generate_story(provider="qwen"):
    prompt = (
        "You are a viral YouTube Shorts creator using AI to make engaging 30-second videos. Generate a cohesive, continuous story based on popular themes like mini vlogs, food challenges, DIY projects, dances, pet tricks, or transformations be various. Avoid specific niche trends; focus on relatable, timeless ideas that are visually appealing and easy to follow.\n"
        "STYLE: style of Pixar 3D animation, realistic fur texture, smooth skin, no hard outlines, cozy atmosphere, cinematic composition, Pixar-style character design\n"
        "Write a complete structured script for a 30-second video, divided into exactly 6 scenes of 5 seconds each.\n"
        "Start with a short title, a YouTube-ready description, and 1-3 relevant hashtags.\n"
        "IMPORTANT: Treat the story as one continuous narrative. For each scene, explicitly repeat and build upon context from previous scenes (e.g., if a character wears red in scene 1, describe them as 'the character in red' in later scenes; repeat locations, actions, and states). Repeat key descriptions in Visual and Sound to maintain continuity, as scenes will be processed separately.\n"
        "REPEAT AND BUILD ON PREVIOUS CONTEXT IN EVERY SCENE DESCRIPTION.\n"
        "Respond using this EXACT format only:\n"
        "\n"
        "**VIDEO_Title:** Short, catchy video title.\n"
        "**VIDEO_Description:** Brief description for YouTube, 1-2 sentences.\n"
        "**VIDEO_Hashtags:** 1-3 hashtags, separated by commas.\n"
        "**Overall_Music:** Description of background music fitting the entire video (e.g., upbeat pop track).\n"
        "**characters:** Detailed visual descriptions of all main characters (use names to separate, e.g., 'Alice: young woman with long blonde hair, wearing casual jeans; Bob: fluffy white dog'). This will be referenced in every scene.\n"
        "\n"
        "**[00:00-00:05]**\n"
        "**Title:** Short scene title.\n"
        "**Visual:** Detailed scene description, incorporating the characters block. Use at least 10 sentences covering background, foreground, actions, and visuals. Repeat context from prior scenes.\n"
        "**Sound:** Describe ambient sounds or effects, building on prior scenes. In the last scene, include a call-to-action sound if needed.\n"
        "**Text:** On-screen caption and narrator text, you can enumerate ingredients, steps, or instructions (7-15 words, with emotions like 'Wow!' or exclamation marks) it can be more than 5 sec, feel free to put more text and storytelling elements.\n"
        "---\n"
        "Repeat for each 5-second segment: [00:05-00:10], [00:10-00:15], [00:15-00:20], [00:20-00:25], [00:25-00:30].\n"
        "In the last scene's Text, include a subscribe call like 'Subscribe now!'.\n"
        "Ensure timestamps are exact and total 30 seconds. Do not add any extra text, explanations, or variations outside this format.\n"
    )
    return await generate_response_allmy(provider, prompt)

def parse_story_blocks(story_text):
    """
    Parse story text into metadata and scenes, handling optional scene-specific characters field.
    """
    story_text = re.sub(r'<think>.*?</think>', '', story_text, flags=re.DOTALL).strip()
    print(f"Parsed story text: {story_text[:100]}...")  # Debugging output, show first 100 chars
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
            "characters": meta_match.group(5).strip()
        }

    # Updated regex to make characters field optional
    pattern = re.compile(
        r'\*\*\[(\d{2}:\d{2})-(\d{2}:\d{2})\]\*\*\s*'
        r'(?:\*\*Title:\*\*\s*(.*?)\s*\n)?'  # Optional Title
        r'(?:\*\*characters:\*\*\s*(.*?)\s*\n)?'  # Optional characters field
        r'\*\*Visual:\*\*\s*(.*?)\s*\n'
        r'\*\*Sound:\*\*\s*(.*?)\s*\n'
        r'\*\*Text:\*\*\s*(.*?)\s*(?=\n\*\*\[\d{2}:\d{2}-\d{2}:\d{2}\]\*\*|\n\*\*[^\[]+|\Z)',
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
    
def generate_videos(blocks, meta, negative_prompt="low quality, distorted, static"):
    video_paths = []
    for idx, blk in enumerate(blocks, 1):
        print(f"[Scene {idx}] Generating: {blk['title']}")
        duration = blk.get('duration', 10)
        if not isinstance(duration, int) or duration > 10 or duration <= 0:
            duration = 10
            
        timestamp = datetime.now().strftime("%H:%M")
        print(f"⌛ Waiting for completion... [{timestamp}]")
        positive_prompt = meta['characters'] + "\n" + blk['visual']
        additional_style = "STYLE: style of Pixar 3D animation, Soft global illumination, realistic fur texture, smooth skin, no hard outlines, cozy atmosphere, cinematic composition, golden-hour lighting, Pixar-style character design\n"
        clip = wan_2_1_t2v_gguf_api(additional_style + positive_prompt,  video_seconds=5) # override duration for testing purposes

        # clip = text_to_video_wan_api_nouugf(blk, negative_prompt, video_seconds=duration)
        # clip = run_text2video(blk['visual'])
        if clip:
            new_name = RESULT_DIR / f"scene_{idx:02d}_video.mp4"  # Format index as 2-digit number
            shutil.move(Path(clip), str(new_name))  # Rename the file
            # os.unlink(clip)  # Remove the original file
            video_paths.append(str(new_name))
            print(f"✅ Video for scene {idx} saved as: {new_name}")
        else:
            print(f"⚠️ No clip found for scene {idx}")
        clear_vram()
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

def add_audio_to_scenes(video_paths, blocks, negative_prompt="low quality, noise, music, speaking, chatting"):

    audio_video_paths = []
    for idx, (video_path, blk) in enumerate(zip(video_paths, blocks), 1):
        newname = each_audio_scene(video_path, "", negative_prompt, idx, newname=RESULT_DIR / f"scene_{idx:02d}_audio.mp4")
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

def merge_audio_and_video(blocks, audio_path=None, video_path=None, output_path=None):
    """
    Merge TTS audio (scene_XX_voice.wav) into the corresponding video (scene_XX_*.mp4).
    If the video is shorter than the audio, loop the necessary part from the end of the video to match the audio duration.
    If the video has no audio, use only TTS. If it has audio, mix it with TTS.
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
            "[0:a]volume=0.6[a0]; [1:a]volume=1.0[a1]; [a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]",
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
    vids = add_audio_to_scenes(vids, blocks)  # 2. накладываем аудио только звуки scene_{idx:02d}_audio.mp4"
    
    vids = list_files_in_result("scene_*_audio.mp4","result") 

    blocks = translateTextBlocks(blocks, ["ru","ro"])  # 3. переводим текст на английский
    # here we can create different languages
    original_vids = vids.copy()  # Keep original video list
    for language in ["en", "ro", "ru"]:
        burn_subtitles(original_vids, blocks, language)   # 2. накладываем субтитры f"{input_path.stem}_subtitled.mp4"

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
                output_path=RESULT_DIR / f"scene_{idx:02d}_merged_{language}.mp4"
            )
    for language in ["en", "ro", "ru"]:
        vids = list_files_in_result(f"scene_*_merged_{language}.mp4","result") 
        video = combine_videos(vids, f"final_movie_{language}", output_path=Path("result/"))
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP each_audio_scene [{timestamp}]")
    ####generate music
    generated_music = run_text2music(prompt=meta["overall_music"], 
                                     negative_prompt="low quality, noise, static, blurred details, subtitles, paintings, pictures", 
                                     duration=VideoFileClip(str(RESULT_DIR/"final_movie_en.mp4")).duration,
                                     output_name=RESULT_DIR / "final_movie_music.mp4")
    
    for language in ["en", "ro", "ru"]:
        output_path=f"video_output/{sanitize_filename(meta['video_title'])}_{language}"
        merge_audio_and_video(
            blocks=blocks,
            audio_path=RESULT_DIR / "final_movie_music.mp4",
            video_path=RESULT_DIR / f"final_movie_{language}.mp4",
            output_path=f"{output_path}.mp4"
        )
        create_youtube_csv(meta, output_path)
    
    timestamp = datetime.now().strftime('%H:%M')
    print(f"⌛ TIMESTAMP [{timestamp}]")
    for language in ["en", "ro", "ru"]:
        subtitle_file = create_full_subtitles_text(blocks, language)
        subtitle_output = Path("video_output") / f"{sanitize_filename(meta['video_title'])}_{language}.srt"
        shutil.copy(subtitle_file, subtitle_output)
        print(f"📝 Subtitle file saved to: {subtitle_output}")

    #save meta
    # Save meta to video_output directory

    meta_file = video_output_dir / f"{sanitize_filename(meta['video_title'])}.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    clear_vram()
    #############END#############
async def main_test(): 
    meta, blocks = parse_story_blocks((RESULT_DIR / "story.txt").read_text(encoding="utf-8"))
    print(f"Parsed {len(blocks)} scenes.")
    blocks = clean_text_captions(blocks)  # 2. очищаем текст от лишних символов
    blocks = translateTextBlocks(blocks, ["ru","ro"])  # 3. переводим текст на английский
    print("Starting main pipeline...")


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
        run_speecht5_tts(
            language=language,
            gen_text=blk["text"][language],
            output_file=RESULT_DIR / f"scene_{idx:02d}_voice_{language}.wav",
        )
    # output_path = run_f5_tts(
    #     language="ru",
    #     gen_text="Вау! вот это нормер!! я сияна паук+ова и это мой компьютерный голос, я хочу сделать видео с комментарием, как я играю в игру, и это будет очень интересно",
    #     output_file=r"C:\AI\comfyui_automatization\result\output_ru.wav",
    #     ref_audio=r"C:\AI\comfyui_automatization\result_debug\russian_female_1.wav",  # Замени на русский референс
    #     ref_text="Серьезно? Не, я не хочу. У меня вообще это... Ну, жутко интересно, Гент, я волосы закорю, конечно. Так, хорошо. А что можно делать этим станком?"
    # )
    # print(f"Generated audio saved to: {output_path}")

    
if __name__ == "__main__":
    while True:
        asyncio.run(main_production())