"""
SayTTS — Unified TTS Engine Router
===================================
Central router directing speech synthesis requests to the appropriate engine:
- Kokoro (Primary / Default): standard catalog voices, news, multi-speaker dialogue
- Pocket TTS (Secondary): 26 character voices, zero-shot custom cloned voices
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from core.base_engine import BaseTTSEngine
from core.kokoro_engine import KokoroStudioEngine, VOICE_CATALOG
from core.pocket_engine import PocketTTSEngine, POCKET_VOICE_CATALOG, POCKET_RAW_VOICES

logger = logging.getLogger("saytts.router")


class TTSRouter:
    """
    Centralized router for multi-engine TTS execution.
    Transparently resolves engine from voice identifier.
    """

    def __init__(
        self,
        kokoro_engine: Optional[KokoroStudioEngine] = None,
        pocket_engine: Optional[PocketTTSEngine] = None,
    ):
        self.kokoro = kokoro_engine or KokoroStudioEngine()
        self.pocket = pocket_engine or PocketTTSEngine()

    def resolve_engine_for_voice(self, voice_id: str) -> str:
        """
        Determine whether a voice belongs to Kokoro or Pocket TTS.
        Kokoro is always the authoritative default.
        """
        if not voice_id:
            return "kokoro"

        v_lower = str(voice_id).strip().lower()

        # Custom cloned voices belong to Pocket TTS
        if v_lower.startswith("custom_") or v_lower.endswith(".safetensors"):
            return "pocket"

        # Pocket character voices
        if v_lower.startswith("pocket_") or v_lower in POCKET_RAW_VOICES:
            return "pocket"

        # Explicit check against Pocket catalog
        if v_lower in POCKET_VOICE_CATALOG:
            return "pocket"

        # Default to Kokoro
        return "kokoro"

    def is_valid_voice(self, voice_id: str) -> bool:
        """Check if a voice_id is recognized by either Kokoro, Pocket, or custom prefix."""
        if not voice_id:
            return False
        v_lower = str(voice_id).strip().lower()
        if v_lower in VOICE_CATALOG:
            return True
        if v_lower in POCKET_VOICE_CATALOG or v_lower.startswith("pocket_") or v_lower in POCKET_RAW_VOICES:
            return True
        if v_lower.startswith("custom_") or v_lower.endswith(".safetensors"):
            return True
        return False

    def get_engine_for_voice(self, voice_id: str) -> BaseTTSEngine:
        """Return the concrete BaseTTSEngine instance for a voice."""
        engine_type = self.resolve_engine_for_voice(voice_id)
        if engine_type == "pocket":
            return self.pocket
        return self.kokoro

    def synthesize(
        self,
        text: str,
        voice: Union[str, Any] = "af_bella",
        speed: float = 1.0,
        lang: Optional[str] = "auto",
        master_preset: str = "Raw Unprocessed",
        progress_callback: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, int, str]:
        """
        Route and execute synthesis.
        Returns:
            Tuple of (samples: np.ndarray, sample_rate: int, engine_used: str)
        """
        if "voice_id" in kwargs:
            voice = kwargs.pop("voice_id")
        custom_voice_state = kwargs.pop("custom_voice_state", None)

        voice_str = voice if isinstance(voice, str) else "af_bella"
        engine_type = self.resolve_engine_for_voice(voice_str)

        if engine_type == "pocket":
            samples, sr = self.pocket.synthesize_text(
                text=text,
                voice=voice,
                speed=speed,
                lang=lang,
                master_preset=master_preset,
                progress_callback=progress_callback,
                custom_voice_state=custom_voice_state,
                **kwargs,
            )
            return samples, sr, "pocket"

        # Kokoro (Primary)
        samples, sr = self.kokoro.synthesize_text(
            text=text,
            voice=voice,
            speed=speed,
            lang=lang,
            master_preset=master_preset,
            progress_callback=progress_callback,
        )
        return samples, sr, "kokoro"

    def get_unified_catalog(
        self, custom_voices: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Combines standard Kokoro voices, Pocket character voices, and custom voices
        into a single catalog with metadata.
        """
        unified: List[Dict[str, Any]] = []

        # 1. Kokoro Standard Voices (Primary)
        for vid, vdata in VOICE_CATALOG.items():
            unified.append({
                "id": vid,
                "name": vdata.get("name", vid),
                "gender": vdata.get("gender", "Neutral"),
                "lang": vdata.get("lang", "en-us"),
                "lang_name": vdata.get("lang_name", "English (US)"),
                "flag": vdata.get("flag", "🌐"),
                "description": vdata.get("description", ""),
                "engine": "kokoro",
                "type": "standard",
            })

        # 2. Custom Voices (if provided for device)
        if custom_voices:
            for cv in custom_voices:
                unified.append({
                    "id": cv.get("id"),
                    "name": cv.get("name", "Custom Voice"),
                    "gender": cv.get("gender", "Neutral"),
                    "lang": cv.get("lang", "en-us"),
                    "lang_name": "Custom Cloned Voice",
                    "flag": "🎙️",
                    "description": cv.get("description", "User cloned custom voice"),
                    "engine": "pocket",
                    "type": "custom",
                })

        # 3. Pocket Character Voices
        for pvid, pvdata in POCKET_VOICE_CATALOG.items():
            unified.append({
                "id": pvid,
                "name": pvdata.get("name", pvid),
                "gender": pvdata.get("gender", "Neutral"),
                "lang": pvdata.get("lang", "en-us"),
                "lang_name": pvdata.get("lang_name", "English (Pocket)"),
                "flag": pvdata.get("flag", "🎭"),
                "description": pvdata.get("description", ""),
                "engine": "pocket",
                "type": "character",
            })

        return unified
