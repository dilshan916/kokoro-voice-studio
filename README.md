# 🎙️ Kokoro Voice Studio Pro

A modern, studio-grade desktop Text-to-Speech application running 100% offline on your PC, powered by **Kokoro-82M ONNX** and an advanced **Multilingual G2P Preprocessor**.

---

## ✨ Key Features

* **⚡ Ultra-Fast CPU Inference**: Synthesizes speech faster than real-time on any standard laptop or PC without needing a dedicated GPU.
* **🌐 Multilingual G2P & Auto Language Detection**: Seamlessly processes text in 9+ international languages with script-aware phonemization (preserving accents, CJK ideographs, Hangul, and Devanagari).
* **🎙️ 60 Studio-Grade Voices**: High-retention character voices across English (US & UK), French, Japanese, Korean, Mandarin Chinese, Spanish, Hindi, Italian, Portuguese, and German.
* **🎛️ Neural Voice Blender**: Dynamically mix two voices with precise interpolation ratios to create unique character timbres.
* **🎭 Multi-Speaker Drama Studio**: Automatically parses character dialog formats (`[Bella (fr)]: Bonjour! \n [Adam (en)]: Hello!`) and weaves multi-voice conversations with customizable pauses.
* **🎵 In-App Live Audio Player**: Listen, pause, seek, and adjust volume directly inside the app with zero file hunting.
* **📜 Synchronized Subtitle Generator**: Export `.srt` and `.vtt` subtitles aligned with generated speech for CapCut, Premiere, and DaVinci Resolve.
* **📂 Batch File Converter**: Queue up `.txt` documents, articles, or book chapters and convert them into organized audio tracks.
* **💾 Multi-Format Export**: Save as `.mp3`, `.wav`, or `.ogg` with studio-grade acoustic EQ presets.

---

## 🌍 Supported Languages & International Voices

| Flag | Language / Accent | Language Code | Available Voices | Sample Characters |
| :--- | :--- | :--- | :--- | :--- |
| 🇺🇸 | **English (US)** | `en-us` | **20 voices** | Bella, Adam, Heart, Echo, Nicole, Sarah, Sky |
| 🇬🇧 | **English (UK)** | `en-gb` | **8 voices** | George, Lewis, Emma, Daniel, Alice, Isabella |
| 🇫🇷 | **French** | `fr-fr` | **5 voices** | Siwis, Alexandre, Lucas, Camille, Juliette |
| 🇯🇵 | **Japanese** | `ja` | **5 voices** | Alpha (アルファ), Gongitsune, Nezumi, Kumo |
| 🇰🇷 | **Korean** | `ko` | **2 voices** | Minji (민지), Junho (준호) |
| 🇨🇳 | **Mandarin Chinese** | `cmn` | **8 voices** | Xiaobei (小北), Xiaoxiao (小小), Yunxi (云希) |
| 🇪🇸 | **Spanish** | `es` | **3 voices** | Dora, Alex, Papá Noel |
| 🇮🇳 | **Hindi** | `hi` | **4 voices** | Alpha (अल्फा), Beta, Omega, Psi |
| 🇮🇹 | **Italian** | `it` | **2 voices** | Sara, Nicola |
| 🇧🇷 | **Portuguese (BR)** | `pt-br` | **3 voices** | Dora (BR), Alex (BR), Papai Noel |

---

## 🚀 Quick Start

### 1. Launch the Desktop App:
Double-click **`run.bat`** (or open a terminal and run `python app.py`).

### 2. Package as a Portable Windows EXE:
Double-click **`build_exe.bat`**. The standalone executable and installer will be generated in `dist/`.

---

## 💻 Tech Stack
* **UI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Dark-mode responsive desktop window)
* **Audio Engine**: [Kokoro-ONNX](https://github.com/thewh1teagle/kokoro-onnx) (82M parameter lightweight TTS)
* **G2P & Phonetization**: Multilingual G2P + [eSpeak-NG](https://github.com/espeak-ng/espeak-ng) + [langdetect](https://github.com/Mimino666/langdetect)
* **Audio Processing**: Pygame & Pydub
