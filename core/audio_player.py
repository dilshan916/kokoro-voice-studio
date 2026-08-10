"""
Kokoro Studio — Audio Player Module
===================================
Lightweight, thread-safe in-app audio playback via Pygame Mixer.
"""

from __future__ import annotations

import io
import os
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

import pygame


class AudioPlayer:
    """Controls in-app audio playback with play, pause, stop, and volume."""

    def __init__(self):
        self._is_initialized = False
        self._is_paused = False
        self._current_file: Optional[Path] = None
        self._temp_files = []
        self._init_mixer()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=1024)
            self._is_initialized = True
        except Exception as e:
            print(f"Warning: Could not initialize Pygame mixer: {e}")
            self._is_initialized = False

    def play_file(self, file_path: Path | str) -> bool:
        """Load and play an audio file from disk."""
        if not self._is_initialized:
            self._init_mixer()

        file_path = Path(file_path)
        if not file_path.exists():
            return False

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            self._is_paused = False
            self._current_file = file_path
            return True
        except Exception as e:
            print(f"Failed to play audio file: {e}")
            return False

    def play_segment(self, audio_segment) -> bool:
        """Play a pydub AudioSegment directly from memory."""
        try:
            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_wav.close()
            audio_segment.export(temp_wav.name, format="wav")
            self._temp_files.append(temp_wav.name)
            return self.play_file(temp_wav.name)
        except Exception as e:
            print(f"Failed to play audio segment: {e}")
            return False

    def pause(self):
        """Pause playback."""
        if self._is_initialized and pygame.mixer.music.get_busy() and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True

    def unpause(self):
        """Resume playback from pause."""
        if self._is_initialized and self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False

    def toggle_pause(self):
        """Toggle between play and pause."""
        if self._is_paused:
            self.unpause()
        else:
            self.pause()

    def stop(self):
        """Stop playback completely."""
        if self._is_initialized:
            pygame.mixer.music.stop()
            self._is_paused = False

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        if self._is_initialized:
            clamped = max(0.0, min(1.0, float(volume)))
            pygame.mixer.music.set_volume(clamped)

    def is_playing(self) -> bool:
        """Check if audio is actively playing."""
        if not self._is_initialized:
            return False
        return pygame.mixer.music.get_busy() and not self._is_paused

    def is_paused(self) -> bool:
        return self._is_paused

    def cleanup(self):
        """Stop playback and delete temporary files."""
        self.stop()
        for temp_path in self._temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
        self._temp_files.clear()
