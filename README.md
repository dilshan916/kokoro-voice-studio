# 🎙️ Kokoro Voice Studio

A modern, studio-grade desktop Text-to-Speech application running 100% offline on your PC, powered by **Kokoro-82M ONNX**.

---

## ✨ Key Features

* **⚡ Ultra-Fast CPU Inference**: Synthesizes speech faster than real-time on any standard laptop or PC without needing a dedicated GPU.
* **👩‍🦰 11 Studio-Grade Voices**: High-retention narration styles covering American and British accents with natural emotion and cadence.
* **🎭 Multi-Speaker Drama Studio**: Automatically parses character dialog formats (`[Adam]: ... \n [Bella]: ...`) and weaves multi-voice conversations with customizable pauses.
* **🎵 In-App Live Audio Player**: Listen, pause, seek, and adjust volume directly inside the app with zero file hunting.
* **📜 Synchronized Subtitle Generator**: Export `.srt` and `.vtt` subtitles aligned with generated speech for CapCut, Premiere, and DaVinci Resolve.
* **📂 Batch File Converter**: Queue up `.txt` documents, articles, or book chapters and convert them into organized audio tracks.
* **💾 Multi-Format Export**: Save as `.mp3`, `.wav`, or `.ogg` with customizable bitrates.

---

## 🚀 Quick Start

### 1. Launch the Desktop App:
Double-click **`run.bat`** (or open a terminal and run `python app.py`).

### 2. Package as a Portable Windows EXE:
Double-click **`build_exe.bat`**. The standalone executable will be generated inside `dist/KokoroVoiceStudio/KokoroVoiceStudio.exe`.

---

## 🎙️ Included Voice Library

| Voice Key | Character | Accent | Gender | Best For |
| :--- | :--- | :--- | :--- | :--- |
| `af_bella` | Bella | American | Female | High-retention drama & viral voiceovers |
| `am_adam` | Adam | American | Male | Deep podcast & authoritative narration |
| `bm_george` | George | British | Male | Distinguished & documentary storytelling |
| `af_nicole` | Nicole | American | Female | Calm, thoughtful audiobook narrations |
| `af_sky` | Sky | American | Female | Bright, conversational, youthful dialogue |
| `am_michael`| Michael | American | Male | Friendly, clean studio voiceover |
| `bf_emma` | Emma | British | Female | Sophisticated, crisp presentation |
| `bf_isabella`| Isabella | British | Female | Soft, gentle, relaxed reading |
| `bm_lewis` | Lewis | British | Male | Articulate BBC documentary tone |
| `am_puck` | Puck | American | Male | Energetic, upbeat pacing |
| `af_sarah` | Sarah | American | Female | Everyday conversational warmth |

---

## 💻 Tech Stack
* **UI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Dark-mode responsive desktop window)
* **Audio Engine**: [Kokoro-ONNX](https://github.com/thewh1teagle/kokoro-onnx) (82M parameter lightweight TTS)
* **Audio Processing**: Pygame & Pydub
