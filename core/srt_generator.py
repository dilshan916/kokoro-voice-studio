"""
Kokoro Studio — Subtitle (.SRT / .VTT) Generator
================================================
Generates time-synchronized caption files for video editors (CapCut, Premiere, DaVinci).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List


class SubtitleGenerator:
    """Creates formatted .srt and .vtt caption files from speech segment metadata."""

    @staticmethod
    def format_timestamp_srt(seconds: float) -> str:
        """Format seconds into HH:MM:SS,mmm for SubRip (.srt)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def format_timestamp_vtt(seconds: float) -> str:
        """Format seconds into HH:MM:SS.mmm for WebVTT (.vtt)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @classmethod
    def generate_srt(cls, segments: List[Dict[str, Any]], output_path: Path) -> Path:
        """Generate a standard .srt file from a list of segments.

        Each segment must have: {"start_sec": float, "end_sec": float, "text": str, "speaker": Optional[str]}
        """
        output_path = Path(output_path)
        lines = []

        for idx, seg in enumerate(segments, start=1):
            start = float(seg.get("start_sec", 0.0))
            end = float(seg.get("end_sec", start))
            # Minimum 1.0s duration floor to eliminate subtitle flicker
            if end - start < 1.0:
                end = start + 1.0

            start_str = cls.format_timestamp_srt(start)
            end_str = cls.format_timestamp_srt(end)
            speaker = seg.get("speaker")
            text = seg.get("text", "").strip()

            if speaker:
                display_text = f"[{speaker}]: {text}"
            else:
                display_text = text

            lines.append(str(idx))
            lines.append(f"{start_str} --> {end_str}")
            lines.append(display_text)
            lines.append("")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_path
