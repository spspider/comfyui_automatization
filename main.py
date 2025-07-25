# main.py
import argparse
from lmstudio_api import describe_image
from video2audio_workflow import run_video2audio

def main():
    parser = argparse.ArgumentParser(description="Main pipeline controller")
    parser.add_argument("--image", type=str, help="Path to image to describe", default="gen/input.jpeg")
    parser.add_argument("--image2video", type=str, help="Path to image to transform into video", default="gen/input.jpeg")
    parser.add_argument("--video", type=str, help="Path to video to transform", default="inputs/fluffy.mp4")
    parser.add_argument("--describe", action="store_true", help="Run image description first")
    parser.add_argument("--run", action="store_true", help="Run video2audio generation")
    args = parser.parse_args()

    if args.describe:
        print(f"🧠 Описание изображения {args.image} через LM Studio...")
        description = describe_image(args.image)
        print("\n📜 Получено описание:")
        print(description)
    else:
        description = "A dreamy anime atmosphere with glowing particles"

    if args.run:
        print(f"\n🎬 Генерация видео с описанием: {description}")
        run_video2audio(video_path=args.video, prompt=description, negative_prompt="low quality, distortion")

    
if __name__ == "__main__":
    main()
