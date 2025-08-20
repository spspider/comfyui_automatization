# 🎬 ComfyUI Automatization - AI Video Generation Pipeline

An automated pipeline for generating multilingual YouTube Shorts using AI. This system creates complete videos with text-to-video generation, multilingual TTS, subtitles, and automatic YouTube upload.

## ✨ Features

- 🎥 **AI Video Generation**: Multiple animation styles (Pixar, Studio Ghibli, Disney, etc.)
- 🗣️ **Multilingual TTS**: Support for English, Russian, and Romanian
- 🎵 **AI Music Generation**: Automatic background music creation
- 📝 **Subtitle Generation**: SRT format subtitles for YouTube
- 🌍 **Translation**: Automatic content translation
- 📤 **YouTube Upload**: Direct upload to YouTube with metadata
- 🎨 **Multiple Styles**: 7 different animation styles with consistency

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10 | Required for compatibility |
| CUDA | 11.8+ | For GPU acceleration |
| FFmpeg | Latest | For video processing |
| ComfyUI | Latest | For AI video generation |

### 1. Environment Setup

```bash
# Create conda environment
conda create -n comfyui-auto python=3.10
conda activate comfyui-auto

# Clone repository
git clone <repository-url>
cd comfyui_automatization
```

### 2. PyTorch Installation

**IMPORTANT**: Install PyTorch with CUDA support first:

```bash
# For CUDA 11.8
pip install torch==2.2.0+cu118 torchaudio==2.2.0+cu118 --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch==2.2.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121
```

### 3. Dependencies Installation

```bash
pip install -r requirements.txt
```

### 4. Zonos TTS Setup

**CRITICAL**: For Zonos TTS to work properly:

1. Download the Zonos TTS model
2. Extract the `backbone/` folder
3. Place it in the Zonos installation directory
4. **Without the backbone folder, you'll get "backbone not found" error**

```
zonos-installation-directory/
├── backbone/          # ← This folder is REQUIRED
├── other-files...
```

### 5. Configuration

Create `.env` file:
```env
OPENAI_API_KEY=your_openai_key
YOUTUBE_CLIENT_SECRETS=client_secrets.json
```

## 📋 Installation Guide

### Step-by-Step Installation

| Step | Command | Description |
|------|---------|-------------|
| 1 | `conda create -n comfyui-auto python=3.10` | Create environment |
| 2 | `conda activate comfyui-auto` | Activate environment |
| 3 | `pip install torch==2.2.0+cu118 torchaudio==2.2.0+cu118 --index-url https://download.pytorch.org/whl/cu118` | Install PyTorch |
| 4 | `pip install -r requirements.txt` | Install dependencies |
| 5 | Setup Zonos backbone folder | Place backbone/ in Zonos directory |
| 6 | Configure `.env` file | Add API keys |
| 7 | `python pipeline.py` | Run the pipeline |

## 🎯 Usage

### Basic Usage

```bash
# Run full production pipeline
python pipeline.py

# Run test mode (uses existing story)
# Uncomment main_test() in pipeline.py
```

### Pipeline Stages

1. **Story Generation**: AI creates 30-second video script
2. **Video Generation**: Text-to-video with consistent style
3. **Audio Generation**: Scene-specific sound effects
4. **Translation**: Multi-language support
5. **TTS Generation**: Voice synthesis for each language
6. **Subtitle Burning**: Embedded subtitles
7. **Music Generation**: Background music
8. **Final Assembly**: Complete video creation
9. **YouTube Upload**: Automatic upload with metadata

## 📁 Project Structure

```
comfyui_automatization/
├── pipeline.py              # Main pipeline script
├── utilites/                # Utility modules
│   ├── text2audiof5.py     # F5-TTS integration
│   ├── text2audioZonos.py  # Zonos TTS integration
│   ├── subtitles.py        # Subtitle generation
│   ├── upload_youtube.py   # YouTube upload
│   └── argotranslate.py    # Translation utilities
├── workflow_run/            # ComfyUI workflow runners
├── workflows/               # ComfyUI workflow definitions
├── models/                  # TTS models
├── ref_audio/              # Reference audio files
├── result/                 # Processing results
├── video_output/           # Final videos
└── uploaded_videos/        # Uploaded content archive
```

## ⚙️ Configuration

### Animation Styles

The system randomly selects from 7 animation styles:
- Pixar 3D Animation
- Studio Ghibli Anime
- Disney 2D Animation
- Cartoon Network Style
- Claymation Stop-Motion
- Realistic CGI
- Minimalist Flat Design

### Language Support

| Language | TTS Engine | Status |
|----------|------------|--------|
| English | Zonos | ✅ Active |
| Russian | F5-TTS | ✅ Active |
| Romanian | SpeechT5 | ✅ Active |

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "backbone not found" | Place backbone/ folder in Zonos directory |
| CUDA out of memory | Reduce batch size or use CPU mode |
| Unicode encoding error | Text cleaning function handles this automatically |
| YouTube upload fails | Check client_secrets.json and API quotas |

### Debug Mode

Set `DEBUG = True` in pipeline.py to skip story generation and use existing content.

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Contribution Areas

- 🎨 New animation styles
- 🌍 Additional language support
- 🎵 Music generation improvements
- 🔧 Performance optimizations
- 📚 Documentation improvements

### Code Standards

- Follow PEP 8 style guidelines
- Add docstrings to functions
- Include type hints where possible
- Write tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Terms of Use

- ✅ **Commercial use** allowed
- ✅ **Modification** allowed
- ✅ **Distribution** allowed
- ✅ **Private use** allowed
- ❗ **License and copyright notice** required

## 💖 Support the Project

If this project helps you create amazing content, consider supporting its development:

### Donation Options

| Platform | Link | Description |
|----------|------|-------------|
| 💳 **PayPal** | [Donate via PayPal](https://paypal.me/yourpaypal) | One-time or recurring |
| ☕ **Buy Me a Coffee** | [buymeacoffee.com/yourname](https://buymeacoffee.com/yourname) | Support with coffee |
| 🪙 **Crypto** | `your-crypto-address` | Bitcoin/Ethereum |
| 💎 **GitHub Sponsors** | [Sponsor on GitHub](https://github.com/sponsors/yourusername) | Monthly sponsorship |

### Why Donate?

- 🚀 **Accelerate development** of new features
- 🐛 **Faster bug fixes** and improvements
- 📚 **Better documentation** and tutorials
- 🎯 **Priority support** for donors
- 🌟 **New AI models** integration

## 📊 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11, Linux, macOS |
| RAM | 16GB |
| GPU | NVIDIA GTX 1060 6GB |
| Storage | 50GB free space |
| Internet | Stable connection for API calls |

### Recommended Requirements

| Component | Requirement |
|-----------|-------------|
| RAM | 32GB+ |
| GPU | NVIDIA RTX 3080+ |
| Storage | 100GB+ SSD |
| CPU | 8+ cores |

## 🔗 Related Projects

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - AI image/video generation
- [F5-TTS](https://github.com/SWivid/F5-TTS) - Russian TTS
- [Zonos TTS](https://github.com/zonos/tts) - Multilingual TTS

## 📞 Support

- 📧 **Email**: your-email@example.com
- 💬 **Discord**: [Join our server](https://discord.gg/yourserver)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/repo/issues)
- 📖 **Wiki**: [Project Wiki](https://github.com/yourusername/repo/wiki)

---

⭐ **Star this repository** if it helped you create amazing AI videos!

Made with ❤️ by [Your Name]