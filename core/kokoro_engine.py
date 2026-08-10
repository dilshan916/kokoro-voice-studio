"""
Kokoro Studio — Multilingual Kokoro TTS Engine (v1.0 / 50+ Voices)
==================================================================
Wraps Kokoro-82M ONNX inference for 8 international languages and 50+ voices.
"""

from __future__ import annotations

import io
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from pydub import AudioSegment

# Comprehensive International Voice Catalog
VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    # ------------------ 🇺🇸 American English (en-us) ------------------
    "af_bella": {"name": "Bella", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Warm, expressive, high-retention narration"},
    "af_heart": {"name": "Heart", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Gentle, soothing, emotional clarity"},
    "af_nicole": {"name": "Nicole", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Mature, calm, thoughtful storyteller"},
    "af_sarah": {"name": "Sarah", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Natural, everyday conversational warmth"},
    "af_sky": {"name": "Sky", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Youthful, energetic, conversational"},
    "af_alloy": {"name": "Alloy", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Clean, modern, articulate corporate tone"},
    "af_aoede": {"name": "Aoede", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Melodic, poetic, storytelling cadence"},
    "af_jessica": {"name": "Jessica", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Casual, upbeat, commercial presenter"},
    "af_kore": {"name": "Kore", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Resonant, clear, informative reading"},
    "af_nova": {"name": "Nova", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Sharp, tech-focused, dynamic pacing"},
    "af_river": {"name": "River", "gender": "Female", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Calm, acoustic, relaxed podcast voice"},
    "am_adam": {"name": "Adam", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Deep, authoritative, podcast host style"},
    "am_michael": {"name": "Michael", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Friendly, relatable, clean studio tone"},
    "am_echo": {"name": "Echo", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Smooth, resonant, radio broadcast voice"},
    "am_eric": {"name": "Eric", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Confident, direct, business professional"},
    "am_fenrir": {"name": "Fenrir", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Deep, dramatic, cinematic trailer tone"},
    "am_liam": {"name": "Liam", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Youthful, modern, YouTube style narrator"},
    "am_onyx": {"name": "Onyx", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Heavy baritone, powerful, commanding"},
    "am_puck": {"name": "Puck", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Playful, bright, upbeat storytelling"},
    "am_santa": {"name": "Santa", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Warm, grandfatherly, jovial narration"},

    # ------------------ 🇬🇧 British English (en-gb) ------------------
    "bm_george": {"name": "George", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Distinguished, resonant, classic narrator"},
    "bm_lewis": {"name": "Lewis", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Articulate, engaging BBC documentary tone"},
    "bm_daniel": {"name": "Daniel", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Cultured, academic, refined presentation"},
    "bm_fable": {"name": "Fable", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Whimsical, storybook, character narrator"},
    "bf_emma": {"name": "Emma", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Sophisticated, crisp, professional"},
    "bf_isabella": {"name": "Isabella", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Soft, gentle, audio-book style"},
    "bf_alice": {"name": "Alice", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Clear, modern British accent"},
    "bf_lily": {"name": "Lily", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Bright, engaging, friendly British tone"},

    # ------------------ 🇪🇸 Spanish (es) ------------------
    "ef_dora": {"name": "Dora", "gender": "Female", "lang": "es", "lang_name": "Spanish", "flag": "🇪🇸", "description": "Warm, expressive Spanish narrator"},
    "em_alex": {"name": "Alex", "gender": "Male", "lang": "es", "lang_name": "Spanish", "flag": "🇪🇸", "description": "Clear, dynamic Spanish male voice"},
    "em_santa": {"name": "Papá Noel", "gender": "Male", "lang": "es", "lang_name": "Spanish", "flag": "🇪🇸", "description": "Jovial, warm Spanish baritone"},

    # ------------------ 🇫🇷 French (fr-fr) ------------------
    "ff_siwis": {"name": "Siwis", "gender": "Female", "lang": "fr-fr", "lang_name": "French", "flag": "🇫🇷", "description": "Elegant, authentic Parisian French voice"},

    # ------------------ 🇮🇳 Hindi (hi) ------------------
    "hf_alpha": {"name": "Alpha (अल्फा)", "gender": "Female", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Clear, expressive Hindi female narrator"},
    "hf_beta": {"name": "Beta (बीटा)", "gender": "Female", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Soothing, melodic Hindi voice"},
    "hm_omega": {"name": "Omega (ओमेगा)", "gender": "Male", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Resonant, authoritative Hindi male voice"},
    "hm_psi": {"name": "Psi (साई)", "gender": "Male", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Youthful, energetic Hindi storyteller"},

    # ------------------ 🇮🇹 Italian (it) ------------------
    "if_sara": {"name": "Sara", "gender": "Female", "lang": "it", "lang_name": "Italian", "flag": "🇮🇹", "description": "Lively, melodic, authentic Italian voice"},
    "im_nicola": {"name": "Nicola", "gender": "Male", "lang": "it", "lang_name": "Italian", "flag": "🇮🇹", "description": "Warm, expressive Italian narrator"},

    # ------------------ 🇧🇷 Portuguese (pt-br) ------------------
    "pf_dora": {"name": "Dora (BR)", "gender": "Female", "lang": "pt-br", "lang_name": "Portuguese (BR)", "flag": "🇧🇷", "description": "Natural, warm Brazilian Portuguese voice"},
    "pm_alex": {"name": "Alex (BR)", "gender": "Male", "lang": "pt-br", "lang_name": "Portuguese (BR)", "flag": "🇧🇷", "description": "Modern, friendly Brazilian narrator"},
    "pm_santa": {"name": "Papai Noel", "gender": "Male", "lang": "pt-br", "lang_name": "Portuguese (BR)", "flag": "🇧🇷", "description": "Warm Brazilian Portuguese storytelling voice"},

    # ------------------ 🇯🇵 Japanese (ja) ------------------
    "jf_alpha": {"name": "Alpha (アルファ)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Clear, gentle anime-style Japanese female voice"},
    "jf_gongitsune": {"name": "Gongitsune (ごんぎつね)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Traditional Japanese storybook narration"},
    "jf_nezumi": {"name": "Nezumi (ねずみ)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Cute, high-energy Japanese character voice"},
    "jf_tebukuro": {"name": "Tebukuro (てぶくろ)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Calm, gentle Japanese audiobook tone"},
    "jm_kumo": {"name": "Kumo (くも)", "gender": "Male", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Deep, calm Japanese male narrator"},
}


class KokoroStudioEngine:
    """Manages model loading, international voice synthesis, and audio generation."""

    def __init__(self, model_dir: Optional[Path] = None):
        if model_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
            model_dir = base_dir / "assets" / "kokoro"

        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "kokoro-v0_19.onnx"
        self.voices_path = self.model_dir / "voices-v1.0.bin"
        if not self.voices_path.exists():
            self.voices_path = self.model_dir / "voices.bin"

        self._kokoro: Optional[Kokoro] = None
        self._is_loaded = False
        self.sample_rate = 24000

    def load_model(self) -> bool:
        """Load the Kokoro ONNX model into memory."""
        if self._is_loaded and self._kokoro is not None:
            return True

        if not self.model_path.exists():
            raise FileNotFoundError(f"Kokoro model not found at: {self.model_path}")
        if not self.voices_path.exists():
            raise FileNotFoundError(f"Kokoro voices file not found at: {self.voices_path}")

        self._kokoro = Kokoro(
            model_path=str(self.model_path),
            voices_path=str(self.voices_path),
        )
        self._is_loaded = True
        return True

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @staticmethod
    def get_lang_code_for_voice(voice_key: str) -> str:
        """Map voice key to its phonetic language code."""
        info = VOICE_CATALOG.get(voice_key)
        if info:
            return info["lang"]

        prefix = voice_key[:2].lower()
        if prefix in ("af", "am"):
            return "en-us"
        elif prefix in ("bf", "bm"):
            return "en-gb"
        elif prefix in ("ef", "em"):
            return "es"
        elif prefix in ("ff", "fm"):
            return "fr-fr"
        elif prefix in ("hf", "hm"):
            return "hi"
        elif prefix in ("if", "im"):
            return "it"
        elif prefix in ("pf", "pm"):
            return "pt-br"
        elif prefix in ("jf", "jm"):
            return "ja"
        return "en-us"

    def get_available_voices(self, filter_lang: Optional[str] = None) -> List[Tuple[str, str]]:
        """Return list of (voice_key, formatted_label) tuples, optionally filtered by language."""
        voices = []
        for key, info in VOICE_CATALOG.items():
            if filter_lang and filter_lang != "All" and info["lang_name"] != filter_lang:
                continue
            flag = info.get("flag", "🌐")
            label = f"{flag} {info['name']} ({info['gender']}, {info['lang_name']}) — {info['description']}"
            voices.append((key, label))
        return voices

    def get_language_options(self) -> List[str]:
        """Return list of unique language names for UI filtering."""
        langs = sorted(list(set(info["lang_name"] for info in VOICE_CATALOG.values())))
        return ["All Languages"] + langs

    def synthesize_text(
        self,
        text: str,
        voice: str = "af_bella",
        speed: float = 1.0,
        lang: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[np.ndarray, int]:
        """Synthesize a block of text into audio with automatic language resolution."""
        if not self._is_loaded:
            self.load_model()

        clean_text = text.strip()
        if not clean_text:
            return np.array([], dtype=np.float32), self.sample_rate

        resolved_lang = lang or self.get_lang_code_for_voice(voice)

        if progress_callback:
            progress_callback(0.1, f"Synthesizing with {voice} ({resolved_lang})...")

        samples, sample_rate = self._kokoro.create(
            text=clean_text,
            voice=voice,
            speed=speed,
            lang=resolved_lang,
        )

        if progress_callback:
            progress_callback(1.0, "Synthesis complete!")

        return samples, sample_rate

    def synthesize_dialogue(
        self,
        dialogue_blocks: List[Dict[str, Any]],
        speaker_voice_map: Dict[str, str],
        pause_ms: int = 350,
        default_speed: float = 1.0,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> AudioSegment:
        """Synthesize a multi-character script across languages and concatenate with natural pauses."""
        if not self._is_loaded:
            self.load_model()

        combined_audio = AudioSegment.empty()
        silence = AudioSegment.silent(duration=pause_ms)
        total = len(dialogue_blocks)

        for idx, block in enumerate(dialogue_blocks):
            speaker = block.get("speaker", "Speaker").strip()
            text = block.get("text", "").strip()
            if not text:
                continue

            voice = speaker_voice_map.get(speaker, "af_bella")
            speed = block.get("speed", default_speed)
            lang = self.get_lang_code_for_voice(voice)

            if progress_callback:
                frac = idx / total
                progress_callback(frac, f"Synthesizing {speaker} ({idx + 1}/{total})...")

            samples, sr = self.synthesize_text(text, voice=voice, speed=speed, lang=lang)
            if len(samples) == 0:
                continue

            audio_seg = self.numpy_to_audiosegment(samples, sr)
            if len(combined_audio) > 0:
                combined_audio += silence
            combined_audio += audio_seg

        if progress_callback:
            progress_callback(1.0, "Multi-speaker drama complete!")

        return combined_audio

    @staticmethod
    def numpy_to_audiosegment(samples: np.ndarray, sample_rate: int = 24000) -> AudioSegment:
        """Convert float32 numpy audio samples to pydub AudioSegment."""
        scaled = np.int16(np.clip(samples, -1.0, 1.0) * 32767)
        byte_io = io.BytesIO()
        sf.write(byte_io, scaled, sample_rate, format="WAV", subtype="PCM_16")
        byte_io.seek(0)
        return AudioSegment.from_wav(byte_io)

    @staticmethod
    def export_audio(
        audio: AudioSegment | Tuple[np.ndarray, int],
        output_path: Path,
        format: str = "mp3",
        bitrate: str = "192k",
    ) -> Path:
        """Export audio to disk in the desired format (.mp3, .wav, .ogg)."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(audio, tuple):
            samples, sr = audio
            seg = KokoroStudioEngine.numpy_to_audiosegment(samples, sr)
        else:
            seg = audio

        clean_fmt = format.lower().replace(".", "")
        if clean_fmt == "mp3":
            seg.export(str(output_path), format="mp3", bitrate=bitrate)
        elif clean_fmt == "wav":
            seg.export(str(output_path), format="wav")
        elif clean_fmt == "ogg":
            seg.export(str(output_path), format="ogg")
        else:
            seg.export(str(output_path), format="mp3", bitrate=bitrate)

        return output_path
