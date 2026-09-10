"""
SayTTS — Unified Base TTS Engine Interface
===========================================
Defines the standard contract for all neural TTS engines (Kokoro, Pocket TTS, etc.).
Every engine must expose uniform lifecycle, status, and synthesis methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Tuple, Union
import numpy as np


class BaseTTSEngine(ABC):
    """Abstract base class for all speech synthesis engines in SayTTS."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Friendly identifier for the engine (e.g. 'kokoro', 'pocket')."""
        pass

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Output audio sample rate in Hz (e.g. 24000)."""
        pass

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """True if the model weights are loaded in memory and ready for inference."""
        pass

    @abstractmethod
    def load_model(self) -> bool:
        """Load model weights into memory. Returns True on success."""
        pass

    @abstractmethod
    def synthesize_text(
        self,
        text: str,
        voice: Union[str, Any] = "default",
        speed: float = 1.0,
        lang: Optional[str] = "auto",
        master_preset: str = "Raw Unprocessed",
        progress_callback: Optional[Callable[[float, str], None]] = None,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, int]:
        """
        Synthesize speech from input text.
        
        Returns:
            Tuple of (audio_samples: np.ndarray, sample_rate: int)
            audio_samples must be a 1D float32 numpy array normalized in [-1.0, 1.0].
        """
        pass
