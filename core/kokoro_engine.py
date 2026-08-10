"""
Kokoro Studio — Core Kokoro TTS Engine
======================================
Wraps Kokoro-82M ONNX inference for single-speaker and multi-speaker synthesis.
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

# Comprehensive catalog of Kokoro voices with display metadata
VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    "af_bella": {
        "name": "Bella",
        "gender": "Female",
        "accent": "American",
        "description": "Warm, expressive, high-retention narration",
    },
    "am_adam": {
        "name": "Adam",
        "gender": "Male",
        "accent": "American",
        "description": "Deep, authoritative, podcast host style",
    },
    "af_nicole": {
        "name": "Nicole",
        "gender": "Female",
        "accent": "American",
        "description": "Mature, calm, thoughtful storyteller",
    },
    "bm_george": {
        "name": "George",
        "gender": "Male",
        "accent": "British",
        "description": "Distinguished, resonant, classic narrator",
    },
    "af_sky": {
        "name": "Sky",
        "gender": "Female",
        "accent": "American",
        "description": "Youthful, energetic, conversational",
    },
    "am_michael": {
        "name": "Michael",
        "gender": "Male",
        "accent": "American",
        "description": "Friendly, relatable, clean studio tone",
    },
    "am_puck": {
        "name": "Puck",
        "gender": "Male",
        "accent": "American",
        "description": "Playful, bright, upbeat pacing",
    },
    "bf_emma": {
        "name": "Emma",
        "gender": "Female",
        "accent": "British",
        "description": "Sophisticated, crisp, professional",
    },
    "bf_isabella": {
        "name": "Isabella",
        "gender": "Female",
        "accent": "British",
        "description": "Soft, gentle, audio-book style",
    },
    "bm_lewis": {
        "name": "Lewis",
        "gender": "Male",
        "accent": "British",
        "description": "Articulate, engaging BBC documentary tone",
    },
    "af_sarah": {
        "name": "Sarah",
        "gender": "Female",
        "accent": "American",
        "description": "Natural, everyday conversational warmth",
    },
}


class KokoroStudioEngine:
    """Manages model loading, voice synthesis, and audio generation."""

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
        """Return list of (voice_key, formatted_label) tuples."""
        voices = []
        for key, info in VOICE_CATALOG.items():
            label = f"{info['name']} ({info['gender']}, {info['accent']}) — {info['description']}"
            voices.append((key, label))
        return voices

    def synthesize_text(
        self,
        text: str,
        voice: str = "am_adam",
        speed: float = 1.0,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[np.ndarray, int]:
        """Synthesize a block of text into audio.

        Args:
            text: Input string.
            voice: Voice key (e.g. 'af_bella').
            speed: Playback speed multiplier (0.5 to 2.0).
            progress_callback: Optional callback(fraction, status_text).

        Returns:
            Tuple of (audio_samples_numpy_array, sample_rate).
        """
        if not self._is_loaded:
            self.load_model()

        clean_text = text.strip()
        if not clean_text:
            return np.array([], dtype=np.float32), self.sample_rate

        if progress_callback:
            progress_callback(0.1, f"Synthesizing with {voice}...")

        # Kokoro handles chunks internally or via create()
        samples, sample_rate = self._kokoro.create(
            text=clean_text,
            voice=voice,
            speed=speed,
            lang="en-us",
        )

        if progress_callback:
            progress_callback(1.0, "Synthesis complete!")

        return samples, sample_rate

    def synthesize_dialogue(
        self,
        dialogue_blocks: List[Dict[str, Any]],
        speaker_voice_map: Dict[str, str],
        pause_ms: int = 400,
        default_speed: float = 1.0,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> AudioSegment:
        """Synthesize a multi-character script and concatenate with natural pauses.

        Args:
            dialogue_blocks: List of {"speaker": str, "text": str, "speed": Optional[float]}.
            speaker_voice_map: Mapping from speaker names to Kokoro voice keys.
            pause_ms: Milliseconds of silence between turns.
            default_speed: Default speed for blocks without specific speed.
            progress_callback: Callback for overall dialogue progress.

        Returns:
            Combined pydub AudioSegment.
        """
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

            voice = speaker_voice_map.get(speaker, "am_adam")
            speed = block.get("speed", default_speed)

            if progress_callback:
                frac = idx / total
                progress_callback(frac, f"Synthesizing {speaker} ({idx + 1}/{total})...")

            samples, sr = self.synthesize_text(text, voice=voice, speed=speed)
            if len(samples) == 0:
                continue

            # Convert numpy array to pydub AudioSegment
            audio_seg = self.numpy_to_audiosegment(samples, sr)
            if len(combined_audio) > 0:
                combined_audio += silence
            combined_audio += audio_seg

        if progress_callback:
            progress_callback(1.0, "Multi-speaker synthesis complete!")

        return combined_audio

    @staticmethod
    def numpy_to_audiosegment(samples: np.ndarray, sample_rate: int = 24000) -> AudioSegment:
        """Convert float32 numpy audio samples to pydub AudioSegment."""
        # Convert float32 [-1.0, 1.0] to int16
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
