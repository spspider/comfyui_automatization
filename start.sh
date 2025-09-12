#!/bin/bash
clear

# Prevent system sleep while script runs
powercfg -change -standby-timeout-ac 0
powercfg -change -hibernate-timeout-ac 0

# Initialize Conda for bash
source ~/miniconda3/etc/profile.d/conda.sh

# Activate your environment
conda activate f5-tts

# Run your Python script
python /c/AI/comfyui_automatization/pipeline.py

# Restore original sleep settings when script ends
powercfg -restoredefaultschemes

