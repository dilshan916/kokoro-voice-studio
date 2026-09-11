"""
Kokoro Studio — Engine with Complete 54 Multilingual Voices & Master EQ
========================================================================
Ultra-Pro TTS engine powered by Kokoro-82M ONNX with 54 voices across 9+ languages,
Multilingual G2P phonemizer integration, custom voice mixing (blending),
acoustic EQ mastering presets, and smart pause parsing.
"""

from __future__ import annotations

import io
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from core.multilingual_g2p import CANONICAL_LANG_MAP

# Lazy engine dependency placeholders
np = None
sf = None
Kokoro = None
AudioSegment = None
effects = None
MultilingualG2P = None

def _ensure_engine_deps():
    global np, sf, Kokoro, AudioSegment, effects, MultilingualG2P
    if Kokoro is None:
        import numpy as _np
        import soundfile as _sf
        from kokoro_onnx import Kokoro as _Kokoro
        from pydub import AudioSegment as _AudioSegment, effects as _effects
        from core.multilingual_g2p import MultilingualG2P as _MultilingualG2P
        np = _np
        sf = _sf
        Kokoro = _Kokoro
        AudioSegment = _AudioSegment
        effects = _effects
        MultilingualG2P = _MultilingualG2P

logger = logging.getLogger(__name__)


def format_srt_timestamp(seconds: float) -> str:
    """Convert seconds (float) into standard SubRip (SRT) timestamp format: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0.0
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        seconds += 1
        millis = 0
    total_seconds = int(seconds)
    secs = total_seconds % 60
    mins = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_srt_from_segments(segments: List[Dict[str, Any]]) -> str:
    """
    Generate standard CapCut / Premiere / DaVinci Resolve compliant .srt subtitle text.
    """
    srt_blocks = []
    counter = 1
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        start_ts = format_srt_timestamp(seg.get("start", 0.0))
        end_ts = format_srt_timestamp(seg.get("end", 0.0))
        srt_blocks.append(f"{counter}\n{start_ts} --> {end_ts}\n{text}\n")
        counter += 1
    return "\n".join(srt_blocks).strip() + "\n"


def apply_boundary_fades(
    samples: np.ndarray,
    fade_ms: float = 8.0,
    sample_rate: int = 24000,
) -> np.ndarray:
    """
    Apply short linear fade-in and fade-out at audio boundaries (5ms - 10ms)
    to eliminate DC offset clicks, pops, and sudden discontinuities when concatenating
    audio chunks and silence arrays.
    """
    if samples is None or len(samples) == 0:
        return samples
    fade_len = int((fade_ms / 1000.0) * sample_rate)
    fade_len = min(fade_len, len(samples) // 2)
    if fade_len <= 1:
        return samples

    samples = samples.copy().astype(np.float32)
    fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
    fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)

    samples[:fade_len] *= fade_in
    samples[-fade_len:] *= fade_out
    return samples


def parse_pause_tag_duration(tag_match_or_str: str) -> float:
    """
    Parse pause tag duration supporting varied formats:
    - [pause 0.5s], [pause 0.5], [pause: 500ms], [break 1.2s], <break time="500ms"/>
    Returns duration in seconds (clamped between 0.02s and 30.0s).
    """
    if not tag_match_or_str:
        return 0.0
    text = str(tag_match_or_str).strip()
    match = re.search(r"([0-9.]+)\s*(s|ms)?", text, re.IGNORECASE)
    if not match:
        return 0.35
    val = float(match.group(1))
    unit = (match.group(2) or "").lower()
    if unit == "ms" or (not unit and val >= 20.0):
        duration = val / 1000.0
    else:
        duration = val
    return max(0.02, min(30.0, duration))


# Complete 54+ Voice International Catalog (Official Kokoro ONNX + Curated Presets)
VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    # ------------------ 🇺🇸 American English (en-us - 20 Voices) ------------------
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
    "am_puck": {"name": "Puck", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Playful, bright, upbeat pacing"},
    "am_santa": {"name": "Santa", "gender": "Male", "lang": "en-us", "lang_name": "English (US)", "flag": "🇺🇸", "description": "Warm, grandfatherly, jovial narration"},

    # ------------------ 🇬🇧 British English (en-gb - 8 Voices) ------------------
    "bm_george": {"name": "George", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Distinguished, resonant, classic narrator"},
    "bm_lewis": {"name": "Lewis", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Articulate, engaging BBC documentary tone"},
    "bm_daniel": {"name": "Daniel", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Cultured, academic, refined presentation"},
    "bm_fable": {"name": "Fable", "gender": "Male", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Whimsical, storybook, character narrator"},
    "bf_emma": {"name": "Emma", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Sophisticated, crisp, professional"},
    "bf_isabella": {"name": "Isabella", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Soft, gentle, audiobook style"},
    "bf_alice": {"name": "Alice", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Clear, modern British accent"},
    "bf_lily": {"name": "Lily", "gender": "Female", "lang": "en-gb", "lang_name": "English (UK)", "flag": "🇬🇧", "description": "Bright, engaging, friendly British tone"},

    # ------------------ 🇫🇷 French (fr-fr - 5 Voices) ------------------
    "ff_siwis": {"name": "Siwis", "gender": "Female", "lang": "fr-fr", "lang_name": "French", "flag": "🇫🇷", "description": "Native Parisian French voice (Clean, elegant)"},
    "fm_alexandre": {"name": "Alexandre", "gender": "Male", "lang": "fr-fr", "lang_name": "French", "flag": "🇫🇷", "description": "Deep French male narrator (Resonant & articulate)"},
    "fm_lucas": {"name": "Lucas", "gender": "Male", "lang": "fr-fr", "lang_name": "French", "flag": "🇫🇷", "description": "Modern French male speaker (Natural & conversational)"},
    "ff_camille": {"name": "Camille", "gender": "Female", "lang": "fr-fr", "lang_name": "French", "flag": "🇫🇷", "description": "Warm French commercial & podcast presenter"},
    "ff_juliette": {"name": "Juliette", "gender": "Female", "lang": "fr-fr", "lang_name": "French", "flag": "🇫🇷", "description": "Sophisticated French audiobook narrator"},

    # ------------------ 🇯🇵 Japanese (ja - 5 Voices) ------------------
    "jf_alpha": {"name": "Alpha (アルファ)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Clear, gentle anime-style Japanese female voice"},
    "jf_gongitsune": {"name": "Gongitsune (ごんぎつね)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Traditional Japanese storybook narration"},
    "jf_nezumi": {"name": "Nezumi (ねずみ)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Cute, high-energy Japanese character voice"},
    "jf_tebukuro": {"name": "Tebukuro (てぶくろ)", "gender": "Female", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Calm, gentle Japanese audiobook tone"},
    "jm_kumo": {"name": "Kumo (くも)", "gender": "Male", "lang": "ja", "lang_name": "Japanese", "flag": "🇯🇵", "description": "Deep, calm Japanese male narrator"},

    # ------------------ 🇰🇷 Korean (ko - 2 Presets) ------------------
    "kf_minji": {"name": "Minji (민지)", "gender": "Female", "lang": "ko", "lang_name": "Korean", "flag": "🇰🇷", "description": "Natural, friendly Korean female voice"},
    "km_junho": {"name": "Junho (준호)", "gender": "Male", "lang": "ko", "lang_name": "Korean", "flag": "🇰🇷", "description": "Warm, articulate Korean male narrator"},

    # ------------------ 🇨🇳 Mandarin Chinese (cmn - 8 Voices) ------------------
    "zf_xiaobei": {"name": "Xiaobei (小北)", "gender": "Female", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Bright, cheerful Mandarin female voice"},
    "zf_xiaoni": {"name": "Xiaoni (小妮)", "gender": "Female", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Gentle, expressive Mandarin storyteller"},
    "zf_xiaoxiao": {"name": "Xiaoxiao (小小)", "gender": "Female", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Standard broadcast-grade Mandarin female voice"},
    "zf_xiaoyi": {"name": "Xiaoyi (小艺)", "gender": "Female", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Articulate, professional Mandarin presenter"},
    "zm_yunjian": {"name": "Yunjian (云健)", "gender": "Male", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Deep, authoritative Mandarin male voice"},
    "zm_yunxi": {"name": "Yunxi (云希)", "gender": "Male", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Natural, conversational Mandarin male host"},
    "zm_yunxia": {"name": "Yunxia (云夏)", "gender": "Male", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Youthful, energetic Mandarin male tone"},
    "zm_yunyang": {"name": "Yunyang (云扬)", "gender": "Male", "lang": "cmn", "lang_name": "Chinese (Mandarin)", "flag": "🇨🇳", "description": "Calm, refined documentary Mandarin narration"},

    # ------------------ 🇪🇸 Spanish (es - 3 Voices) ------------------
    "ef_dora": {"name": "Dora", "gender": "Female", "lang": "es", "lang_name": "Spanish", "flag": "🇪🇸", "description": "Warm, expressive Spanish narrator"},
    "em_alex": {"name": "Alex", "gender": "Male", "lang": "es", "lang_name": "Spanish", "flag": "🇪🇸", "description": "Clear, dynamic Spanish male voice"},
    "em_santa": {"name": "Papá Noel", "gender": "Male", "lang": "es", "lang_name": "Spanish", "flag": "🇪🇸", "description": "Jovial, warm Spanish baritone"},

    # ------------------ 🇮🇳 Hindi (hi - 4 Voices) ------------------
    "hf_alpha": {"name": "Alpha (अल्फा)", "gender": "Female", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Clear, expressive Hindi female narrator"},
    "hf_beta": {"name": "Beta (बीटा)", "gender": "Female", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Soothing, melodic Hindi voice"},
    "hm_omega": {"name": "Omega (ओमेगा)", "gender": "Male", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Resonant, authoritative Hindi male voice"},
    "hm_psi": {"name": "Psi (साई)", "gender": "Male", "lang": "hi", "lang_name": "Hindi", "flag": "🇮🇳", "description": "Youthful, energetic Hindi storyteller"},

    # ------------------ 🇮🇹 Italian (it - 2 Voices) ------------------
    "if_sara": {"name": "Sara", "gender": "Female", "lang": "it", "lang_name": "Italian", "flag": "🇮🇹", "description": "Lively, melodic, authentic Italian voice"},
    "im_nicola": {"name": "Nicola", "gender": "Male", "lang": "it", "lang_name": "Italian", "flag": "🇮🇹", "description": "Warm, expressive Italian narrator"},

    # ------------------ 🇧🇷 Portuguese (pt-br - 3 Voices) ------------------
    "pf_dora": {"name": "Dora (BR)", "gender": "Female", "lang": "pt-br", "lang_name": "Portuguese (BR)", "flag": "🇧🇷", "description": "Natural, warm Brazilian Portuguese voice"},
    "pm_alex": {"name": "Alex (BR)", "gender": "Male", "lang": "pt-br", "lang_name": "Portuguese (BR)", "flag": "🇧🇷", "description": "Modern, friendly Brazilian narrator"},
    "pm_santa": {"name": "Papai Noel", "gender": "Male", "lang": "pt-br", "lang_name": "Portuguese (BR)", "flag": "🇧🇷", "description": "Warm Brazilian Portuguese storytelling voice"},
}

# Virtual voice mapping for curated character presets
VOICE_STYLE_ALIASES: Dict[str, str] = {
    "fm_alexandre": "bm_george",
    "fm_lucas": "am_michael",
    "ff_camille": "af_bella",
    "ff_juliette": "bf_emma",
    "kf_minji": "af_bella",
    "km_junho": "am_michael",
}

MASTERING_PRESETS = [
    "Clean Studio (Default)",
    "Warm Podcast Host (+Bass)",
    "Deep Cinematic Trailer",
    "Radio Broadcast (Punchy)",
    "Raw Unprocessed",
]


class KokoroStudioEngine:
    """Pro Studio TTS Engine supporting 54+ Multilingual Voices, Voice Blending, and Master EQ."""

    def __init__(self, model_dir: Optional[Path] = None):
        _ensure_engine_deps()
        if model_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
            model_dir = base_dir / "assets" / "kokoro"

        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "kokoro-v1.0.onnx"
        if not self.model_path.exists():
            self.model_path = self.model_dir / "kokoro-v0_19.onnx"

        self.voices_path = self.model_dir / "voices-v1.0.bin"
        if not self.voices_path.exists():
            self.voices_path = self.model_dir / "voices.bin"

        self._kokoro: Optional[Any] = None
        self._is_loaded = False
        self.sample_rate = 24000
        self.g2p = MultilingualG2P()

    def load_model(self) -> bool:
        """
        Load the Kokoro ONNX model with multi-tier memory resiliency.
        Automatically mitigates Windows low-RAM / memory fragmentation 'bad allocation' errors
        by adjusting memory arena allocations, thread pools, and graph optimization levels.
        """
        if self._is_loaded and self._kokoro is not None:
            return True

        if not self.model_path.exists() and not (self.model_dir / "kokoro-v0_19.onnx").exists():
            import urllib.request
            self.model_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading Kokoro ONNX model weights from GitHub Releases...")
            model_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
            urllib.request.urlretrieve(model_url, str(self.model_path))
            logger.info("Kokoro ONNX model downloaded successfully!")

        if not self.voices_path.exists():
            import urllib.request
            self.model_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading Kokoro Voices bundle from GitHub Releases...")
            voices_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
            urllib.request.urlretrieve(voices_url, str(self.voices_path))
            logger.info("Kokoro Voices bundle downloaded successfully!")

        candidate_models = []
        if self.model_path.exists():
            candidate_models.append(self.model_path)
        fallback_model = self.model_dir / "kokoro-v0_19.onnx"
        if fallback_model.exists() and fallback_model not in candidate_models:
            candidate_models.append(fallback_model)

        if not candidate_models:
            raise FileNotFoundError(f"Kokoro model not found in directory: {self.model_dir}")
        if not self.voices_path.exists():
            raise FileNotFoundError(f"Kokoro voices file not found at: {self.voices_path}")

        import gc
        import onnxruntime as rt
        from kokoro_onnx.config import KoKoroConfig
        from kokoro_onnx.tokenizer import Tokenizer

        gc.collect()

        sess = None
        loaded_model_path = None
        last_error = None

        # Multi-tiered fallback loading strategies for constrained / fragmented RAM environments
        strategies = [
            # Tier 1: Standard optimized CPU execution
            {"name": "Standard Optimized", "arena": True, "mem_pattern": True, "threads": min(2, os.cpu_count() or 1), "opt": rt.GraphOptimizationLevel.ORT_ENABLE_BASIC},
            # Tier 2: Low-RAM mode (Disable memory arena to eliminate large contiguous block allocations)
            {"name": "Low-Memory (Arena Disabled)", "arena": False, "mem_pattern": False, "threads": min(2, os.cpu_count() or 1), "opt": rt.GraphOptimizationLevel.ORT_ENABLE_BASIC},
            # Tier 3: Ultra Low-RAM / Zero-opt mode
            {"name": "Minimal RAM (Zero Optimizations)", "arena": False, "mem_pattern": False, "threads": 1, "opt": rt.GraphOptimizationLevel.ORT_DISABLE_ALL},
        ]

        for model_cand in candidate_models:
            for strat in strategies:
                try:
                    gc.collect()
                    opts = rt.SessionOptions()
                    opts.enable_cpu_mem_arena = strat["arena"]
                    opts.enable_mem_pattern = strat["mem_pattern"]
                    opts.graph_optimization_level = strat["opt"]
                    opts.intra_op_num_threads = strat["threads"]
                    opts.inter_op_num_threads = 1
                    opts.execution_mode = rt.ExecutionMode.ORT_SEQUENTIAL

                    sess = rt.InferenceSession(
                        str(model_cand),
                        sess_options=opts,
                        providers=["CPUExecutionProvider"],
                    )
                    loaded_model_path = model_cand
                    logger.info(f"Loaded ONNX model '{model_cand.name}' via strategy: {strat['name']}")
                    break
                except Exception as err:
                    last_error = err
                    logger.warning(f"Failed to load '{model_cand.name}' with {strat['name']}: {err}")
                    gc.collect()
            if sess is not None:
                break

        if sess is None:
            raise RuntimeError(f"Failed to load Kokoro ONNX model across all strategies: {last_error}")

        # Construct Kokoro instance safely using the active resilient session
        kokoro_inst = Kokoro.__new__(Kokoro)
        kokoro_inst.config = KoKoroConfig(str(loaded_model_path), str(self.voices_path), None)
        kokoro_inst.sess = sess
        kokoro_inst.voices = np.load(str(self.voices_path))
        vocab = kokoro_inst._load_vocab(None)
        kokoro_inst.tokenizer = Tokenizer(None, vocab=vocab)

        self._kokoro = kokoro_inst
        self.g2p = MultilingualG2P(tokenizer=self._kokoro.tokenizer)
        self._is_loaded = True
        return True

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @staticmethod
    def get_lang_code_for_voice(voice_key: str) -> str:
        """Map voice key to its default language code."""
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
        elif prefix in ("kf", "km"):
            return "ko"
        elif prefix in ("zf", "zm"):
            return "cmn"
        return "en-us"

    def get_available_voices(self, filter_lang: Optional[str] = None) -> List[Tuple[str, str]]:
        voices = []
        for key, info in VOICE_CATALOG.items():
            if filter_lang and filter_lang not in ("All Languages", "🌐 Auto-Detect Language") and info["lang_name"] != filter_lang:
                continue
            flag = info.get("flag", "🌐")
            label = f"{flag} {info['name']} ({info['gender']}, {info['lang_name']}) — {info['description']}"
            voices.append((key, label))
        return voices

    def get_language_options(self) -> List[str]:
        raw_langs = sorted(list(set(info["lang_name"] for info in VOICE_CATALOG.values())))
        return ["🌐 Auto-Detect Language", "All Languages"] + raw_langs

    def get_voice_style(self, voice_key: str) -> np.ndarray:
        if not self._is_loaded:
            self.load_model()

        actual_key = VOICE_STYLE_ALIASES.get(voice_key, voice_key)
        if actual_key in self._kokoro.voices:
            return self._kokoro.get_voice_style(actual_key)

        # Fallback to Bella if key not found
        logger.warning(f"Voice style '{voice_key}' (mapped '{actual_key}') not found. Defaulting to 'af_bella'.")
        return self._kokoro.get_voice_style("af_bella")

    def blend_voices(self, voice_a: str, voice_b: str, ratio: float = 0.5) -> np.ndarray:
        if not self._is_loaded:
            self.load_model()

        v1 = self.get_voice_style(voice_a)
        v2 = self.get_voice_style(voice_b)

        clamped_ratio = max(0.0, min(1.0, float(ratio)))
        blended = ((1.0 - clamped_ratio) * v1) + (clamped_ratio * v2)
        return blended

    def resolve_speaker_voice(
        self,
        speaker: str,
        lang: Optional[str] = None,
        default_voice: str = "af_bella",
    ) -> Tuple[str, str]:
        """
        Resolve a speaker name/tag and optional language annotation into a canonical voice ID and language code.
        Examples:
            "Bella", None -> ("af_bella", "en-us")
            "Alpha", "ja" -> ("jf_alpha", "ja")
            "Alpha", "hi" -> ("hf_alpha", "hi")
            "Camille", "fr-fr" -> ("ff_camille", "fr-fr")
            "jf_alpha", None -> ("jf_alpha", "ja")
        """
        speaker_clean = speaker.strip()
        spk_lower = speaker_clean.lower()

        # 1. Check if speaker is already an exact voice ID or alias
        if spk_lower in VOICE_CATALOG:
            return spk_lower, VOICE_CATALOG[spk_lower].get("lang", "en-us")
        if spk_lower in VOICE_STYLE_ALIASES:
            v_id = VOICE_STYLE_ALIASES[spk_lower]
            return spk_lower, VOICE_CATALOG.get(v_id, {}).get("lang", "en-us")

        # 2. Match with explicit language if provided
        canonical_lang = MultilingualG2P.canonicalize_lang_code(lang) if lang else None
        if canonical_lang:
            for vid, vinfo in VOICE_CATALOG.items():
                if vinfo.get("lang") == canonical_lang:
                    vname_clean = re.sub(r"\s*\([^)]*\)", "", vinfo.get("name", "")).strip().lower()
                    if spk_lower == vname_clean or spk_lower in vid:
                        return vid, vinfo.get("lang", "en-us")

        # 3. Match without language across all voices
        for vid, vinfo in VOICE_CATALOG.items():
            vname_clean = re.sub(r"\s*\([^)]*\)", "", vinfo.get("name", "")).strip().lower()
            if spk_lower == vname_clean:
                return vid, vinfo.get("lang", "en-us")

        # 4. Fallback to default voice
        fallback_lang = self.get_lang_code_for_voice(default_voice)
        return default_voice, fallback_lang

    def synthesize_text(
        self,
        text: str,
        voice: Union[str, np.ndarray] = "af_bella",
        speed: float = 1.0,
        lang: Optional[str] = "auto",
        master_preset: str = "Clean Studio (Default)",
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Synthesize speech from multilingual text with G2P preprocessing and pause parsing.
        Automatically detects multi-speaker dialogue scripts and routes per-speaker voices & G2P engines.
        """
        if cancellation_check and cancellation_check():
            raise RuntimeError("Synthesis cancelled by client disconnect")

        if not self._is_loaded:
            self.load_model()

        # Check if text contains multi-speaker dialogue lines
        raw_lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        parsed_dialogue = []
        has_dialogue_tags = False

        for raw_line in raw_lines:
            spk, line_lang, clean_line_text = self.g2p.parse_dialogue_line(raw_line)
            if spk is not None:
                has_dialogue_tags = True
                parsed_dialogue.append((spk, line_lang, clean_line_text))
            else:
                parsed_dialogue.append((None, None, raw_line))

        if has_dialogue_tags and len(raw_lines) > 1:
            # Multi-speaker dialogue pipeline
            default_voice_str = voice if isinstance(voice, str) else "af_bella"
            combined_samples = []
            silence_len = int(0.35 * self.sample_rate)
            silence_gap = np.zeros(silence_len, dtype=np.float32)

            for idx, (spk, line_lang, line_content) in enumerate(parsed_dialogue):
                if cancellation_check and cancellation_check():
                    raise RuntimeError("Synthesis cancelled by client disconnect")

                if not line_content:
                    continue

                if spk is not None:
                    cur_voice_id, cur_lang = self.resolve_speaker_voice(
                        spk, lang=line_lang, default_voice=default_voice_str
                    )
                else:
                    cur_voice_id = default_voice_str
                    cur_lang = line_lang if line_lang else (lang if lang != "auto" else self.get_lang_code_for_voice(cur_voice_id))

                # Safeguard: If text contains Japanese Kana/Kanji and not explicitly Mandarin, force ja
                if self.g2p.detect_language(line_content, default_lang=cur_lang) in ("ja", "jp"):
                    cur_lang = "ja"

                if progress_callback:
                    progress_callback(idx / len(parsed_dialogue), f"Synthesizing {spk or 'Speaker'} [{cur_lang}]...")

                # Synthesize individual line with clean text (speaker tag stripped)
                line_samples, _ = self.synthesize_text(
                    text=line_content,
                    voice=cur_voice_id,
                    speed=speed,
                    lang=cur_lang,
                    master_preset="Raw Unprocessed",
                    cancellation_check=cancellation_check,
                )

                if len(line_samples) > 0:
                    if len(combined_samples) > 0:
                        combined_samples.append(silence_gap)
                    combined_samples.append(line_samples)

            if combined_samples:
                final_samples = np.concatenate(combined_samples)
            else:
                final_samples = np.array([], dtype=np.float32)

            if progress_callback:
                progress_callback(1.0, "Dialogue synthesis complete!")

            return final_samples, self.sample_rate

        clean_text = self.g2p.normalize_text(text)
        if not clean_text:
            return np.array([], dtype=np.float32), self.sample_rate

        if cancellation_check and cancellation_check():
            raise RuntimeError("Synthesis cancelled by client disconnect")

        # Determine target voice style vector
        if isinstance(voice, str):
            voice_style = self.get_voice_style(voice)
            voice_lang = self.get_lang_code_for_voice(voice)
        else:
            voice_style = voice
            voice_lang = "en-us"

        # Resolve language code
        target_lang = self.g2p.canonicalize_lang_code(lang, fallback="auto")
        if target_lang == "auto":
            resolved_lang = self.g2p.detect_language(clean_text, default_lang=voice_lang)
        else:
            resolved_lang = target_lang

        # Robust multi-format pause tag pattern
        pause_pattern = re.compile(
            r"(\[(?:pause|break)(?:\s+|:\s*)[0-9.]+\s*(?:s|ms)?\]|<break\s+time=[\"'][0-9.]+\s*(?:s|ms)?[\"']\s*/>)",
            re.IGNORECASE,
        )
        segments = pause_pattern.split(clean_text)

        if len(segments) > 1:
            combined_samples = []
            for idx in range(0, len(segments), 2):
                if cancellation_check and cancellation_check():
                    raise RuntimeError("Synthesis cancelled by client disconnect")

                chunk_text = segments[idx].strip()
                if chunk_text:
                    if progress_callback:
                        progress_callback(0.2 + (0.6 * (idx / len(segments))), "Synthesizing section...")

                    # Multilingual G2P phonemize (preserves mid-phrase flow and prosody)
                    phonemes, chunk_lang = self.g2p.phonemize(chunk_text, lang=resolved_lang, default_lang=voice_lang)
                    if cancellation_check and cancellation_check():
                        raise RuntimeError("Synthesis cancelled by client disconnect")

                    if phonemes:
                        samples, sr = self._kokoro.create(phonemes, voice=voice_style, speed=speed, is_phonemes=True)
                        # Apply 8ms linear fade-in/fade-out to eliminate click/pop boundary artifacts
                        samples = apply_boundary_fades(samples, fade_ms=8.0, sample_rate=self.sample_rate)
                        combined_samples.append(samples)

                if idx + 1 < len(segments):
                    try:
                        tag_str = segments[idx + 1]
                        pause_sec = parse_pause_tag_duration(tag_str)
                        silence_len = int(pause_sec * self.sample_rate)
                        if silence_len > 0:
                            combined_samples.append(np.zeros(silence_len, dtype=np.float32))
                    except Exception:
                        pass

            if combined_samples:
                final_samples = np.concatenate(combined_samples)
            else:
                final_samples = np.array([], dtype=np.float32)
        else:
            if cancellation_check and cancellation_check():
                raise RuntimeError("Synthesis cancelled by client disconnect")

            if progress_callback:
                progress_callback(0.3, "Synthesizing voice...")

            phonemes, _ = self.g2p.phonemize(clean_text, lang=resolved_lang, default_lang=voice_lang)
            if cancellation_check and cancellation_check():
                raise RuntimeError("Synthesis cancelled by client disconnect")

            if phonemes:
                final_samples, _ = self._kokoro.create(phonemes, voice=voice_style, speed=speed, is_phonemes=True)
                final_samples = apply_boundary_fades(final_samples, fade_ms=8.0, sample_rate=self.sample_rate)
            else:
                final_samples = np.array([], dtype=np.float32)

        if progress_callback:
            progress_callback(1.0, "Synthesis complete!")

        return final_samples, self.sample_rate

    def synthesize_speech_with_subtitles(
        self,
        text: str,
        voice: Union[str, np.ndarray] = "af_bella",
        speed: float = 1.0,
        lang: Optional[str] = "auto",
        master_preset: str = "Clean Studio (Default)",
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> Tuple[np.ndarray, int, str]:
        """
        Synthesize speech and generate perfectly synchronized CapCut/Premiere SubRip (.srt) subtitles.
        Handles both Multi-Speaker Drama scripts and Single Speaker multi-sentence paragraphs.
        """
        if cancellation_check and cancellation_check():
            raise RuntimeError("Synthesis cancelled by client disconnect")

        if not self._is_loaded:
            self.load_model()

        raw_lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        parsed_dialogue = []
        has_dialogue_tags = False

        for raw_line in raw_lines:
            spk, line_lang, clean_line_text = self.g2p.parse_dialogue_line(raw_line)
            if spk is not None:
                has_dialogue_tags = True
                parsed_dialogue.append((spk, line_lang, clean_line_text))
            else:
                parsed_dialogue.append((None, None, raw_line))

        segments: List[Dict[str, Any]] = []
        current_time = 0.0

        # ----------------------------------------------------
        # Mode 1: Multi-Speaker Dialogue Script
        # ----------------------------------------------------
        if has_dialogue_tags and len(raw_lines) > 1:
            default_voice_str = voice if isinstance(voice, str) else "af_bella"
            combined_samples = []
            silence_dur = 0.35
            silence_len = int(silence_dur * self.sample_rate)
            silence_gap = np.zeros(silence_len, dtype=np.float32)

            for idx, (spk, line_lang, line_content) in enumerate(parsed_dialogue):
                if cancellation_check and cancellation_check():
                    raise RuntimeError("Synthesis cancelled by client disconnect")

                if not line_content:
                    continue

                # Check for pause tag
                pause_match = re.search(r"(\[(?:pause|break)(?:\s+|:\s*)[0-9.]+\s*(?:s|ms)?\]|<break\s+time=[\"'][0-9.]+\s*(?:s|ms)?[\"']\s*/>)", line_content, re.IGNORECASE)
                if pause_match:
                    p_sec = parse_pause_tag_duration(pause_match.group(1))
                    current_time += p_sec
                    p_len = int(p_sec * self.sample_rate)
                    if p_len > 0:
                        combined_samples.append(np.zeros(p_len, dtype=np.float32))
                    continue

                if spk is not None:
                    cur_voice_id, cur_lang = self.resolve_speaker_voice(
                        spk, lang=line_lang, default_voice=default_voice_str
                    )
                else:
                    cur_voice_id = default_voice_str
                    cur_lang = line_lang if line_lang else (lang if lang != "auto" else self.get_lang_code_for_voice(cur_voice_id))

                if self.g2p.detect_language(line_content, default_lang=cur_lang) in ("ja", "jp"):
                    cur_lang = "ja"

                if progress_callback:
                    progress_callback(idx / len(parsed_dialogue), f"Synthesizing {spk or 'Speaker'} [{cur_lang}]...")

                line_samples, _ = self.synthesize_text(
                    text=line_content,
                    voice=cur_voice_id,
                    speed=speed,
                    lang=cur_lang,
                    master_preset="Raw Unprocessed",
                    cancellation_check=cancellation_check,
                )

                if len(line_samples) > 0:
                    line_samples = apply_boundary_fades(line_samples, fade_ms=8.0, sample_rate=self.sample_rate)
                    dur = float(len(line_samples) / self.sample_rate)
                    seg_start = current_time
                    seg_end = current_time + dur
                    segments.append({
                        "start": seg_start,
                        "end": seg_end,
                        "text": line_content,
                        "speaker": spk,
                    })

                    combined_samples.append(line_samples)
                    current_time = seg_end

                    if idx < len(parsed_dialogue) - 1:
                        combined_samples.append(silence_gap)
                        current_time += silence_dur

            final_samples = np.concatenate(combined_samples) if combined_samples else np.array([], dtype=np.float32)
            srt_content = generate_srt_from_segments(segments)
            return final_samples, self.sample_rate, srt_content

        # ----------------------------------------------------
        # Mode 2: Single Speaker (Sentence & Paragraph Chunking)
        # ----------------------------------------------------
        clean_text = self.g2p.normalize_text(text)
        if not clean_text:
            return np.array([], dtype=np.float32), self.sample_rate, ""

        sentence_chunks = [s.strip() for s in re.split(r"(?<=[.!?。！？\n])\s+", clean_text) if s.strip()]
        if not sentence_chunks:
            sentence_chunks = [clean_text]

        combined_samples = []
        inter_sentence_gap_dur = 0.20
        inter_sentence_gap = np.zeros(int(inter_sentence_gap_dur * self.sample_rate), dtype=np.float32)

        for idx, s_chunk in enumerate(sentence_chunks):
            if cancellation_check and cancellation_check():
                raise RuntimeError("Synthesis cancelled by client disconnect")

            if not s_chunk:
                continue

            if progress_callback:
                progress_callback(idx / len(sentence_chunks), f"Synthesizing sentence {idx+1}...")

            chunk_samples, _ = self.synthesize_text(
                text=s_chunk,
                voice=voice,
                speed=speed,
                lang=lang,
                master_preset="Raw Unprocessed",
                cancellation_check=cancellation_check,
            )

            if len(chunk_samples) > 0:
                chunk_samples = apply_boundary_fades(chunk_samples, fade_ms=8.0, sample_rate=self.sample_rate)
                dur = float(len(chunk_samples) / self.sample_rate)
                seg_start = current_time
                seg_end = current_time + dur
                segments.append({
                    "start": seg_start,
                    "end": seg_end,
                    "text": s_chunk,
                })

                combined_samples.append(chunk_samples)
                current_time = seg_end

                if idx < len(sentence_chunks) - 1:
                    combined_samples.append(inter_sentence_gap)
                    current_time += inter_sentence_gap_dur

        final_samples = np.concatenate(combined_samples) if combined_samples else np.array([], dtype=np.float32)
        srt_content = generate_srt_from_segments(segments)
        return final_samples, self.sample_rate, srt_content

    @staticmethod
    def apply_studio_mastering(audio_seg: AudioSegment, preset: str = "Clean Studio (Default)") -> AudioSegment:
        if preset == "Raw Unprocessed":
            return audio_seg

        processed = audio_seg

        if preset == "Warm Podcast Host (+Bass)":
            processed = processed.low_pass_filter(12000)
            processed = effects.normalize(processed, headroom=1.0)
            processed = processed + 2.5

        elif preset == "Deep Cinematic Trailer":
            processed = effects.normalize(processed, headroom=0.5)
            processed = processed + 3.5

        elif preset == "Radio Broadcast (Punchy)":
            processed = effects.compress_dynamic_range(
                processed,
                threshold=-18.0,
                ratio=4.0,
                attack=5.0,
                release=50.0,
            )
            processed = effects.normalize(processed, headroom=1.0)

        elif preset == "Clean Studio (Default)":
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
        """
        Synthesize multi-speaker drama scripts with per-speaker language detection.
        """
        if not self._is_loaded:
            self.load_model()

        combined_audio = AudioSegment.empty()
        silence = AudioSegment.silent(duration=pause_ms)
        total = len(dialogue_blocks)

        for idx, block in enumerate(dialogue_blocks):
            speaker = block.get("speaker", "Speaker").strip()
            raw_text = block.get("text", "").strip()
            if not raw_text:
                continue

            # Check for inline line qualifiers: e.g. [Bella (fr)]: Bonjour!
            _, inline_lang, line_text = self.g2p.parse_dialogue_line(f"[{speaker}]: {raw_text}")
            text_to_speak = line_text if line_text else raw_text

            voice = speaker_voice_map.get(speaker, "af_bella")
            speed = block.get("speed", default_speed)
            speaker_voice_lang = self.get_lang_code_for_voice(voice)

            # Determine line language
            explicit_lang = block.get("lang") or inline_lang
            if explicit_lang and explicit_lang not in ("auto", "🌐 Auto-Detect Language"):
                lang = self.g2p.canonicalize_lang_code(explicit_lang)
            else:
                lang = self.g2p.detect_language(text_to_speak, default_lang=speaker_voice_lang)

            if progress_callback:
                frac = idx / total
                progress_callback(frac, f"Synthesizing {speaker} [{lang}] ({idx + 1}/{total})...")

            samples, sr = self.synthesize_text(
                text_to_speak,
                voice=voice,
                speed=speed,
                lang=lang,
                master_preset="Raw Unprocessed",
            )
            if len(samples) == 0:
                continue

            audio_seg = self.numpy_to_audiosegment(samples, sr)
            if len(combined_audio) > 0:
                combined_audio += silence
            combined_audio += audio_seg

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
