"""
SayTTS — Pocket TTS Engine (Secondary & Voice Cloning Engine)
=============================================================
Provides CPU-accelerated speech synthesis using Kyutai Labs' Pocket TTS (100M CALM),
including 26 European character voices and zero-shot voice cloning from reference audio.
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from core.base_engine import BaseTTSEngine

logger = logging.getLogger("saytts.pocket_engine")

# Confirmed 26 built-in character voices in Pocket TTS 3.1.0
POCKET_RAW_VOICES = [
    "alba", "marius", "javert", "fantine", "cosette", "jean",
    "anna", "vera", "charles", "paul", "eponine", "azelma",
    "george", "mary", "jane", "michael", "eve", "bill_boerst",
    "peter_yearsley", "stuart_bell", "caro_davy", "giovanni",
    "lola", "juergen", "rafael", "estelle",
]

# Curated catalog metadata for Pocket character voices (all 26 built-in CALM voices)
POCKET_VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    "pocket_alba": {"name": "Alba (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Natural European storytelling voice", "engine": "pocket", "type": "character"},
    "pocket_marius": {"name": "Marius (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Youthful, energetic male narration", "engine": "pocket", "type": "character"},
    "pocket_javert": {"name": "Javert (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Deep, authoritative male baritone", "engine": "pocket", "type": "character"},
    "pocket_fantine": {"name": "Fantine (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Gentle, emotive female storytelling tone", "engine": "pocket", "type": "character"},
    "pocket_cosette": {"name": "Cosette (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Light, expressive character voice", "engine": "pocket", "type": "character"},
    "pocket_jean": {"name": "Jean (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Warm, mature, reflective narrator", "engine": "pocket", "type": "character"},
    "pocket_anna": {"name": "Anna (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Clear, articulate female character", "engine": "pocket", "type": "character"},
    "pocket_vera": {"name": "Vera (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Calm, nuanced female narrator", "engine": "pocket", "type": "character"},
    "pocket_charles": {"name": "Charles (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Classic theatrical British tone", "engine": "pocket", "type": "character"},
    "pocket_paul": {"name": "Paul (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Friendly, conversational male speaker", "engine": "pocket", "type": "character"},
    "pocket_eponine": {"name": "Eponine (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Spirited, dramatic female voice", "engine": "pocket", "type": "character"},
    "pocket_azelma": {"name": "Azelma (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Subtle, soft female tone", "engine": "pocket", "type": "character"},
    "pocket_george": {"name": "George (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Steady, documentary narrator", "engine": "pocket", "type": "character"},
    "pocket_mary": {"name": "Mary (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Warm, reassuring storytelling voice", "engine": "pocket", "type": "character"},
    "pocket_jane": {"name": "Jane (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Polished, crisp audiobook voice", "engine": "pocket", "type": "character"},
    "pocket_michael": {"name": "Michael (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Resonant, engaging presenter voice", "engine": "pocket", "type": "character"},
    "pocket_eve": {"name": "Eve (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Modern, clean podcast style", "engine": "pocket", "type": "character"},
    "pocket_bill_boerst": {"name": "Bill Boerst (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Distinguished, mature American voice", "engine": "pocket", "type": "character"},
    "pocket_peter_yearsley": {"name": "Peter Yearsley (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Scholarly, resonant classic voice", "engine": "pocket", "type": "character"},
    "pocket_stuart_bell": {"name": "Stuart Bell (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Deep, smooth British narration", "engine": "pocket", "type": "character"},
    "pocket_caro_davy": {"name": "Caro Davy (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Rich, lyrical storytelling voice", "engine": "pocket", "type": "character"},
    "pocket_giovanni": {"name": "Giovanni (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Expressive Mediterranean character", "engine": "pocket", "type": "character"},
    "pocket_lola": {"name": "Lola (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Bright, cheerful character tone", "engine": "pocket", "type": "character"},
    "pocket_juergen": {"name": "Juergen (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Commanding, precise character voice", "engine": "pocket", "type": "character"},
    "pocket_rafael": {"name": "Rafael (Pocket)", "gender": "Male", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Warm, melodic Spanish-inflected tone", "engine": "pocket", "type": "character"},
    "pocket_estelle": {"name": "Estelle (Pocket)", "gender": "Female", "lang": "en-us", "lang_name": "English (Pocket)", "flag": "🎭", "description": "Elegant, graceful character voice", "engine": "pocket", "type": "character"},
}


class PocketTTSEngine(BaseTTSEngine):
    """
    Pocket TTS Engine implementation for SayTTS.
    Handles character voices and zero-shot voice cloning with state caching.
    """

    def __init__(self, language: str = "english", auto_download: bool = False):
        self.language = language
        self.auto_download = auto_download
        self._model = None
        self._is_loaded = False
        self._init_error: Optional[str] = None
        self._has_voice_cloning = False
        self._lock = threading.Lock()
        self._voice_state_cache: Dict[str, Any] = {}
        self._custom_voices_dir = Path(__file__).resolve().parent.parent / "data" / "custom_voices"
        self._custom_voices_dir.mkdir(parents=True, exist_ok=True)

    @property
    def engine_name(self) -> str:
        return "pocket"

    @property
    def sample_rate(self) -> int:
        return 24000

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded and self._model is not None

    @property
    def has_voice_cloning(self) -> bool:
        return self._has_voice_cloning

    @property
    def init_error(self) -> Optional[str]:
        return self._init_error

    def get_voice_catalog(self) -> Dict[str, Dict[str, str]]:
        """Returns metadata catalog for all Pocket character voices."""
        return POCKET_VOICE_CATALOG

    def are_weights_cached(self) -> bool:
        """Check whether local cache contains model weights without triggering network download."""
        hf_home = os.environ.get("HF_HOME")
        if hf_home:
            cache_root = Path(hf_home) / "hub"
        else:
            cache_root = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub"
        for repo_name in ["models--kyutai--pocket-tts-without-voice-cloning", "models--kyutai--pocket-tts"]:
            repo_dir = cache_root / repo_name / "snapshots"
            if repo_dir.exists():
                for snap in repo_dir.iterdir():
                    if (snap / "languages" / self.language / "model.safetensors").exists():
                        return True
        return False

    def load_model(self, force_download: bool = False) -> bool:
        """
        Loads the Pocket TTS model into memory.
        Safe to call multiple times (idempotent).
        If weights are not cached and auto_download is False, skips download to protect bandwidth.
        """
        if self._is_loaded and self._model is not None:
            return True

        # Guard against auto-download unless explicitly configured
        if not force_download and not self.auto_download and not self.are_weights_cached():
            self._init_error = (
                "Pocket TTS weights are not downloaded locally. "
                "Kokoro voices remain fully functional."
            )
            return False

        with self._lock:
            if self._is_loaded and self._model is not None:
                return True

            try:
                from pocket_tts import TTSModel

                logger.info("Initializing Pocket TTS model on CPU...")
                # Disable symlink warnings on Windows
                os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

                model = TTSModel.load_model(language=self.language)
                model.to("cpu")
                self._model = model
                self._is_loaded = True
                self._has_voice_cloning = getattr(model, "has_voice_cloning", False)
                self._init_error = None
                logger.info(
                    f"Pocket TTS loaded successfully! (Voice Cloning Available: {self._has_voice_cloning})"
                )
                return True

            except Exception as e:
                self._init_error = f"{type(e).__name__}: {str(e)}"
                logger.warning(f"Pocket TTS model load deferred/failed: {self._init_error}")
                return False

    def get_voice_state(self, voice_ref: Union[str, Path]) -> Any:
        """
        Retrieve pre-computed voice state from memory cache, local safetensors,
        or download for built-in character voices.
        """
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError(f"Pocket TTS is not available: {self._init_error}")

        ref_key = str(voice_ref)
        if ref_key in self._voice_state_cache:
            return self._voice_state_cache[ref_key]

        # Normalize pocket_ prefix if present (e.g. pocket_alba -> alba)
        clean_voice = ref_key
        if clean_voice.startswith("pocket_"):
            clean_voice = clean_voice[7:]

        # Check if voice_ref is a local safetensors file
        path_candidate = Path(ref_key)
        if not path_candidate.exists() and (self._custom_voices_dir / ref_key).exists():
            path_candidate = self._custom_voices_dir / ref_key
        if not path_candidate.exists() and (self._custom_voices_dir / f"{ref_key}.safetensors").exists():
            path_candidate = self._custom_voices_dir / f"{ref_key}.safetensors"

        if path_candidate.exists() and str(path_candidate).endswith(".safetensors"):
            state = self._model.get_state_for_audio_prompt(path_candidate)
            self._voice_state_cache[ref_key] = state
            return state

        # Check if it's a known built-in character voice
        if clean_voice in POCKET_RAW_VOICES:
            state = self._model.get_state_for_audio_prompt(clean_voice)
            self._voice_state_cache[ref_key] = state
            return state

        # If it's an audio file path (WAV/MP3) for dynamic cloning
        if path_candidate.exists() and path_candidate.suffix.lower() in (".wav", ".mp3", ".m4a", ".ogg", ".flac"):
            if not self._has_voice_cloning:
                raise RuntimeError(
                    "Pocket TTS voice cloning requires authenticated access to kyutai/pocket-tts on Hugging Face. "
                    "Built-in character voices ('alba', 'marius', 'javert', 'fantine', etc.) are ready to use."
                )
            state = self._model.get_state_for_audio_prompt(path_candidate, truncate=True)
            self._voice_state_cache[ref_key] = state
            return state

        # Fallback to default alba voice
        logger.warning(f"Voice '{voice_ref}' not recognized by Pocket TTS; falling back to 'alba'")
        state = self._model.get_state_for_audio_prompt("alba")
        self._voice_state_cache[ref_key] = state
        return state

    def extract_and_cache_voice_state(
        self,
        reference_audio_path: Union[str, Path],
        output_safetensors_path: Union[str, Path],
    ) -> Path:
        """
        Extract speaker acoustic conditioning from a reference audio recording
        and save as a reusable .safetensors state file.
        """
        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError(f"Pocket TTS is not available: {self._init_error}")

        if not self._has_voice_cloning:
            raise RuntimeError(
                "Pocket TTS voice cloning requires access to the gated kyutai/pocket-tts weights. "
                "Please accept the terms at https://huggingface.co/kyutai/pocket-tts and ensure your "
                "HF_TOKEN environment variable is set."
            )

        ref_path = Path(reference_audio_path)
        if not ref_path.exists():
            raise FileNotFoundError(f"Reference audio file not found: {ref_path}")

        from pocket_tts import export_model_state

        out_path = Path(output_safetensors_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            state = self._model.get_state_for_audio_prompt(ref_path, truncate=True)
            export_model_state(state, out_path)

        # Cache in memory
        self._voice_state_cache[str(out_path)] = state
        logger.info(f"Custom voice state saved and cached at: {out_path}")
        return out_path

    def synthesize_text(
        self,
        text: str,
        voice: Union[str, Any] = "pocket_alba",
        speed: float = 1.0,
        lang: Optional[str] = "en-us",
        master_preset: str = "Raw Unprocessed",
        progress_callback: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, int]:
        """
        Synthesizes speech text using Pocket TTS.
        Thread-safe: protected by internal lock.
        Returns: (samples: np.ndarray, sample_rate: int)
        """
        clean_text = text.strip()
        if not clean_text:
            return np.array([], dtype=np.float32), self.sample_rate

        if not self.is_loaded:
            if not self.load_model():
                raise RuntimeError(f"Pocket TTS model is not available: {self._init_error}")

        # Retrieve voice state
        voice_state = self.get_voice_state(voice)

        with self._lock:
            if progress_callback:
                progress_callback(0.3, "Generating speech with Pocket TTS...")

            audio_tensor = self._model.generate_audio(
                model_state=voice_state,
                text_to_generate=clean_text,
                copy_state=True,
            )

            # Convert torch tensor to 1D float32 numpy array
            samples = audio_tensor.detach().cpu().numpy().astype(np.float32)

            # Ensure 1D array
            if samples.ndim > 1:
                samples = samples.squeeze()

            if progress_callback:
                progress_callback(1.0, "Pocket TTS synthesis complete!")

            return samples, self.sample_rate
