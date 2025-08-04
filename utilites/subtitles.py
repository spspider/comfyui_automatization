from pathlib import Path
import subprocess
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import pysrt

RESULT_DIR = Path(r"C:/AI/comfyui_automatization/result")

################ Subtitles

def format_time(seconds):
    """Преобразует секунды в формат SRT (часы:минуты:секунды,миллисекунды)"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02},000"

def generate_subtitles(blocks):
    """
    Создаёт .srt-файлы для каждой сцены на основе текста из blocks[i]["text"]
    и длительности blocks[i]["duration"]
    """
    for idx, block in enumerate(blocks, 1):
        start_seconds = 0
        end_seconds = block["duration"]

        subtitle_text = block["text"].strip().replace('\n', ' ')

        srt_content = f"""1
{format_time(start_seconds)} --> {format_time(end_seconds)}
{subtitle_text}
"""

        srt_path = RESULT_DIR / f"scene_{idx:02d}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"📝 Субтитры для сцены {idx} сохранены в: {srt_path}")

def ffmpeg_safe_path(path: Path):
    return str(path).replace('\\', '/').replace(':', '\\:')

def burn_subtitles(video_paths, blocks):
    generate_subtitles(blocks)
    ffmpeg = "c:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe"
    subtitled_paths = []

    for idx, video_path in enumerate(video_paths, 1):
        input_path = Path(video_path)
        srt_path = RESULT_DIR / f"scene_{idx:02d}.srt"
        output_path = RESULT_DIR / f"{input_path.stem}_subtitled.mp4"

        cmd = [
            ffmpeg,
            "-y",
            "-i", str(input_path),
            "-vf", f"subtitles='{ffmpeg_safe_path(srt_path)}'",
            "-c:a", "copy",
            str(output_path)
        ]
        print(f"🔤 Накладываем субтитры на {input_path.name} → {output_path.name}", cmd)
        try:
            subprocess.run(cmd, check=True)
            subtitled_paths.append(str(output_path))
            print(f"✅ Subtitles burned into: {output_path.name}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to burn subtitles into: {input_path.name}")
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
