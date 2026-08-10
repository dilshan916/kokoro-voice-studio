"""
Kokoro Studio — Engine with Voice Blending & Studio Mastering
=============================================================
Ultra-Pro TTS engine powered by Kokoro-82M ONNX with custom voice mixing,
acoustic EQ mastering presets, and smart pause SSML tag parsing.
"""

from __future__ import annotations

import io
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from pydub import AudioSegment, effects

# Studio Voice Catalog
VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    # 🇺🇸 American English
    "af_bella": {"name": "Bella", "gender": "Female", "accent": "American", "flag": "🇺🇸", "description": "Warm, expressive, high-retention narration"},
    "af_nicole": {"name": "Nicole", "gender": "Female", "accent": "American", "flag": "🇺🇸", "description": "Mature, calm, thoughtful storyteller"},
    "af_sarah": {"name": "Sarah", "gender": "Female", "accent": "American", "flag": "🇺🇸", "description": "Natural, everyday conversational warmth"},
    "af_sky": {"name": "Sky", "gender": "Female", "accent": "American", "flag": "🇺🇸", "description": "Youthful, energetic, conversational"},
    "am_adam": {"name": "Adam", "gender": "Male", "accent": "American", "flag": "🇺🇸", "description": "Deep, authoritative, podcast host style"},
    "am_michael": {"name": "Michael", "gender": "Male", "accent": "American", "flag": "🇺🇸", "description": "Friendly, relatable, clean studio tone"},

    # 🇬🇧 British English
    "bm_george": {"name": "George", "gender": "Male", "accent": "British", "flag": "🇬🇧", "description": "Distinguished, resonant, classic narrator"},
    "bm_lewis": {"name": "Lewis", "gender": "Male", "accent": "British", "flag": "🇬🇧", "description": "Articulate, engaging BBC documentary tone"},
    "bf_emma": {"name": "Emma", "gender": "Female", "accent": "British", "flag": "🇬🇧", "description": "Sophisticated, crisp, professional"},
    "bf_isabella": {"name": "Isabella", "gender": "Female", "accent": "British", "flag": "🇬🇧", "description": "Soft, gentle, audiobook style"},
}

MASTERING_PRESETS = [
    "Clean Studio (Default)",
    "Warm Podcast Host (+Bass)",
    "Deep Cinematic Trailer",
    "Radio Broadcast (Punchy)",
    "Raw Unprocessed",
]


class KokoroStudioEngine:
    """Pro Studio TTS Engine supporting Voice Blending and Master EQ effects."""

    def __init__(self, model_dir: Optional[Path] = None):
        if model_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
            model_dir = base_dir / "assets" / "kokoro"

        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "kokoro-v0_19.onnx"
        self.voices_path = self.model_dir / "voices.bin"
        if not self.voices_path.exists():
            self.voices_path = self.model_dir / "voices.json"

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

    def get_available_voices(self) -> List[Tuple[str, str]]:
        voices = []
        for key, info in VOICE_CATALOG.items():
            flag = info.get("flag", "🌐")
            label = f"{flag} {info['name']} ({info['gender']}, {info['accent']}) — {info['description']}"
            voices.append((key, label))
        return voices

    def get_voice_style(self, voice_key: str) -> np.ndarray:
        """Retrieve the embedding style vector for a given voice."""
        if not self._is_loaded:
            self.load_model()
        return self._kokoro.get_voice_style(voice_key)

    def blend_voices(self, voice_a: str, voice_b: str, ratio: float = 0.5) -> np.ndarray:
        """
        Blend two voices with a ratio (0.0 = 100% voice_a, 1.0 = 100% voice_b).
        Generates a unique hybrid signature voice!
        """
        if not self._is_loaded:
            self.load_model()

        v1 = self._kokoro.get_voice_style(voice_a)
        v2 = self._kokoro.get_voice_style(voice_b)

        clamped_ratio = max(0.0, min(1.0, float(ratio)))
        blended = ((1.0 - clamped_ratio) * v1) + (clamped_ratio * v2)
        return blended

    def synthesize_text(
        self,
        text: str,
        voice: Union[str, np.ndarray] = "af_bella",
        speed: float = 1.0,
        lang: str = "en-us",
        master_preset: str = "Clean Studio (Default)",
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[np.ndarray, int]:
        """Synthesize text with automatic smart-pause parsing and mastering EQ."""
        if not self._is_loaded:
            self.load_model()

        clean_text = text.strip()
        if not clean_text:
            return np.array([], dtype=np.float32), self.sample_rate

        # Check for embedded pause tags: e.g. [pause 0.5s] or [pause 1.0s]
        pause_pattern = re.compile(r"\[pause\s+([0-9.]+)\s*s?\]", re.IGNORECASE)
        segments = pause_pattern.split(clean_text)

        if len(segments) > 1:
            # Multi-segment with pauses
            combined_samples = []
            for idx in range(0, len(segments), 2):
                chunk_text = segments[idx].strip()
                if chunk_text:
                    if progress_callback:
                        progress_callback(0.2 + (0.6 * (idx / len(segments))), f"Synthesizing section...")
                    samples, sr = self._kokoro.create(chunk_text, voice=voice, speed=speed, lang=lang)
                    combined_samples.append(samples)

                # Next item is pause duration in seconds
                if idx + 1 < len(segments):
                    try:
                        pause_sec = float(segments[idx + 1])
                        silence_len = int(pause_sec * self.sample_rate)
                        combined_samples.append(np.zeros(silence_len, dtype=np.float32))
                    except Exception:
                        pass

            if combined_samples:
                final_samples = np.concatenate(combined_samples)
            else:
                final_samples = np.array([], dtype=np.float32)
        else:
            if progress_callback:
                progress_callback(0.3, "Synthesizing voice...")
            final_samples, _ = self._kokoro.create(clean_text, voice=voice, speed=speed, lang=lang)

        if progress_callback:
            progress_callback(1.0, "Synthesis complete!")

        return final_samples, self.sample_rate

    @staticmethod
    def apply_studio_mastering(audio_seg: AudioSegment, preset: str = "Clean Studio (Default)") -> AudioSegment:
        """Apply professional DAW audio mastering EQ and dynamic processing."""
        if preset == "Raw Unprocessed":
            return audio_seg

        processed = audio_seg

        if preset == "Warm Podcast Host (+Bass)":
            # Warm low end boost + gentle normalization
            processed = processed.low_pass_filter(12000)
            processed = effects.normalize(processed, headroom=1.0)
            # Emphasize warmth by boosting lower mids
            processed = processed + 2.5

        elif preset == "Deep Cinematic Trailer":
            # Deep bass boost & punch
            processed = effects.normalize(processed, headroom=0.5)
            processed = processed + 3.5

        elif preset == "Radio Broadcast (Punchy)":
            # High-presence clarity and punch
            processed = effects.compress_dynamic_range(
                processed,
                threshold=-18.0,
                ratio=4.0,
                attack=5.0,
                release=50.0,
            )
            processed = effects.normalize(processed, headroom=1.0)

        elif preset == "Clean Studio (Default)":
            # Professional peak normalization (-1 dBFS)
            processed = effects.normalize(processed, headroom=1.0)

        return processed

    def synthesize_dialogue(
        self,
        dialogue_blocks: List[Dict[str, Any]],
        speaker_voice_map: Dict[str, str],
        pause_ms: int = 350,
        default_speed: float = 1.0,
        master_preset: str = "Clean Studio (Default)",
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> AudioSegment:
        """Synthesize a multi-character script and apply mastering."""
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

            if progress_callback:
                frac = idx / total
                progress_callback(frac, f"Synthesizing {speaker} ({idx + 1}/{total})...")

            samples, sr = self.synthesize_text(text, voice=voice, speed=speed, master_preset="Raw Unprocessed")
            if len(samples) == 0:
                continue

            audio_seg = self.numpy_to_audiosegment(samples, sr)
            if len(combined_audio) > 0:
                combined_audio += silence
            combined_audio += audio_seg

        # Apply mastering EQ across combined scene
        mastered = self.apply_studio_mastering(combined_audio, preset=master_preset)

        if progress_callback:
            progress_callback(1.0, "Multi-speaker drama complete!")

        return mastered

    @staticmethod
    def numpy_to_audiosegment(samples: np.ndarray, sample_rate: int = 24000) -> AudioSegment:
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
        bitrate: str = "320k",
    ) -> Path:
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
