import sys

sys.path.append(r"C:\AI\Zonos-for-windows\.venv\Lib\site-packages")
import torch
import torchaudio
import random
sys.path.append(r"C:\AI\Zonos-for-windows")

from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from zonos.utils import DEFAULT_DEVICE as device


def generate_audio_from_text(
    text,
    speaker_audio_path=None,
    language="en-us",
    output_path="sample.wav",
    cfg_scale=4.47,
    fmax=24000,
    pitch_std=113,
    speaking_rate=15.0,
    seed=1829951755, #1637827792 - man, 1829951755 - woman
    randomize_seed=False,
    emotions=[1.0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.2],
    unconditional_keys=["emotion",  "pitch_std"]
):
    print("📦 Loading Zonos model...")
    model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-transformer", device=device)

    # Handle seed
    if randomize_seed:
        seed = random.randint(0, 2**32 - 1)
        print(f"🎲 Random seed generated: {seed}")
    else:
        print(f"🔢 Using provided seed: {seed}")
    torch.manual_seed(seed)

    # Speaker embedding (optional)
    speaker = None
    if speaker_audio_path:
        print(f"👤 Using speaker audio: {speaker_audio_path}")
        wav, sr = torchaudio.load(speaker_audio_path)
        speaker = model.make_speaker_embedding(wav, sr).to(device)
    else:
        print("⚠️ No speaker audio provided. Using default voice.")

    # Emotion tensor
    emotion_tensor = torch.tensor(emotions, device=device)

    # Create conditioning dictionary
    cond_dict = make_cond_dict(
        text=text,
        speaker=speaker,
        language=language,
        emotion=emotion_tensor,
        fmax=fmax,
        pitch_std=pitch_std,
        speaking_rate=speaking_rate,
        unconditional_keys=unconditional_keys
    )
    conditioning = model.prepare_conditioning(cond_dict)

    print("🎙️ Generating audio codes...")
    codes = model.generate(
        prefix_conditioning=conditioning,
        cfg_scale=cfg_scale,
        batch_size=1
    )

    print(f"💾 Saving audio to {output_path}...")
    wavs = model.autoencoder.decode(codes).cpu()
    torchaudio.save(output_path, wavs[0], model.autoencoder.sampling_rate)
    print("✅ Generation complete.")
    return seed


if __name__ == "__main__":
    generate_audio_from_text(
        text="WOW!! This is a Zonos voice synthesis test with emotion and CFG scaling!.",
        speaker_audio_path=None,  # or provide a path to an actual voice clone file
        language="en-us",
        output_path="output.wav",
        randomize_seed=False,
        cfg_scale=4.47,
        fmax=24000,
        pitch_std=113,
        speaking_rate=15.0,
        seed=1829951755,
        emotions=[1.0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.2],
        unconditional_keys=["emotion",  "pitch_std"]
    )
