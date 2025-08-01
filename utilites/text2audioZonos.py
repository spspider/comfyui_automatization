import argparse
import os
import torch
import torchaudio
from zonos.model import Zonos
from zonos.conditioning import make_cond_dict, supported_language_codes
from zonos.utils import DEFAULT_DEVICE as device

def parse_args():
    parser = argparse.ArgumentParser(description="Generate audio using Zonos model")
    parser.add_argument("--model", default="Zyphra/Zonos-v0.1-transformer", choices=["Zyphra/Zonos-v0.1-transformer", "Zyphra/Zonos-v0.1-hybrid"], help="Zonos model type")
    parser.add_argument("--text", default="Hello, this is a test audio!", help="Text to synthesize")
    parser.add_argument("--language", default="en-us", choices=supported_language_codes, help="Language code")
    parser.add_argument("--speaker_audio", default=None, help="Path to speaker audio file for cloning")
    parser.add_argument("--prefix_audio", default=None, help="Path to prefix audio file to continue from")
    parser.add_argument("--output", default="output.wav", help="Output audio file path")
    parser.add_argument("--emotion", nargs=8, type=float, default=[1.0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.2], help="Emotion values (8 floats for Happiness, Sadness, Disgust, Fear, Surprise, Anger, Other, Neutral)")
    parser.add_argument("--vq_score", type=float, default=0.78, help="VQ score value")
    parser.add_argument("--fmax", type=float, default=24000.0, help="Fmax value (Hz)")
    parser.add_argument("--pitch_std", type=float, default=45.0, help="Pitch standard deviation")
    parser.add_argument("--speaking_rate", type=float, default=15.0, help="Speaking rate")
    parser.add_argument("--dnsmos_ovrl", type=float, default=4.0, help="DNSMOS overall score")
    parser.add_argument("--speaker_noised", action="store_true", help="Denoise speaker audio")
    parser.add_argument("--cfg_scale", type=float, default=2.0, help="CFG scale")
    parser.add_argument("--top_p", type=float, default=0.0, help="Top P sampling")
    parser.add_argument("--top_k", type=int, default=0, help="Top K sampling")
    parser.add_argument("--min_p", type=float, default=0.0, help="Min P sampling")
    parser.add_argument("--linear", type=float, default=0.5, help="Linear sampling parameter")
    parser.add_argument("--confidence", type=float, default=0.4, help="Confidence sampling parameter")
    parser.add_argument("--quadratic", type=float, default=0.0, help="Quadratic sampling parameter")
    parser.add_argument("--seed", type=int, default=420, help="Random seed")
    parser.add_argument("--randomize_seed", action="store_true", help="Randomize seed before generation")
    parser.add_argument("--unconditional_keys", nargs="*", default=["emotion"], choices=["speaker", "emotion", "vqscore_8", "fmax", "pitch_std", "speaking_rate", "dnsmos_ovrl", "speaker_noised"], help="Unconditional keys to ignore")
    return parser.parse_args()

def main():
    args = parse_args()

    # Установите переменные окружения (как в вашем оригинальном скрипте)
    os.environ["HF_HOME"] = os.path.join(os.getcwd(), "huggingface")
    os.environ["TORCH_HOME"] = os.path.join(os.getcwd(), "torch")
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "C:\\Program Files\\eSpeak NG\\libespeak-ng.dll"

    # Загрузка модели
    print(f"Loading {args.model} model...")
    model = Zonos.from_pretrained(args.model, device=device)
    model.requires_grad_(False).eval()
    print(f"{args.model} model loaded successfully!")

    # Установка seed
    if args.randomize_seed:
        args.seed = torch.randint(0, 2**32 - 1, (1,)).item()
    torch.manual_seed(args.seed)
    print(f"Using seed: {args.seed}")

    # Подготовка спикера (если указан)
    speaker_embedding = None
    if args.speaker_audio and "speaker" not in args.unconditional_keys:
        print("Computing speaker embedding...")
        wav, sr = torchaudio.load(args.speaker_audio)
        speaker_embedding = model.make_speaker_embedding(wav, sr)
        speaker_embedding = speaker_embedding.to(device, dtype=torch.bfloat16)

    # Подготовка префиксного аудио (если указано)
    audio_prefix_codes = None
    if args.prefix_audio:
        print("Processing prefix audio...")
        wav_prefix, sr_prefix = torchaudio.load(args.prefix_audio)
        wav_prefix = wav_prefix.mean(0, keepdim=True)
        wav_prefix = model.autoencoder.preprocess(wav_prefix, sr_prefix)
        wav_prefix = wav_prefix.to(device, dtype=torch.float32)
        audio_prefix_codes = model.autoencoder.encode(wav_prefix.unsqueeze(0))

    # Подготовка эмоций
    emotion_tensor = torch.tensor(args.emotion, device=device)

    # Подготовка VQ score
    vq_tensor = torch.tensor([args.vq_score] * 8, device=device).unsqueeze(0)

    # Формирование словаря кондиционеров
    cond_dict = make_cond_dict(
        text=args.text,
        language=args.language,
        speaker=speaker_embedding,
        emotion=emotion_tensor,
        vqscore_8=vq_tensor,
        fmax=args.fmax,
        pitch_std=args.pitch_std,
        speaking_rate=args.speaking_rate,
        dnsmos_ovrl=args.dnsmos_ovrl,
        speaker_noised=args.speaker_noised,
        device=device,
        unconditional_keys=args.unconditional_keys,
    )
    conditioning = model.prepare_conditioning(cond_dict)

    # Параметры генерации
    max_new_tokens = 86 * 30
    sampling_params = {
        "top_p": args.top_p,
        "top_k": args.top_k,
        "min_p": args.min_p,
        "linear": args.linear,
        "conf": args.confidence,
        "quad": args.quadratic,
    }

    # Генерация аудио
    print("Generating audio...")
    codes = model.generate(
        prefix_conditioning=conditioning,
        audio_prefix_codes=audio_prefix_codes,
        max_new_tokens=max_new_tokens,
        cfg_scale=args.cfg_scale,
        batch_size=1,
        sampling_params=sampling_params,
        disable_torch_compile=True if "transformer" in args.model else False,
    )

    # Декодирование и сохранение аудио
    print(f"Saving audio to {args.output}...")
    wav_out = model.autoencoder.decode(codes).cpu().detach()
    sr_out = model.autoencoder.sampling_rate
    if wav_out.dim() == 2 and wav_out.size(0) > 1:
        wav_out = wav_out[0:1, :]
    torchaudio.save(args.output, wav_out.squeeze(0), sr_out)

    print("Done!")

if __name__ == "__main__":
    main()