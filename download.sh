#!/bin/bash
huggingface-cli download ionut-visan/SpeechT5_ro --local-dir C:/AI/comfyui_automatization/models/SpeechT5_ro --local-dir-use-symlinks False

conda activate f5-tts
pip install -r /c/AI/comfyui_automatization/utilites/requirements.txt
pip install git+https://github.com/Zyphra/Zonos.git