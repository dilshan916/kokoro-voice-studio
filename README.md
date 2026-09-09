# 🎙️ Kokoro Voice Studio (SayTTS)

<div align="center">

[![Live Demo](https://img.shields.io/badge/Live%20Demo-saytts.site-00e599?style=for-the-badge&logo=googlechrome&logoColor=white)](https://saytts.site)
[![Model](https://img.shields.io/badge/Model-Kokoro--82M%20ONNX-3b82f6?style=for-the-badge&logo=onnx&logoColor=white)](https://huggingface.co/hexgrad/Kokoro-82M)
[![Voices](https://img.shields.io/badge/Voices-60%2B%20Studio%20Neural-8b5cf6?style=for-the-badge)](#-supported-languages--voices)
[![Lighthouse Accessibility](https://img.shields.io/badge/Accessibility-100%2F100-success?style=for-the-badge)](https://pagespeed.web.dev/analysis?url=https%3A%2F%2Fsaytts.site%2F)
[![Mobile App](https://img.shields.io/badge/Android%20APK-v1.0.0-ff6b00?style=for-the-badge&logo=android&logoColor=white)](https://github.com/dilshan916/kokoro-mobile/releases/download/v1.0.0/kokoro-voice-studio-v1.0.0-universal.apk)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

### **Next-Generation, Studio-Grade Neural Text-to-Speech Platform**
*Synthesize ultra-realistic, natural voiceovers directly in your browser or self-host with Docker. Zero login required.*

### 🔗 **[Try the Live Web App: https://saytts.site](https://saytts.site)**

</div>

---

## 🌟 Overview

**Kokoro Voice Studio (SayTTS)** is an open-source, studio-grade Text-to-Speech (TTS) workstation powered by the state-of-the-art **Kokoro-82M ONNX** neural model and an advanced **Multilingual G2P (Grapheme-to-Phoneme)** phonetic engine.

Designed for content creators, video editors, podcasters, and developers, SayTTS delivers broadcast-quality human speech faster than real-time on standard CPUs without requiring expensive GPUs or third-party cloud API tokens.

### 🚀 Why SayTTS?
* 🌐 **Instant Live Web Access**: Use it immediately at **[saytts.site](https://saytts.site)** — no credit card, no registration, no waitlists.
* ⚡ **Ultra-Fast CPU Inference**: Synthesizes speech in under 200 milliseconds using lightweight 82M parameter ONNX quantization.
* 🎙️ **60+ Character & Regional Voices**: Rich emotional inflections across 9+ languages (English, French, Japanese, Korean, Mandarin, Spanish, Hindi, Italian, and Portuguese).
* 🎛️ **Studio Mastering Engine**: 6 professional acoustic EQ presets (Warm Studio, Podcast Punch, Air & Presence, Bass Boost, Broadcast Pro, Crisp Vocal).
* 📜 **Synced Subtitles (SRT & VTT)**: Exports frame-accurate subtitle files matched with synthesized audio for direct drag-and-drop into CapCut, Adobe Premiere, DaVinci Resolve, and Final Cut Pro.
* 🎚️ **Neural Voice Blender**: Morph and interpolate between two voices with fine-grained weight controls to create entirely unique vocal timbres.
* 🎭 **Multi-Speaker Dialogue Scripting**: Direct multi-character dramatic conversations with automated per-line speaker switches and customizable inter-dialogue pauses.
* 📱 **Mobile & PWA Ready**: Install as a progressive web app or download the native Android APK.

---

## 🌍 Supported Languages & Voices

| Flag | Language / Accent | Code | Voices | Sample Personalities & Characters |
| :---: | :--- | :---: | :---: | :--- |
| 🇺🇸 | **English (US)** | `en-us` | **20 voices** | Bella, Adam, Heart, Echo, Nicole, Sarah, Sky, Michael, Emma, Santa |
| 🇬🇧 | **English (UK)** | `en-gb` | **8 voices** | George, Lewis, Emma, Daniel, Alice, Isabella, Lily, Fable |
| 🇫🇷 | **French** | `fr-fr` | **5 voices** | Siwis, Alexandre, Lucas, Camille, Juliette |
| 🇯🇵 | **Japanese** | `ja` | **5 voices** | Alpha (アルファ), Gongitsune, Nezumi, Kumo, Sora |
| 🇰🇷 | **Korean** | `ko` | **2 voices** | Minji (민지), Junho (준호) |
| 🇨🇳 | **Mandarin Chinese** | `cmn` | **8 voices** | Xiaobei (小北), Xiaoxiao (小小), Yunxi (云希), Yunjian |
| 🇪🇸 | **Spanish** | `es` | **3 voices** | Dora, Alex, Papá Noel |
| 🇮🇳 | **Hindi** | `hi` | **4 voices** | Alpha (अल्फा), Beta, Omega, Psi |
| 🇮🇹 | **Italian** | `it` | **2 voices** | Sara, Nicola |
| 🇧🇷 | **Portuguese (BR)** | `pt-br` | **3 voices** | Dora (BR), Alex (BR), Papai Noel |

---

## 🖥️ Live Web App vs Self-Hosted

| Feature | Live Web App ([saytts.site](https://saytts.site)) | Self-Hosted / Docker | Desktop App (Local) |
| :--- | :---: | :---: | :---: |
| **Setup Time** | Instant (0 sec) | 2 minutes | 3 minutes |
| **Hardware Required** | Any browser / phone | Any x86_64 / ARM server | Local Windows / Linux / macOS PC |
| **GPU Required** | No | No (CPU-accelerated) | No |
| **Offline Support** | No (Cloud CDN) | Intranet / Localhost | 100% Offline |
| **API Endpoint** | Optional | Full REST API | CLI / Local GUI |
| **Mastering EQ** | Included | Included | Included |
| **SRT Subtitles** | Included | Included | Included |

---

## 🚀 Quick Start & Installation

### Option 1: Live Web Application
Visit **[https://saytts.site](https://saytts.site)** directly in your browser.

---

### Option 2: Docker Deployment (Recommended for Servers)

Run Kokoro Voice Studio on any Linux VPS or server with a single Docker command:

```bash
# Clone the repository
git clone https://github.com/dilshan916/kokoro-voice-studio.git
cd kokoro-voice-studio

# Build and run with Docker
docker build -t kokoro-voice-studio .
docker run -d -p 8000:8000 --name saytts kokoro-voice-studio
```

Open `http://localhost:8000` in your browser. The Docker container automatically downloads the ONNX model weights and voice dictionaries on first boot.

---

### Option 3: Local Python & Frontend Development

#### 1. Prerequisites
* **Python 3.10+**
* **Node.js 18+** & `npm`
* **eSpeak-NG** (for international phonemization)
  * Windows: `winget install espeak-ng` or download MSI installer
  * Ubuntu / Debian: `sudo apt-get install -y espeak-ng`
  * macOS: `brew install espeak-ng`

#### 2. Backend Setup
```bash
# Clone repository
git clone https://github.com/dilshan916/kokoro-voice-studio.git
cd kokoro-voice-studio

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI audio synthesis backend
python server.py
```
*The backend automatically downloads the ONNX model files from GitHub releases if not present locally.*

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to access the hot-reloading development workspace.

---

## 🔌 REST API Integration

SayTTS exposes high-throughput, OpenAI-compatible and native REST endpoints:

### Endpoint: `POST /v1/audio/speech` or `POST /api/tts`

#### Example `curl` Request:
```bash
curl -X POST https://saytts.site/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello! Welcome to Kokoro Voice Studio, powered by SayTTS.",
    "voice": "af_bella",
    "speed": 1.0,
    "response_format": "mp3"
  }' \
  --output voiceover.mp3
```

#### Example Python Request:
```python
import requests

url = "https://saytts.site/v1/audio/speech"
payload = {
    "input": "Kokoro Voice Studio delivers natural speech with zero latency.",
    "voice": "am_adam",
    "speed": 1.05,
    "response_format": "mp3"
}

response = requests.post(url, json=payload)
with open("speech.mp3", "wb") as f:
    f.write(response.content)
```

---

## 🛠️ Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│              Modern React 18 + Vite Frontend            │
│    (Tailwind CSS • Lucide Icons • Web Audio API Scrubber)│
└────────────────────────────┬────────────────────────────┘
                             │ REST / WebSocket
┌────────────────────────────▼────────────────────────────┐
│                  FastAPI Backend Server                 │
├────────────────────────────┬────────────────────────────┤
│   Multilingual G2P Engine  │     Audio Mastering EQ     │
│  (eSpeak-NG • langdetect)  │  (Pydub • Pygame • Scipy)  │
├────────────────────────────┴────────────────────────────┤
│            Kokoro-82M ONNX Inference Engine             │
│       (Int8 Quantization • Threaded Memory Arena)       │
└─────────────────────────────────────────────────────────┘
```

* **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, HTML5 Web Audio API.
* **Backend**: FastAPI, Uvicorn, Pydantic, Python 3.12.
* **Inference Engine**: ONNX Runtime with Kokoro-82M lightweight neural weights.
* **Acoustics & DSP**: Pydub, Scipy digital biquad filter bands, automated SRT word aligner.

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

### Acknowledgments & Credits
* Model architecture & weights: **[Hexgrad Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)**
* ONNX Runtime Engine: **[thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)**
* Built & Maintained by: **[Dilshan Chandrarathne](https://github.com/dilshan916)**

