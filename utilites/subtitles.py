from pathlib import Path
import subprocess
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import pysrt

RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")

################ Subtitles

def format_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def generate_subtitles(blocks, lang=None):
    """
    Generate .srt files for each scene based on text and duration from blocks.
    """
    for idx, block in enumerate(blocks, 1):
        start_seconds = 0
        end_seconds = block["duration"]
        subtitle_text = block["text"][lang].strip().replace('\n', ' ') if lang else block["text"].strip().replace('\n', ' ')

        srt_content = f"""1
{format_time(start_seconds)} --> {format_time(end_seconds)}
{subtitle_text}
"""
        srt_path = RESULT_DIR / f"scene_{idx:02d}_{lang}.srt"
        try:
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            print(f"📝 Субтитры для сцены {idx} ({lang}) сохранены в: {srt_path}")
        except Exception as e:
            print(f"❌ Failed to write SRT file {srt_path}: {e}")
    return True

def ffmpeg_safe_path(path: Path):
    return str(path.relative_to(Path.cwd())).replace('\\', '/')

def burn_subtitles(video_paths, blocks, lang="en"):
    """
    Burn subtitles into videos using FFmpeg.
    """
    ffmpeg = r"c:\ProgramData\chocolatey\bin\ffmpeg.exe"
    subtitled_paths = []
    
    # Ensure the result directory exists
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate subtitles
    if not generate_subtitles(blocks, lang):
        print("⚠️ Subtitle generation failed, proceeding without subtitles")
        return video_paths

    for idx, video_path in enumerate(video_paths, 1):
        input_path = Path(video_path)
        srt_path = RESULT_DIR / f"scene_{idx:02d}_{lang}.srt"
        # clean_stem = input_path.stem.split('_subtitled_')[0]
        output_path = RESULT_DIR / f"{input_path.stem}_subtitled_{lang}.mp4"
        
        # Check if input video and SRT file exist
        if not input_path.exists():
            print(f"⚠️ Input video not found: {input_path}, skipping")
            subtitled_paths.append(str(input_path))
            continue
        if not srt_path.exists():
            print(f"⚠️ SRT file not found: {srt_path}, skipping subtitles for {input_path.name}")
            subtitled_paths.append(str(input_path))
            continue
        
        # Properly escape SRT path for FFmpeg
        escaped_srt = str(srt_path).replace("\\", "/").replace(":", "\\:")
        vf_filter = f"subtitles='{escaped_srt}':force_style='Fontsize=12,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=1,Shadow=0'"
        
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(input_path),
            "-vf", vf_filter,
            "-c:a", "copy",
            str(output_path)
        ]
        print(f"🔤 Накладываем субтитры на {input_path.name} → {output_path.name}: {cmd}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            subtitled_paths.append(str(output_path))
            print(f"✅ Subtitles burned into: {output_path.name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to burn subtitles into: {input_path.name}")
            print(f"Error: {e.stderr}")
            subtitled_paths.append(str(input_path))

    return subtitled_paths
def create_full_subtitles(blocks):
    """
    Creates full subtitles txt file from blocks, where duration and scenes, so it adds subtitles to the video.
    """
    full_subtitles = []
    for idx, block in enumerate(blocks, 1):
        start_seconds = sum(b["duration"] for b in blocks[:idx-1])
        end_seconds = start_seconds + block["duration"]
        subtitle_text = block["text"].strip().replace('\n', ' ')
        full_subtitles.append(f"{format_time(start_seconds)} --> {format_time(end_seconds)}\n{subtitle_text}\n")

    full_srt_path = RESULT_DIR / "full_subtitles.srt"
    with open(full_srt_path, "w", encoding="utf-8") as f:
        f.writelines(full_subtitles)
    print(f"📝 Полные субтитры сохранены в: {full_srt_path}")
    return full_srt_path
def create_full_subtitles_text(blocks, lang="en"):
    """
    Creates full subtitles SRT file from blocks with proper timecodes for YouTube.
    """
    srt_content = []
    current_time = 0.0
    
    for idx, block in enumerate(blocks, 1):
        # Handle both string and dictionary text formats
        if isinstance(block["text"], dict):
            subtitle_text = block["text"][lang].strip().replace('\n', ' ')
        else:
            subtitle_text = block["text"].strip().replace('\n', ' ')
        
        start_time = current_time
        end_time = current_time + block.get("duration", 5.0)  # Default 5 seconds if no duration
        
        # Add SRT entry
        srt_content.append(f"{idx}")
        srt_content.append(f"{format_time(start_time)} --> {format_time(end_time)}")
        srt_content.append(subtitle_text)
        srt_content.append("")  # Empty line between entries
        
        current_time = end_time

    full_srt_path = RESULT_DIR / f"full_subtitles_{lang}.srt"
    with open(full_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))
    print(f"📝 Full SRT subtitles saved to: {full_srt_path}")
    return full_srt_path
def create_video_with_subtitles(video_path, audio_path, subtitle_path, output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    subtitles = pysrt.open(subtitle_path)

    subtitle_clips = []
    for sub in subtitles:
        txt = sub.text.replace("\n", " ")
        start = sub.start.to_time()
        end = sub.end.to_time()

        txt_clip = (TextClip(txt, fontsize=48, color='white', stroke_color='black', stroke_width=2, font='Arial-Bold')
                    .set_position(('center', 'bottom'))
                    .set_start(start.total_seconds())
                    .set_duration((end - start).total_seconds()))
        subtitle_clips.append(txt_clip)

    final = CompositeVideoClip([video] + subtitle_clips)
    # final = final.with_audio(audio)
    final.write_videofile(output_path, codec='libx264', audio_codec='aac')

def clean_text_captions(blocks):
    """Clean text blocks to keep only English characters and basic punctuation."""
    import re
    
    for block in blocks:
        text = block['text']
        
        # Replace accented characters with basic equivalents
        text = re.sub(r'[áàäâ]', 'a', text)
        text = re.sub(r'[éèëê]', 'e', text)
        text = re.sub(r'[íìïî]', 'i', text)
        text = re.sub(r'[óòöô]', 'o', text)
        text = re.sub(r'[úùüû]', 'u', text)
        text = re.sub(r'[ñ]', 'n', text)
        text = re.sub(r'[ç]', 'c', text)
        
        # Keep only English letters, numbers, spaces, and basic punctuation
        cleaned = re.sub(r'[^a-zA-Z0-9\s.,!?;:]', '', text)
        
        # Remove extra whitespace
        block['text'] = re.sub(r'\s+', ' ', cleaned).strip()
    
    return blocks

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