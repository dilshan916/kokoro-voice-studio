"""
Kokoro Studio — Production FastAPI Backend Server
=================================================
Hardened, high-performance multilingual TTS & mastering backend powered by Kokoro-82M ONNX.
Featuring:
- Server-issued anonymous session authorization (HttpOnly secure cookie + X-Device-Token)
- Strict account isolation & high-entropy recovery keys
- Dual-worker architecture: Worker 1 (interactive <= 3k/6k) & Worker 2 (batch jobs <= 25k)
- Bounded queues (sync: 20, batch: 50) and cooperative client disconnect cancellation
- 128-bit audio filename entropy with authenticated ownership and 2-hour TTL retention
- Zero plaintext API keys at rest or in API responses
- License brute-force lockout defense
- CORS origin restriction & OpenAPI schema exclusion for administrative routes
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import datetime
import hashlib
import io
import logging
import math
import multiprocessing as mp
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import uuid

import numpy as np
from pydantic import BaseModel, Field
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Header, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from core.billing_db import billing_db
from core.kokoro_engine import MASTERING_PRESETS, VOICE_CATALOG

# ============================================================================
# Paths, Directories & Logging Setup
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"

for d in (ASSETS_DIR, OUTPUT_DIR, DATA_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("kokoro-server")

# Security & Policy Constants
COOKIE_NAME = "saytts_session"
DEFAULT_ARTIFACT_TTL = 7200  # 2 hours
MAX_FREE_CHARS_SYNC = 3000
MAX_PRO_CHARS_SYNC = 6000
MAX_PRO_CHARS_ASYNC = 25000
MAX_INTERACTIVE_QUEUE = 20
MAX_BATCH_QUEUE = 50

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
ADMIN_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "")

# In-memory tracking for free-tier concurrency enforcement (1 active render per session)
active_free_renders: Set[str] = set()

# ============================================================================
# Pydantic Request & Response Schemas
# ============================================================================

class RenderRequest(BaseModel):
    text: str = Field(..., description="Input text to synthesize", min_length=1, max_length=25000)
    voice_id: str = Field("af_bella", description="Voice ID from the voice catalog")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier (0.5 to 2.0)")
    lang: Optional[str] = Field("auto", description="Target language code or 'auto'")
    eq_preset: Optional[str] = Field("Clean Studio (Default)", description="Acoustic mastering EQ preset")
    output_format: Optional[str] = Field("wav", description="Audio container format ('wav' or 'mp3')")
    pause_punctuation_ms: Optional[int] = Field(150, ge=0, le=2000, description="Pause after punctuation marks (ms)")
    pause_paragraph_ms: Optional[int] = Field(400, ge=0, le=5000, description="Pause between paragraphs (ms)")
    device_id: Optional[str] = Field(None, description="Deprecated client identifier (ignored for auth)")

class CreateTTSJobRequest(BaseModel):
    text: str = Field(..., description="Input text for asynchronous batch rendering", min_length=1, max_length=25000)
    voice_id: str = Field("af_bella", description="Voice ID from the voice catalog")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier (0.5 to 2.0)")
    lang: Optional[str] = Field("auto", description="Target language code or 'auto'")
    eq_preset: Optional[str] = Field("Clean Studio (Default)", description="Acoustic mastering EQ preset")
    output_format: Optional[str] = Field("wav", description="Audio container format ('wav' or 'mp3')")
    pause_punctuation_ms: Optional[int] = Field(150, ge=0, le=2000)
    pause_paragraph_ms: Optional[int] = Field(400, ge=0, le=5000)

class RedeemLicenseRequest(BaseModel):
    code: str = Field(..., description="VIP promo or license key code", min_length=4, max_length=64)
    device_id: Optional[str] = Field(None, description="Deprecated (ignored, session used)")

class CreateCheckoutRequest(BaseModel):
    return_url: Optional[str] = None
    tier: str = Field("pro", description="Requested tier")
    device_id: Optional[str] = Field(None, description="Deprecated (ignored, session used)")

class GrantProRequest(BaseModel):
    device_id: str = Field(..., min_length=3)
    tier: str = Field("pro")
    note: Optional[str] = None

class CreateLicenseKeyRequest(BaseModel):
    code: Optional[str] = None
    tier: str = Field("pro")
    max_uses: int = Field(1, ge=1, le=1000)
    note: Optional[str] = None

class ToggleAutoRenewRequest(BaseModel):
    cancel_at_period_end: bool = Field(..., description="True to cancel renewal at period end")
    device_id: Optional[str] = Field(None, description="Deprecated (ignored, session used)")

class CancelSubscriptionRequest(BaseModel):
    immediate: bool = Field(False, description="True to cancel immediately, False at period end")
    device_id: Optional[str] = Field(None, description="Deprecated (ignored, session used)")

class OpenAISpeechRequest(BaseModel):
    model: str = Field("kokoro", description="Model identifier ('kokoro', 'tts-1')")
    input: str = Field(..., description="Text to synthesize", min_length=1, max_length=25000)
    voice: str = Field("alloy", description="Voice identifier")
    response_format: str = Field("mp3", description="Audio format ('mp3', 'wav', 'aac', 'flac', 'opus')")
    speed: float = Field(1.0, ge=0.25, le=4.0, description="Speech rate multiplier")
    eq_preset: Optional[str] = Field(None, description="EQ preset")
    lang: Optional[str] = Field("auto", description="Language code")
    pause_punctuation_ms: Optional[int] = Field(150)
    pause_paragraph_ms: Optional[int] = Field(400)

class CreateApiKeyRequest(BaseModel):
    name: str = Field("Default API Key", max_length=60)
    device_id: Optional[str] = Field(None, description="Deprecated (ignored, session used)")

class RecoverAccountRequest(BaseModel):
    recovery_key: str = Field(..., min_length=16, description="192-bit Pro account recovery key")

class RenderResponse(BaseModel):
    success: bool
    audio_path: str
    audio_url: str
    filename: str
    duration: float
    sample_rate: int
    file_size_bytes: int
    voice_id: str
    voice_name: str
    lang_resolved: str
    eq_preset: str
    audio_base64: Optional[str] = None
    srt_content: Optional[str] = None
    srt_filename: Optional[str] = None

class VoiceMetadata(BaseModel):
    id: str
    name: str
    gender: str
    lang: str
    lang_name: str
    flag: str
    description: str

class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
    voices_count: int
    output_directory: str
    supported_languages: List[Dict[str, str]]
    mastering_presets: List[str]
    voices: List[VoiceMetadata]


# ============================================================================
# Subtitle & CJK Helpers
# ============================================================================

def format_srt_timestamp(seconds: float) -> str:
    """Format seconds into SubRip timestamp: HH:MM:SS,mmm"""
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


def is_cjk_text(text: str) -> bool:
    """Detect if string contains Chinese, Japanese, or Korean characters."""
    return bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text))


def split_cjk_clause(clause: str, max_chars: int = 18) -> List[str]:
    """Break long CJK clauses into readable subtitle chunks."""
    clause = clause.strip()
    if not clause:
        return []
    if len(clause) <= max_chars:
        return [clause]
    sub_parts = re.split(r"([，、；：\s]+)", clause)
    chunks = []
    current = ""
    for part in sub_parts:
        if not part:
            continue
        if len(current) + len(part) <= max_chars:
            current += part
        else:
            if current.strip():
                chunks.append(current.strip())
            current = part
    if current.strip():
        chunks.append(current.strip())

    final_chunks = []
    for c in chunks:
        if len(c) > max_chars:
            for i in range(0, len(c), max_chars):
                sub = c[i : i + max_chars].strip()
                if sub:
                    final_chunks.append(sub)
        else:
            final_chunks.append(c)
    return final_chunks


def split_clause_into_balanced_chunks(
    clause: str, max_words: int = 6, max_chars: int = 34
) -> List[str]:
    """
    Split clause into balanced, punchy vertical-video chunks (Shorts / Reels / TikTok).
    Eliminates 1-2 word orphan tails, breaks on natural conjunctions/prepositions,
    and preserves 17-20 characters-per-second reading cadence.
    """
    words = clause.strip().split()
    if not words:
        return []

    # If the clause fits naturally without visual crowding, keep it intact
    if len(words) <= max_words and len(clause) <= max_chars:
        return [clause.strip()]

    conjunctions = {
        "and", "but", "or", "so", "because", "when", "while", "if", "that",
        "which", "rather", "than", "where", "then", "as", "with", "to", "for", "in", "on"
    }

    total_words = len(words)
    num_chunks = max(math.ceil(total_words / max_words), math.ceil(len(clause) / max_chars), 2)
    target_words = total_words // num_chunks

    chunks = []
    current = []

    for idx, w in enumerate(words):
        current.append(w)
        words_left = total_words - (idx + 1)
        cur_text = " ".join(current)
        cur_len = len(cur_text)

        if words_left == 0:
            break

        tail_words = words[idx + 1:]
        tail_text = " ".join(tail_words)
        tail_len = len(tail_text)

        # If remaining words are only 1 or 2 words, absorb unless hard cap is reached
        if words_left <= 2 and (cur_len + 1 + tail_len) <= max_chars + 6:
            continue

        next_w = words[idx + 1].lower().rstrip(",.!?")
        is_natural_boundary = (next_w in conjunctions and len(current) >= max(2, target_words - 1))

        hit_hard_limit = (len(current) >= max_words or cur_len >= max_chars)
        hit_natural_split = (len(current) >= target_words and is_natural_boundary and words_left >= 2)
        hit_target = (len(current) >= target_words and cur_len >= 20 and words_left >= 2)

        if (hit_hard_limit or hit_natural_split or hit_target) and words_left >= 2:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


def merge_micro_clauses(clauses: List[str], max_chars: int = 34) -> List[str]:
    """
    Merge 1-2 word micro-clauses (e.g. 'Yes,', 'Well,', 'In fact,') into adjacent
    clauses so they don't produce orphaned flickering subtitle cards.
    """
    if len(clauses) <= 1:
        return clauses

    merged: List[str] = []
    i = 0
    while i < len(clauses):
        cur = clauses[i].strip()
        words = cur.split()

        # If this is a micro-clause (<= 2 words or <= 12 chars), merge forward if it fits
        if (len(words) <= 2 or len(cur) <= 12) and i < len(clauses) - 1:
            nxt = clauses[i + 1].strip()
            if len(cur) + 1 + len(nxt) <= max_chars:
                merged.append(f"{cur} {nxt}")
                i += 2
                continue

        # If it's a trailing micro-clause at the end, merge backwards if it fits
        if (len(words) <= 2 or len(cur) <= 12) and i == len(clauses) - 1 and merged:
            prev = merged[-1]
            if len(prev) + 1 + len(cur) <= max_chars + 6:
                merged[-1] = f"{prev} {cur}"
                i += 1
                continue

        merged.append(cur)
        i += 1

    return merged


def split_text_into_punchy_srt_chunks(
    text: str, max_words: int = 6, max_chars: int = 34
) -> List[str]:
    """Build subtitle chunk list formatted for video creators."""
    clean = re.sub(
        r"(\[(?:pause|break)(?:\s+|:\s*)[0-9.]+\s*(?:s|ms)?\]|<break\s+time=[\"'][0-9.]+\s*(?:s|ms)?[\"']\s*/>)",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return []

    cjk_mode = is_cjk_text(clean)
    raw_clauses = [
        c.strip()
        for c in re.split(r"(?<=[.!?,;:—\n。！？，；：])\s*", clean)
        if c.strip()
    ]
    if not raw_clauses:
        raw_clauses = [clean]

    # Pre-merge micro-clauses before chunking (garse punctuation-first recommendation)
    clauses = merge_micro_clauses(raw_clauses, max_chars=max_chars)

    all_chunks = []
    for cl in clauses:
        if cjk_mode:
            all_chunks.extend(split_cjk_clause(cl, max_chars=18))
        else:
            all_chunks.extend(split_clause_into_balanced_chunks(cl, max_words, max_chars))

    return all_chunks or [clean]


def calculate_chunk_acoustic_weight(chunk: str) -> float:
    """Estimate speech duration weight of a text chunk with natural pauses."""
    chars = len(chunk)
    words = len(chunk.split())
    # Baseline acoustic weighting: ~0.055s per character (18 CPS target)
    weight = float(max(chars, words * 4))
    if re.search(r"[.!?。！？]$", chunk.strip()):
        weight += 6.0  # sentence end pause
    elif re.search(r"[,;:\-—，；：]$", chunk.strip()):
        weight += 3.0  # clause boundary pause
    return max(weight, 2.0)


def build_srt_subtitles(
    text: str,
    total_duration: float,
    max_words: int = 6,
    max_chars: int = 34,
    max_chunk_dur: float = 3.5,
    min_chunk_dur: float = 1.1,  # 1.1s minimum duration floor (anti-flicker per garse advice)
) -> str:
    """Generate perfectly synchronized, vertical-video optimized SubRip (.srt) subtitles."""
    chunks = split_text_into_punchy_srt_chunks(text, max_words, max_chars)
    if not chunks or total_duration <= 0.05:
        return f"1\n00:00:00,000 --> {format_srt_timestamp(max(total_duration, 1.0))}\n{text.strip()}\n"

    weights = [calculate_chunk_acoustic_weight(c) for c in chunks]
    total_w = sum(weights)

    # Floor scales down gracefully if total audio is shorter than num_chunks * min_chunk_dur
    effective_floor = min(min_chunk_dur, total_duration / len(chunks)) if len(chunks) > 0 else min_chunk_dur

    raw_durations = [(w / total_w) * total_duration for w in weights]
    floored_durations = [max(d, effective_floor) for d in raw_durations]

    # Proportional scaling to match total_duration exactly
    floored_total = sum(floored_durations)
    if floored_total > 0:
        scaled_durations = [(d / floored_total) * total_duration for d in floored_durations]
    else:
        scaled_durations = raw_durations

    srt_lines = []
    current_time = 0.0

    for idx, (chunk, dur) in enumerate(zip(chunks, scaled_durations), 1):
        if idx == len(chunks):
            dur = max(0.2, total_duration - current_time)

        start_ts = format_srt_timestamp(current_time)
        end_time = min(current_time + dur, total_duration)
        end_ts = format_srt_timestamp(end_time)
        srt_lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{chunk}\n")
        current_time = end_time

    return "\n".join(srt_lines).strip() + "\n"


# ============================================================================
# Background Worker Process (Isolated OS Process)
# ============================================================================

def _engine_worker_loop(
    task_queue: mp.Queue,
    response_queue: mp.Queue,
    model_dir: str,
    output_dir: str,
    cancellation_dict: Any,
    worker_name: str = "worker",
) -> None:
    """
    Dedicated background worker process.
    Loads ONNX weights with 2 intra-op threads and executes synthesis tasks.
    Supports cooperative disconnect cancellation at pipeline checkpoints.
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        from core.kokoro_engine import KokoroStudioEngine
        engine = KokoroStudioEngine(model_dir=Path(model_dir))
        engine.load_model()
        response_queue.put({"type": "INIT_DONE", "worker": worker_name, "success": True})
        logger.info(f"Kokoro Engine worker [{worker_name}] initialized successfully.")
    except Exception as e:
        err_msg = f"{type(e).__name__}: {str(e) or repr(e)}"
        response_queue.put({"type": "INIT_DONE", "worker": worker_name, "success": False, "error": err_msg})
        logger.error(f"Kokoro Engine worker [{worker_name}] initialization failed: {err_msg}")
        return

    while True:
        try:
            task = task_queue.get()
            if not isinstance(task, dict):
                continue

            msg_type = task.get("type", "RENDER")
            if msg_type == "STOP":
                logger.info(f"Worker [{worker_name}] received STOP signal. Exiting.")
                break

            req_id = task.get("id")
            is_job = task.get("is_job", False)
            job_id = task.get("job_id")
            device_id = task.get("device_id", "dev_anonymous")

            # Checkpoint 0: Cancelled before pickup
            if cancellation_dict.get(req_id, False) or (job_id and cancellation_dict.get(job_id, False)):
                logger.info(f"Task {req_id or job_id} cancelled prior to worker execution.")
                response_queue.put({
                    "type": "JOB_DONE" if is_job else "RENDER_DONE",
                    "id": req_id,
                    "job_id": job_id,
                    "device_id": device_id,
                    "success": False,
                    "cancelled": True,
                    "error": "Synthesis cancelled before execution",
                })
                continue

            def cancellation_check() -> bool:
                if cancellation_dict.get(req_id, False):
                    return True
                if job_id and cancellation_dict.get(job_id, False):
                    return True
                return False

            text = task.get("text", "")
            voice_id = task.get("voice_id", "af_bella")
            speed = float(task.get("speed", 1.0))
            lang = task.get("lang", "auto")
            eq_preset = task.get("eq_preset", "Clean Studio (Default)")
            out_format = task.get("output_format", "wav").lower().strip()

            try:
                # Checkpoint 1: In-synthesis check
                samples, sr = engine.synthesize_text(
                    text=text,
                    voice=voice_id,
                    speed=speed,
                    lang=lang,
                    master_preset="Raw Unprocessed",
                    cancellation_check=cancellation_check,
                )

                # Checkpoint 2: Post-synthesis / Pre-mastering check
                if cancellation_check():
                    raise RuntimeError("Synthesis cancelled by client disconnect")

                audio_seg = engine.numpy_to_audiosegment(samples, sr)
                if eq_preset != "Raw Unprocessed":
                    audio_seg = engine.apply_studio_mastering(audio_seg, preset=eq_preset)

                # Checkpoint 3: Pre-export check
                if cancellation_check():
                    raise RuntimeError("Synthesis cancelled by client disconnect")

                dur = float(len(audio_seg) / 1000.0)
                srt_content = build_srt_subtitles(
                    text=text,
                    total_duration=dur,
                    max_words=6,
                    max_chars=34,
                    max_chunk_dur=3.5,
                    min_chunk_dur=1.1,
                )

                # Checkpoint 4: Final pre-write check
                if cancellation_check():
                    raise RuntimeError("Synthesis cancelled by client disconnect")

                # Generate 128-bit secure identifier
                token_id = secrets.token_urlsafe(16)
                safe_voice = re.sub(r"[^\w\-]", "_", voice_id)
                base_name = f"kokoro_{safe_voice}_{token_id}"
                file_ext = "mp3" if out_format == "mp3" else "wav"
                filename = f"{base_name}.{file_ext}"
                file_dest = out_path / filename

                engine.export_audio(audio_seg, output_path=file_dest, format=file_ext)

                srt_filename = f"{base_name}.srt"
                srt_dest = out_path / srt_filename
                with open(srt_dest, "w", encoding="utf-8") as f:
                    f.write(srt_content)

                file_size = os.path.getsize(file_dest)

                # Base64 for instant browser audio playback
                audio_b64 = None
                if file_size < 10 * 1024 * 1024:  # Only for files under 10MB
                    with open(file_dest, "rb") as f:
                        import base64
                        audio_b64 = base64.b64encode(f.read()).decode("ascii")

                v_meta = VOICE_CATALOG.get(voice_id, {})
                voice_name = v_meta.get("name", voice_id)
                resolved_lang = lang if lang != "auto" else v_meta.get("lang", "en-us")

                response_queue.put({
                    "type": "JOB_DONE" if is_job else "RENDER_DONE",
                    "id": req_id,
                    "job_id": job_id,
                    "device_id": device_id,
                    "success": True,
                    "cancelled": False,
                    "audio_path": str(file_dest.resolve()),
                    "filename": filename,
                    "base_name": base_name,
                    "file_ext": file_ext,
                    "duration": round(dur, 2),
                    "sample_rate": sr,
                    "file_size_bytes": file_size,
                    "voice_id": voice_id,
                    "voice_name": voice_name,
                    "lang_resolved": resolved_lang,
                    "eq_preset": eq_preset,
                    "audio_base64": audio_b64,
                    "srt_content": srt_content,
                    "srt_filename": srt_filename,
                })

            except Exception as task_err:
                is_cancelled = "cancelled" in str(task_err).lower()
                response_queue.put({
                    "type": "JOB_DONE" if is_job else "RENDER_DONE",
                    "id": req_id,
                    "job_id": job_id,
                    "device_id": device_id,
                    "success": False,
                    "cancelled": is_cancelled,
                    "error": str(task_err),
                })

        except Exception as queue_err:
            logger.error(f"Worker [{worker_name}] queue loop error: {queue_err}")


# ============================================================================
# Dual-Worker Process Manager (Async Bridge in FastAPI)
# ============================================================================

class EngineProcessManager:
    """
    Manages dual background workers:
    - Worker 1: Interactive synchronous renders (queue bounded at 20)
    - Worker 2: Long-running Pro batch jobs (queue bounded at 50)
    Tracks futures and coordinates shared cross-process disconnect cancellations.
    """

    def __init__(self):
        self.sync_queue: Optional[mp.Queue] = None
        self.batch_queue: Optional[mp.Queue] = None
        self.response_queue: Optional[mp.Queue] = None
        self.mp_manager: Optional[Any] = None
        self.cancellation_dict: Optional[Any] = None
        self.worker_sync: Optional[mp.Process] = None
        self.worker_batch: Optional[mp.Process] = None
        self.is_ready: bool = False
        self.init_error: Optional[str] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listener_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready_workers: Set[str] = set()

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start dual workers and the IPC response listener."""
        import threading
        self._loop = loop
        self.sync_queue = mp.Queue(maxsize=MAX_INTERACTIVE_QUEUE)
        self.batch_queue = mp.Queue(maxsize=MAX_BATCH_QUEUE)
        self.response_queue = mp.Queue()

        self.mp_manager = mp.Manager()
        self.cancellation_dict = self.mp_manager.dict()

        # Worker 1: Interactive Short Renders
        self.worker_sync = mp.Process(
            target=_engine_worker_loop,
            args=(
                self.sync_queue,
                self.response_queue,
                str(ASSETS_DIR),
                str(OUTPUT_DIR),
                self.cancellation_dict,
                "worker_sync",
            ),
            daemon=True,
        )
        self.worker_sync.start()

        # Worker 2: Pro Batch Jobs
        self.worker_batch = mp.Process(
            target=_engine_worker_loop,
            args=(
                self.batch_queue,
                self.response_queue,
                str(ASSETS_DIR),
                str(OUTPUT_DIR),
                self.cancellation_dict,
                "worker_batch",
            ),
            daemon=True,
        )
        self.worker_batch.start()

        logger.info(
            f"Spawned dual Kokoro Engine workers: Sync PID {self.worker_sync.pid}, Batch PID {self.worker_batch.pid}"
        )

        self._listener_thread = threading.Thread(target=self._response_listener, daemon=True)
        self._listener_thread.start()

    def _response_listener(self) -> None:
        """Reads responses from worker processes and resolves Futures or updates DB records."""
        while True:
            try:
                if self.response_queue is None:
                    break
                msg = self.response_queue.get()
                if not isinstance(msg, dict):
                    continue

                m_type = msg.get("type")

                if m_type == "INIT_DONE":
                    w_name = msg.get("worker", "worker")
                    if msg.get("success"):
                        self._ready_workers.add(w_name)
                        logger.info(f"Worker [{w_name}] reported READY.")
                        if len(self._ready_workers) >= 1:
                            self.is_ready = True
                    else:
                        self.init_error = msg.get("error", "Unknown worker init error")
                        logger.error(f"Worker [{w_name}] failed: {self.init_error}")
                    continue

                if m_type == "RENDER_DONE":
                    req_id = msg.get("id")
                    if req_id and req_id in self._pending_requests:
                        fut = self._pending_requests.pop(req_id)
                        if not fut.done() and self._loop:
                            self._loop.call_soon_threadsafe(fut.set_result, msg)
                    continue

                if m_type == "JOB_DONE":
                    job_id = msg.get("job_id")
                    device_id = msg.get("device_id")
                    if job_id:
                        if msg.get("success"):
                            filename = msg.get("filename")
                            base_name = msg.get("base_name")
                            file_ext = msg.get("file_ext", "wav")
                            file_size = msg.get("file_size_bytes", 0)
                            audio_url = f"/audio/{filename}"

                            # Record artifact ownership
                            billing_db.record_audio_artifact(
                                file_id=base_name,
                                device_id=device_id,
                                filename=filename,
                                format=file_ext,
                                file_size=file_size,
                                ttl_seconds=DEFAULT_ARTIFACT_TTL,
                            )
                            billing_db.update_tts_job(
                                job_id=job_id,
                                status="COMPLETED",
                                filename=filename,
                                audio_url=audio_url,
                                progress=1.0,
                            )
                            logger.info(f"Async Job {job_id} COMPLETED for device {device_id}")
                        elif msg.get("cancelled"):
                            billing_db.update_tts_job(
                                job_id=job_id,
                                status="CANCELLED",
                                error_message="Job was cancelled",
                            )
                            logger.info(f"Async Job {job_id} CANCELLED")
                        else:
                            billing_db.update_tts_job(
                                job_id=job_id,
                                status="FAILED",
                                error_message=msg.get("error", "Rendering error"),
                            )
                            logger.warning(f"Async Job {job_id} FAILED: {msg.get('error')}")
                    continue

            except Exception as e:
                logger.error(f"Error in response listener thread: {e}")
                break

    async def render_sync_async(
        self, payload: Dict[str, Any], timeout_sec: float = 240.0
    ) -> Dict[str, Any]:
        """Submits task to Worker 1 (interactive queue bounded at 20)."""
        if self.init_error and not self.is_ready:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Engine worker failed to initialize: {self.init_error}",
            )

        if not self.is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kokoro model is loading in background. Please retry in a few moments.",
            )

        req_id = payload.get("id") or str(uuid.uuid4())
        payload["id"] = req_id
        payload["type"] = "RENDER"
        payload["is_job"] = False

        future = self._loop.create_future()
        self._pending_requests[req_id] = future

        try:
            self.sync_queue.put_nowait(payload)
        except queue.Full:
            self._pending_requests.pop(req_id, None)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Interactive TTS queue is full (max 20 concurrent tasks). Please try again shortly.",
            )

        try:
            result = await asyncio.wait_for(future, timeout=timeout_sec)
            if result.get("cancelled"):
                raise HTTPException(
                    status_code=499,
                    detail="Synthesis cancelled by client disconnect",
                )
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Speech rendering failed inside engine worker"),
                )
            return result
        except asyncio.TimeoutError:
            self.cancellation_dict[req_id] = True
            self._pending_requests.pop(req_id, None)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Audio rendering timed out after {timeout_sec}s. Try a shorter script or faster speed.",
            )
        except asyncio.CancelledError:
            self.cancellation_dict[req_id] = True
            self._pending_requests.pop(req_id, None)
            raise

    def submit_batch_job(self, payload: Dict[str, Any]) -> None:
        """Submits long-form async task to Worker 2 (batch queue bounded at 50)."""
        if not self.is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kokoro model is loading in background. Please retry in a few moments.",
            )

        payload["type"] = "RENDER"
        payload["is_job"] = True

        try:
            self.batch_queue.put_nowait(payload)
        except queue.Full:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Batch job queue is full (max 50 queued tasks). Please try again shortly.",
            )

    def shutdown(self) -> None:
        """Gracefully terminate background workers on server shutdown."""
        logger.info("Shutting down Kokoro Engine workers...")
        for q in (self.sync_queue, self.batch_queue):
            if q:
                try:
                    q.put({"type": "STOP"})
                except Exception:
                    pass

        for w in (self.worker_sync, self.worker_batch):
            if w and w.is_alive():
                w.terminate()
                w.join(timeout=2.0)

        if self.mp_manager:
            try:
                self.mp_manager.shutdown()
            except Exception:
                pass

# Global engine manager instance
engine_manager = EngineProcessManager()


# ============================================================================
# Background Retention Task & FastAPI Lifespan
# ============================================================================

async def audio_retention_loop():
    """Application-aware artifact retention worker: runs every 15 mins."""
    while True:
        try:
            await asyncio.sleep(900)  # 15 minutes
            cleaned = billing_db.cleanup_expired_artifacts(OUTPUT_DIR, max_age_seconds=DEFAULT_ARTIFACT_TTL)
            if cleaned > 0:
                logger.info(f"Audio Retention: Pruned {cleaned} expired audio files (>2h old).")

            # Emergency disk check: if free disk < 5GB, prune files older than 30 mins
            total, used, free = shutil.disk_usage(OUTPUT_DIR)
            if free < 5 * 1024 * 1024 * 1024:
                logger.warning(f"Disk space low ({free // (1024*1024)} MB free). Running emergency prune (>30m).")
                billing_db.cleanup_expired_artifacts(OUTPUT_DIR, max_age_seconds=1800)
        except asyncio.CancelledError:
            break
        except Exception as err:
            logger.error(f"Error in audio retention loop: {err}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start workers and retention loop on startup; shut down on exit."""
    loop = asyncio.get_running_loop()
    engine_manager.start(loop)
    cleanup_task = asyncio.create_task(audio_retention_loop())
    yield
    cleanup_task.cancel()
    engine_manager.shutdown()


# ============================================================================
# FastAPI Application & Restricted CORS Configuration
# ============================================================================

app = FastAPI(
    title="Kokoro Voice Studio Pro — Backend API",
    description="Production hardened multilingual TTS & mastering backend powered by Kokoro-82M ONNX.",
    version="2.6.0",
    lifespan=lifespan,
)

# Strict CORS origin allowlist (disallows wildcard with credentials)
ALLOWED_ORIGINS = [
    "https://saytts.site",
    "https://www.saytts.site",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)


def get_client_ip(request: Request) -> str:
    """Extract authenticated client IP prioritizing trusted Nginx X-Real-IP header."""
    return (
        request.headers.get("x-real-ip")
        or request.headers.get("X-Real-IP")
        or (request.headers.get("x-forwarded-for", "").split(",")[0].strip() if request.headers.get("x-forwarded-for") else "")
        or (request.client.host if request.client else "")
    )


# ============================================================================
# Authentication Middleware & Dependency Layer
# ============================================================================

class SessionAuth:
    """
    Dependency that authenticates server-issued anonymous sessions.
    Validates HttpOnly 'saytts_session' cookie or 'X-Device-Token' header.
    Never trusts client-supplied device_id for authorization.
    """

    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        token = request.headers.get("X-Device-Token") or request.headers.get("x-device-token")
        if not token:
            token = request.cookies.get(COOKIE_NAME)
        if not token:
            auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                bearer_val = auth_header[7:].strip()
                if not bearer_val.startswith("sk_"):
                    token = bearer_val

        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required. Please initialize a session via POST /v1/auth/session.",
                )
            return None

        is_valid, device_id, session_record = billing_db.authenticate_session(token)
        if not is_valid or not device_id:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session. Please refresh your session via POST /v1/auth/session.",
                )
            return None

        dev_quota = billing_db.get_device_quota(device_id)
        session = {
            "session_id": session_record.get("session_id", "") if session_record else "",
            "device_id": device_id,
            "is_pro": dev_quota.get("tier") == "pro",
            "tier": dev_quota.get("tier", "free"),
        }
        request.state.session = session
        request.state.device_id = device_id
        return session

get_current_session = SessionAuth(auto_error=True)
get_optional_session = SessionAuth(auto_error=False)


# ============================================================================
# Static SPA Delivery & Health
# ============================================================================

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path(sys.executable).parent / "frontend" / "dist"


@app.api_route("/", methods=["GET", "HEAD"], summary="Kokoro Voice Studio Web Application")
async def root_spa():
    """Serves the production React 19 Studio application UI."""
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(
            path=str(index_file),
            media_type="text/html",
            headers={"Cache-Control": "no-cache, must-revalidate"},
        )
    return JSONResponse({
        "name": "Kokoro Voice Studio",
        "status": "online",
        "version": "2.6.0",
        "docs_url": "/docs",
    })

@app.api_route("/legal", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/legal/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def legal_spa(path: str = ""):
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(path=str(index_file), media_type="text/html")
    return RedirectResponse(url="/")

@app.get("/api", summary="API Overview")
async def api_info():
    return {
        "title": "Kokoro Voice Studio Pro API",
        "version": "2.6.0",
        "status": "operational",
        "endpoints": {
            "health": "GET /health",
            "auth_session": "POST /v1/auth/session",
            "render": "POST /render",
            "jobs": "POST /v1/tts/jobs",
            "quota": "GET /v1/user/quota",
            "developer_keys": "GET/POST /v1/developer/keys",
            "openai_tts": "POST /v1/audio/speech",
        },
    }

@app.get("/health", response_model=HealthResponse, summary="Engine Health & Voice Catalog")
async def health_check():
    """Returns engine readiness state, supported languages, mastering presets, and voice catalog."""
    engine_status = "ready" if engine_manager.is_ready else ("error" if engine_manager.init_error else "loading")

    voices_list: List[VoiceMetadata] = []
    for vid, vdata in VOICE_CATALOG.items():
        voices_list.append(
            VoiceMetadata(
                id=vid,
                name=vdata.get("name", vid),
                gender=vdata.get("gender", "Neutral"),
                lang=vdata.get("lang", "en-us"),
                lang_name=vdata.get("lang_name", "English (US)"),
                flag=vdata.get("flag", "🌐"),
                description=vdata.get("description", ""),
            )
        )

    languages = [
        {"code": "auto", "name": "🌐 Auto-Detect Language", "flag": "🌐"},
        {"code": "en-us", "name": "English (US)", "flag": "🇺🇸"},
        {"code": "en-gb", "name": "English (UK)", "flag": "🇬🇧"},
        {"code": "fr-fr", "name": "French", "flag": "🇫🇷"},
        {"code": "ja", "name": "Japanese", "flag": "🇯🇵"},
        {"code": "ko", "name": "Korean", "flag": "🇰🇷"},
        {"code": "cmn", "name": "Mandarin Chinese", "flag": "🇨🇳"},
        {"code": "es", "name": "Spanish", "flag": "🇪🇸"},
        {"code": "hi", "name": "Hindi", "flag": "🇮🇳"},
        {"code": "it", "name": "Italian", "flag": "🇮🇹"},
        {"code": "pt-br", "name": "Portuguese (BR)", "flag": "🇧🇷"},
    ]

    return HealthResponse(
        status=engine_status,
        version="2.6.0",
        model_loaded=engine_manager.is_ready,
        voices_count=len(VOICE_CATALOG),
        output_directory=str(OUTPUT_DIR.resolve()),
        supported_languages=languages,
        mastering_presets=MASTERING_PRESETS,
        voices=voices_list,
    )


# ============================================================================
# Session Management Endpoints (Zero-Login Architecture)
# ============================================================================

@app.post("/v1/auth/session", summary="Initialize or Refresh Anonymous Authenticated Session")
async def create_or_refresh_session(request: Request, response: Response):
    """
    Issues a server-generated anonymous session.
    Sets HttpOnly, Secure, SameSite=Lax cookie and returns token for API clients.
    Enforces IP velocity limit: max 3 new sessions per IP per 24 hours.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    is_secure = (request.url.scheme == "https") or (request.headers.get("x-forwarded-proto", "").lower() == "https")

    # Check for existing valid session token
    existing_token = request.cookies.get(COOKIE_NAME) or request.headers.get("X-Device-Token") or request.headers.get("x-device-token")
    if existing_token:
        is_valid, dev_id, session_rec = billing_db.authenticate_session(existing_token)
        if is_valid and dev_id:
            quota = billing_db.get_device_quota(dev_id)
            # Re-set cookie with fresh expiration
            response.set_cookie(
                key=COOKIE_NAME,
                value=existing_token,
                max_age=31536000,
                httponly=True,
                secure=is_secure,
                samesite="lax",
                path="/",
            )
            rec_key = billing_db.generate_recovery_key(dev_id)
            return {
                "device_id": dev_id,
                "token": existing_token,
                "session_token": existing_token,
                "recovery_key": rec_key,
                "is_pro": quota.get("tier") == "pro",
                "message": "Existing active session verified.",
            }

    # Layer 2 Anti-Abuse: IP Rate Limit
    if not billing_db.can_create_device_session(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many new sessions created from this IP address today. Please try again later.",
        )

    session_id, new_token, quota_info = billing_db.create_device_session(
        device_id=None,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    new_device_id = quota_info.get("device_id")

    response.set_cookie(
        key=COOKIE_NAME,
        value=new_token,
        max_age=31536000,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )

    rec_key = billing_db.generate_recovery_key(new_device_id)

    return {
        "device_id": new_device_id,
        "token": new_token,
        "session_token": new_token,
        "recovery_key": rec_key,
        "is_pro": False,
        "message": "Anonymous session created successfully.",
    }

@app.post("/v1/auth/recover", summary="Recover Pro Account using 192-Bit Recovery Key")
async def recover_account_endpoint(req: RecoverAccountRequest, request: Request, response: Response):
    """
    Restores zero-login account access using high-entropy recovery key.
    Stores only SHA-256 hash at rest. Issues fresh session on success.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    is_secure = (request.url.scheme == "https") or (request.headers.get("x-forwarded-proto", "").lower() == "https")

    success, message, result_data = billing_db.recover_account(
        req.recovery_key.strip(), client_ip=client_ip, user_agent=user_agent
    )
    if not success or not result_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message or "Invalid or unrecognized recovery key.",
        )

    device_id = result_data["device_id"]
    new_token = result_data["session_token"]

    response.set_cookie(
        key=COOKIE_NAME,
        value=new_token,
        max_age=31536000,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )

    quota = result_data.get("quota") or billing_db.get_device_quota(device_id)
    return {
        "success": True,
        "device_id": device_id,
        "token": new_token,
        "is_pro": quota.get("tier") == "pro",
        "message": "Account recovered successfully.",
    }

@app.post("/v1/auth/reset", summary="Revoke Active Session")
async def reset_session_endpoint(request: Request, response: Response):
    """Revokes active session token and clears cookie."""
    token = request.cookies.get(COOKIE_NAME) or request.headers.get("X-Device-Token") or request.headers.get("x-device-token")
    if token:
        billing_db.revoke_session(token)
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"success": True, "message": "Session revoked."}


# ============================================================================
# Quota, Promo Code & Billing Endpoints (Server-Authorized)
# ============================================================================

@app.get("/v1/user/quota", summary="Get Character Quota & Subscription Status")
@app.get("/user/quota", include_in_schema=False)
@app.get("/quota", include_in_schema=False)
async def get_user_quota(request: Request, session: Dict[str, Any] = Depends(get_current_session)):
    """
    Returns sanitized monthly character usage and tier.
    CRITICAL: Never exposes Stripe IDs, license codes, or internal notes.
    """
    device_id = session["device_id"]
    return billing_db.get_device_quota(device_id)

@app.post("/v1/user/redeem-license", summary="Redeem VIP Promo / License Code")
@app.post("/user/redeem-license", include_in_schema=False)
@app.post("/redeem-license", include_in_schema=False)
@app.post("/v1/license/redeem", include_in_schema=False)
@app.post("/license/redeem", include_in_schema=False)
async def redeem_license(
    req: RedeemLicenseRequest,
    request: Request,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """
    Redeems a Promo / VIP License code for the authenticated session.
    Protected against brute-force attacks with lockout after 5 failed attempts.
    Returns 192-bit recovery key upon successful Pro activation.
    """
    device_id = session["device_id"]
    client_ip = get_client_ip(request)

    success, message, quota = billing_db.redeem_license_key(
        device_id=device_id, code=req.code, client_ip=client_ip
    )
    if not success:
        if "lockout" in message.lower() or "too many" in message.lower():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Generate high-entropy recovery key upon Pro upgrade
    recovery_key = billing_db.generate_recovery_key(device_id)

    return {
        "success": True,
        "message": message,
        "quota": quota,
        "recovery_key": recovery_key,
    }

@app.post("/v1/billing/create-checkout-session", summary="Generate Stripe Checkout Link")
@app.post("/billing/create-checkout-session", include_in_schema=False)
async def create_checkout_session(
    req: CreateCheckoutRequest,
    request: Request,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """
    Creates Stripe Checkout Session strictly bound to authenticated session device ID.
    Ignores any client-supplied device_id in request body.
    """
    target_device = session["device_id"]

    UPGRADES_PAUSED = False
    if UPGRADES_PAUSED:
        return {
            "checkout_url": None,
            "message": "Pro upgrades are temporarily paused. Please check back soon!",
        }

    stripe_key = STRIPE_SECRET_KEY
    price_id = STRIPE_PRICE_ID

    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    public_base_url = f"{forwarded_proto}://{forwarded_host}".rstrip("/") if forwarded_host else str(request.base_url).rstrip("/")

    return_url = req.return_url or f"{public_base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{public_base_url}/billing/cancel"

    if stripe_key and price_id:
        try:
            import stripe
            stripe.api_key = stripe_key

            try:
                price_obj = stripe.Price.retrieve(price_id)
                mode = "subscription" if price_obj.type == "recurring" else "payment"
            except Exception:
                mode = "subscription"

            checkout_kwargs = {
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": mode,
                "success_url": return_url,
                "cancel_url": cancel_url,
                "client_reference_id": target_device,
                "metadata": {"device_id": target_device},
            }

            try:
                stripe_sess = stripe.checkout.Session.create(**checkout_kwargs, managed_payments={"enabled": False})
            except Exception:
                stripe_sess = stripe.checkout.Session.create(**checkout_kwargs)

            logger.info(f"Generated Stripe Checkout session {stripe_sess.id} for authenticated device '{target_device}'")
            return {"checkout_url": stripe_sess.url}
        except Exception as e:
            logger.error(f"Stripe session error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"checkout_url": None, "message": "Stripe billing is not configured yet."}

@app.get("/billing/success", include_in_schema=False)
async def billing_success(request: Request, session_id: Optional[str] = None):
    """Handles return redirect after successful Stripe checkout."""
    if session_id and STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            checkout_sess = stripe.checkout.Session.retrieve(session_id)
            target_device = checkout_sess.client_reference_id or (checkout_sess.metadata and checkout_sess.metadata.get("device_id"))
            if target_device:
                cust = checkout_sess.customer or ""
                sub = checkout_sess.subscription or ""
                expires_at = None
                if sub and STRIPE_SECRET_KEY:
                    try:
                        sub_obj = stripe.Subscription.retrieve(sub)
                        if hasattr(sub_obj, "current_period_end") and sub_obj.current_period_end:
                            expires_at = datetime.datetime.fromtimestamp(
                                sub_obj.current_period_end, datetime.timezone.utc
                            ).isoformat()
                    except Exception as sub_err:
                        logger.warning(f"Failed to fetch current_period_end from Stripe sub {sub}: {sub_err}")

                billing_db.grant_pro(
                    target_device,
                    tier="pro",
                    note=f"Stripe Paid: {session_id}",
                    stripe_customer_id=cust,
                    stripe_subscription_id=sub,
                    subscription_expires_at=expires_at,
                )
                logger.info(f"Upgraded device '{target_device}' to PRO via Stripe Checkout session {session_id}")
        except Exception as e:
            logger.warning(f"Error retrieving Stripe session {session_id}: {e}")

    return RedirectResponse(url="/?payment=success")

@app.get("/billing/cancel", include_in_schema=False)
async def billing_cancel():
    return RedirectResponse(url="/?payment=cancelled")

@app.post("/v1/billing/toggle-auto-renew", summary="Toggle Subscription Auto-Renewal")
async def toggle_auto_renew(
    req: ToggleAutoRenewRequest,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """
    Turns auto-renewal on or off strictly for the authenticated session device.
    Ignores any client-supplied device ID in request body.
    """
    target_device = session["device_id"]
    dev = billing_db.get_device_raw(target_device)
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")

    sub_id = dev.get("stripe_subscription_id")
    if sub_id and STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            stripe.Subscription.modify(sub_id, cancel_at_period_end=req.cancel_at_period_end)
            logger.info(f"Stripe sub {sub_id} cancel_at_period_end updated to {req.cancel_at_period_end}")
        except Exception as e:
            logger.error(f"Error updating Stripe renewal: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update subscription: {str(e)}")

    updated_quota = billing_db.set_auto_renew(target_device, auto_renew=not req.cancel_at_period_end)
    return {
        "success": True,
        "auto_renew": not req.cancel_at_period_end,
        "message": f"Auto-renewal {'enabled' if not req.cancel_at_period_end else 'disabled'}.",
        "quota": updated_quota,
    }

@app.post("/v1/billing/cancel-subscription", summary="Cancel Pro Subscription")
async def cancel_subscription(
    req: CancelSubscriptionRequest,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """
    Cancels Pro subscription renewal strictly for the authenticated session device.
    Pro features persist until the end of the paid 30-day period.
    """
    target_device = session["device_id"]
    dev = billing_db.get_device_raw(target_device)
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")

    sub_id = dev.get("stripe_subscription_id")
    if sub_id and STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            stripe.Subscription.modify(sub_id, cancel_at_period_end=True)
            logger.info(f"Scheduled Stripe subscription {sub_id} cancellation at period end")
        except Exception as e:
            logger.error(f"Error modifying Stripe sub {sub_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to cancel subscription with provider: {str(e)}")

    updated_quota = billing_db.cancel_subscription_immediate(
        target_device, note="Subscription cancelled - retains Pro access until 30-day period ends"
    )

    return {
        "success": True,
        "immediate": False,
        "message": "Subscription cancelled. Auto-renewal turned off. Pro access retained until period ends.",
        "quota": updated_quota,
    }

@app.post("/v1/billing/webhook", summary="Stripe Webhook Receiver")
async def stripe_webhook(request: Request):
    """Handles signed Stripe webhooks with cryptographic signature verification."""
    webhook_secret = STRIPE_WEBHOOK_SECRET
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not webhook_secret or not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook signature")

    try:
        import stripe
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        logger.warning(f"Stripe webhook signature error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid signature: {e}")

    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        target_dev = event_data.get("client_reference_id") or event_data.get("metadata", {}).get("device_id")
        cust_id = event_data.get("customer", "")
        sub_id = event_data.get("subscription", "")
        if target_dev:
            billing_db.grant_pro(
                target_dev,
                tier="pro",
                note=f"Stripe Checkout webhook ({event.get('id')})",
                stripe_customer_id=cust_id,
                stripe_subscription_id=sub_id,
            )
            logger.info(f"Webhook checkout.session.completed: Upgraded '{target_dev}' to Pro")

    elif event_type == "customer.subscription.deleted":
        sub_id = event_data.get("id")
        if sub_id:
            billing_db.cancel_subscription_by_sub_id(sub_id, note="Stripe subscription deleted")
            logger.info(f"Webhook customer.subscription.deleted: Revoked Pro for sub {sub_id}")

    return {"status": "success"}


# ============================================================================
# Admin Endpoints (Hidden from OpenAPI Schema)
# ============================================================================

@app.post("/admin/grant-pro", summary="Admin API: Directly Grant Pro", include_in_schema=False)
async def admin_grant_pro(req: GrantProRequest, request: Request):
    """Admin endpoint protected by X-Admin-Secret header."""
    admin_secret = ADMIN_SECRET_KEY
    client_secret = request.headers.get("X-Admin-Secret") or request.headers.get("x-admin-secret")

    if not admin_secret or client_secret != admin_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Admin Secret Key")

    res = billing_db.grant_pro(req.device_id, tier=req.tier, note=req.note)
    return {"success": True, "device_id": req.device_id, "quota": res}

@app.post("/admin/create-license-key", summary="Admin API: Generate License Code", include_in_schema=False)
async def admin_create_license_key(req: CreateLicenseKeyRequest, request: Request):
    """Admin endpoint protected by X-Admin-Secret header. Generates 128-bit license code."""
    admin_secret = ADMIN_SECRET_KEY
    client_secret = request.headers.get("X-Admin-Secret") or request.headers.get("x-admin-secret")

    if not admin_secret or client_secret != admin_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Admin Secret Key")

    res = billing_db.create_license_key(
        code=req.code,
        tier=req.tier,
        max_uses=req.max_uses,
        note=req.note,
    )
    return {"success": True, "license_key": res}


# ============================================================================
# Synchronous TTS Rendering Endpoint (Worker 1)
# ============================================================================

@app.post("/render", response_model=RenderResponse, summary="Synthesize Text to Mastered Audio")
async def render_audio(
    req: RenderRequest,
    request: Request,
    response: Response,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """
    Synthesize input text into speech with selected voice, speed, language, and EQ preset.
    Limits:
    - Free tier: max 3,000 characters per request, 1 active concurrent render per session.
    - Pro tier: max 6,000 characters for synchronous rendering (scripts up to 25k use /v1/tts/jobs).
    Dispatches to Worker 1 interactive queue (bounded at 20 tasks).
    Supports cooperative client disconnect cancellation.
    """
    device_id = session["device_id"]
    is_pro = session.get("is_pro", False)
    text_len = len(req.text or "")

    # Layer 1 Input Limits
    if not is_pro and text_len > MAX_FREE_CHARS_SYNC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Free tier limit is {MAX_FREE_CHARS_SYNC} characters per render. Upgrade to Pro for longer scripts.",
        )
    if is_pro and text_len > MAX_PRO_CHARS_SYNC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Synchronous limit is {MAX_PRO_CHARS_SYNC} characters. Use /v1/tts/jobs for scripts up to {MAX_PRO_CHARS_ASYNC} characters.",
        )

    # Layer 4 Concurrency Protection for Free Tier (1 active render per session)
    if not is_pro:
        if device_id in active_free_renders:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Free tier allows 1 active render at a time. Please wait for your current render to complete.",
            )
        active_free_renders.add(device_id)

    try:
        client_ip = get_client_ip(request)
        allowed, quota_info, quota_msg = billing_db.check_and_consume_quota(
            device_id=device_id,
            char_count=text_len,
            voice_id=req.voice_id,
            client_ip=client_ip,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "quota_exceeded",
                    "message": quota_msg,
                    "quota": quota_info,
                },
            )

        response.headers["X-User-Tier"] = quota_info.get("tier", "free")
        response.headers["X-Quota-Usage"] = str(quota_info.get("monthly_usage", 0))
        response.headers["X-Quota-Remaining"] = str(quota_info.get("remaining_chars", "unlimited"))

        if req.voice_id not in VOICE_CATALOG:
            req.voice_id = "af_bella"
        if req.eq_preset not in MASTERING_PRESETS:
            req.eq_preset = "Clean Studio (Default)"

        render_payload = req.model_dump()
        render_payload["device_id"] = device_id

        # Timeout hierarchy: FastAPI request timeout is 240s
        result = await engine_manager.render_sync_async(render_payload, timeout_sec=240.0)

        filename = result["filename"]
        base_name = result["base_name"]
        file_ext = result.get("file_ext", "wav")
        file_size = result.get("file_size_bytes", 0)

        # Record authenticated ownership in audio_artifacts with 2-hour TTL
        billing_db.record_audio_artifact(
            file_id=base_name,
            device_id=device_id,
            filename=filename,
            format=file_ext,
            file_size=file_size,
            ttl_seconds=DEFAULT_ARTIFACT_TTL,
        )

        base_url = str(request.base_url).rstrip("/")
        audio_url = f"{base_url}/audio/{filename}"

        return RenderResponse(
            success=True,
            audio_path=result["audio_path"],
            audio_url=audio_url,
            filename=filename,
            duration=result["duration"],
            sample_rate=result["sample_rate"],
            file_size_bytes=file_size,
            voice_id=result["voice_id"],
            voice_name=result["voice_name"],
            lang_resolved=result["lang_resolved"],
            eq_preset=result["eq_preset"],
            audio_base64=result.get("audio_base64"),
            srt_content=result.get("srt_content"),
            srt_filename=result.get("srt_filename"),
        )
    finally:
        if not is_pro:
            active_free_renders.discard(device_id)


# ============================================================================
# Asynchronous TTS Job API (Worker 2)
# ============================================================================

@app.post("/v1/tts/jobs", status_code=status.HTTP_202_ACCEPTED, summary="Submit Long-Form Pro Batch TTS Job")
async def create_tts_job(
    req: CreateTTSJobRequest,
    request: Request,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """
    Submits a long-form TTS job (up to 25,000 characters) to Worker 2.
    Requires an active Pro subscription. Returns HTTP 202 with job_id.
    """
    device_id = session["device_id"]
    is_pro = session.get("is_pro", False)
    text_len = len(req.text or "")

    if not is_pro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Asynchronous batch jobs require an active Pro subscription.",
        )

    if text_len > MAX_PRO_CHARS_ASYNC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum script length for async jobs is {MAX_PRO_CHARS_ASYNC} characters.",
        )

    # Consume quota
    client_ip = get_client_ip(request)
    allowed, quota_info, quota_msg = billing_db.check_and_consume_quota(
        device_id=device_id, char_count=text_len, voice_id=req.voice_id, client_ip=client_ip
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": "quota_exceeded", "message": quota_msg, "quota": quota_info},
        )

    job_id = f"job_{secrets.token_urlsafe(16)}"
    billing_db.create_tts_job(job_id=job_id, device_id=device_id, char_count=text_len)

    payload = req.model_dump()
    payload["job_id"] = job_id
    payload["device_id"] = device_id
    payload["is_job"] = True

    engine_manager.submit_batch_job(payload)

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "char_count": text_len,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

@app.get("/v1/tts/jobs/{job_id}", summary="Get Status of Asynchronous TTS Job")
async def get_tts_job(job_id: str, session: Dict[str, Any] = Depends(get_current_session)):
    """Returns status and audio URL for a job. Enforces session ownership."""
    device_id = session["device_id"]
    job = billing_db.get_tts_job(job_id)
    if not job or job["device_id"] != device_id:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job.get("progress", 0.0),
        "filename": job.get("filename"),
        "audio_url": job.get("audio_url"),
        "char_count": job.get("char_count"),
        "created_at": job["created_at"],
        "updated_at": job.get("updated_at"),
        "error_message": job.get("error_message"),
    }

@app.get("/v1/tts/jobs/{job_id}/audio", summary="Download Finished Audio for TTS Job")
async def get_tts_job_audio(job_id: str, session: Dict[str, Any] = Depends(get_current_session)):
    """Delivers completed audio file for a job. Enforces session ownership."""
    device_id = session["device_id"]
    job = billing_db.get_tts_job(job_id)
    if not job or job["device_id"] != device_id:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "COMPLETED" or not job.get("filename"):
        raise HTTPException(status_code=400, detail=f"Job is not completed (status={job['status']})")

    filename = job["filename"]
    safe_fn = Path(filename).name
    file_path = OUTPUT_DIR / safe_fn

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Job audio file not found on disk")

    media_type = "audio/mpeg" if safe_fn.endswith(".mp3") else "audio/wav"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={"Cache-Control": "private, no-cache", "Content-Disposition": f'inline; filename="{safe_fn}"'},
    )

@app.post("/v1/tts/jobs/{job_id}/cancel", summary="Cancel Running or Queued TTS Job")
async def cancel_tts_job(job_id: str, session: Dict[str, Any] = Depends(get_current_session)):
    """Cancels an active or queued job. Enforces session ownership."""
    device_id = session["device_id"]
    job = billing_db.get_tts_job(job_id)
    if not job or job["device_id"] != device_id:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
        return {"success": False, "message": f"Job already in terminal state ({job['status']})"}

    engine_manager.cancellation_dict[job_id] = True
    billing_db.update_tts_job(job_id, status="CANCELLED", error_message="Cancelled by user")
    return {"success": True, "message": "Job cancelled successfully."}


# ============================================================================
# Authenticated & Hardened Audio Delivery Endpoint
# ============================================================================

@app.api_route("/audio/{filename}", methods=["GET", "HEAD"], summary="Download Rendered Audio or SRT Subtitles")
async def get_audio_file(
    filename: str,
    request: Request,
    session: Optional[Dict[str, Any]] = Depends(get_optional_session),
):
    """
    Delivers audio or subtitle files with authenticated ownership and 2-hour TTL verification.
    Rejects path traversal attempts. Requires caller to own the artifact.
    """
    # 1. Path Traversal Defense
    safe_filename = Path(filename).name
    if ".." in filename or "/" in filename or "\\" in filename or safe_filename != filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename format")

    device_id = session["device_id"] if session else None
    if not device_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required to access audio artifact")
    status_code, artifact = billing_db.get_audio_artifact(safe_filename, device_id=device_id)

    if status_code == "NOT_FOUND":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found or expired")
    if status_code == "EXPIRED":
        file_path = OUTPUT_DIR / safe_filename
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file has expired (2-hour TTL)")
    if status_code == "UNAUTHORIZED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to audio artifact")

    file_path = OUTPUT_DIR / safe_filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found on disk")

    if safe_filename.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif safe_filename.endswith(".srt"):
        media_type = "text/plain; charset=utf-8"
    else:
        media_type = "audio/wav"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        content_disposition_type="inline",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "private, no-cache",
            "Content-Disposition": f'inline; filename="{safe_filename}"',
        },
    )

@app.get("/voices", summary="List All Available Voices")
async def list_voices():
    return {"count": len(VOICE_CATALOG), "voices": VOICE_CATALOG}

@app.get("/presets", summary="List Mastering EQ Presets")
async def list_presets():
    return {"count": len(MASTERING_PRESETS), "presets": MASTERING_PRESETS}


# ============================================================================
# OpenAI-Compatible Speech API & Developer Platform Endpoints
# ============================================================================

def extract_api_key(request: Request) -> Optional[str]:
    """Extracts secret key from Authorization Bearer or X-API-Key header."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    api_key_header = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if api_key_header:
        return api_key_header.strip()
    return None

FREE_TIER_API_DELAY_SECONDS = 5.0

class AntiDDoSRateLimiter:
    """In-memory rate limiter enforcing delay between consecutive API calls for free tier."""

    def __init__(self, free_delay_seconds: float = FREE_TIER_API_DELAY_SECONDS):
        self.free_delay = free_delay_seconds
        self._last_call_timestamps: Dict[str, float] = {}
        self._active_connections: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def check_and_acquire(self, identifier: str, is_pro: bool = False) -> float:
        async with self._lock:
            active = self._active_connections.get(identifier, 0)
            if not is_pro and active >= 1:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "message": "Free tier API is restricted to 1 concurrent request. Upgrade to Pro for unlimited concurrency.",
                            "type": "concurrency_limit_exceeded",
                            "code": "free_tier_concurrency_limit",
                        }
                    },
                )
            self._active_connections[identifier] = active + 1

            if is_pro:
                return 0.0

            last_time = self._last_call_timestamps.get(identifier, 0.0)
            elapsed = time.time() - last_time
            if elapsed < self.free_delay:
                return self.free_delay - elapsed
            return 0.0

    async def release(self, identifier: str, is_pro: bool = False):
        async with self._lock:
            curr = self._active_connections.get(identifier, 1)
            self._active_connections[identifier] = max(0, curr - 1)
            self._last_call_timestamps[identifier] = time.time()

api_rate_limiter = AntiDDoSRateLimiter(free_delay_seconds=FREE_TIER_API_DELAY_SECONDS)

@app.get("/v1/models", summary="OpenAI-Compatible Model List")
async def openai_list_models():
    return {
        "object": "list",
        "data": [
            {"id": "kokoro", "object": "model", "created": 1700000000, "owned_by": "kokoro-studio"},
            {"id": "kokoro-82m", "object": "model", "created": 1700000000, "owned_by": "kokoro-studio"},
            {"id": "tts-1", "object": "model", "created": 1700000000, "owned_by": "kokoro-studio"},
            {"id": "tts-1-hd", "object": "model", "created": 1700000000, "owned_by": "kokoro-studio"},
        ],
    }

@app.post("/v1/audio/speech", summary="OpenAI-Compatible Text-to-Speech Endpoint")
async def openai_audio_speech(req: OpenAISpeechRequest, request: Request):
    """
    Drop-in OpenAI-compatible speech synthesis endpoint.
    Protected by SHA-256 hashed API key authentication at rest.
    """
    api_key = extract_api_key(request)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "Missing API key. Pass secret key in Authorization header: 'Bearer sk_live_kokoro_...'",
                    "type": "invalid_request_error",
                    "code": "missing_api_key",
                }
            },
        )

    text_len = len(req.input or "")
    if text_len == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"message": "'input' text must not be empty.", "code": "empty_input"}},
        )

    is_valid, key_data, auth_err = billing_db.authenticate_api_key(api_key)
    if not is_valid or not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"message": auth_err or "Invalid or revoked API key.", "code": "invalid_api_key"}},
        )

    key_id = key_data["key_id"]
    tier = key_data.get("tier", "free")
    is_pro = (tier == "pro")

    wait_seconds = await api_rate_limiter.check_and_acquire(key_id, is_pro=is_pro)

    try:
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        client_ip = get_client_ip(request)
        allowed, quota_info, quota_msg = billing_db.check_and_consume_api_key_quota(
            api_key=api_key,
            char_count=text_len,
            client_ip=client_ip,
            voice_id=req.voice,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": {"message": quota_msg, "type": "insufficient_quota", "code": "quota_exceeded"}},
            )

        target_voice = req.voice
        openai_voice_map = {
            "alloy": "am_adam",
            "echo": "am_michael",
            "fable": "bm_george",
            "onyx": "am_fenrir",
            "nova": "af_bella",
            "shimmer": "af_sarah",
        }
        if target_voice in openai_voice_map:
            target_voice = openai_voice_map[target_voice]
        elif target_voice not in VOICE_CATALOG:
            target_voice = "af_bella"

        fmt = req.response_format.lower().strip()
        output_format = "mp3" if fmt in ("mp3", "aac", "opus", "flac") else "wav"

        render_payload = {
            "text": req.input,
            "voice_id": target_voice,
            "speed": float(req.speed),
            "eq_preset": req.eq_preset or "Clean Studio (Default)",
            "lang": req.lang or "auto",
            "output_format": output_format,
            "pause_punctuation_ms": req.pause_punctuation_ms or 150,
            "pause_paragraph_ms": req.pause_paragraph_ms or 400,
            "device_id": key_data["device_id"],
        }

        result = await engine_manager.render_sync_async(render_payload, timeout_sec=240.0)

        file_path = Path(result["audio_path"])
        if not file_path.exists():
            raise HTTPException(status_code=500, detail="Generated audio file not found")

        # Record artifact
        billing_db.record_audio_artifact(
            file_id=result["base_name"],
            device_id=key_data["device_id"],
            filename=result["filename"],
            format=output_format,
            file_size=result.get("file_size_bytes", 0),
            ttl_seconds=DEFAULT_ARTIFACT_TTL,
        )

        media_type = "audio/mpeg" if output_format == "mp3" else "audio/wav"
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            headers={
                "Content-Type": media_type,
                "OpenAI-Model": req.model,
                "X-Kokoro-Voice": target_voice,
                "X-Audio-Duration": str(result["duration"]),
                "X-Characters-Consumed": str(text_len),
                "X-Quota-Remaining": str(quota_info.get("remaining_chars", "unlimited")),
                "X-RateLimit-Delay-Seconds": "0" if is_pro else str(int(FREE_TIER_API_DELAY_SECONDS)),
                "X-RateLimit-Tier": tier,
            },
        )
    finally:
        await api_rate_limiter.release(key_id, is_pro=is_pro)

@app.get("/v1/audio/voices", summary="OpenAI-Compatible Voice Catalog")
async def openai_list_voices():
    return {"voices": [{"id": k, "name": v.get("name", k), "language": v.get("lang", "en-us")} for k, v in VOICE_CATALOG.items()]}


# ============================================================================
# Developer API Key Management (Server Session Bound)
# ============================================================================

@app.post("/v1/developer/keys", summary="Generate New API Key for Authenticated Session")
async def create_developer_key(
    req: CreateApiKeyRequest,
    session: Dict[str, Any] = Depends(get_current_session),
):
    """
    Generates a secure API key bound to the authenticated session device.
    CRITICAL: The full plaintext secret is returned ONCE upon creation.
    Stored strictly as SHA-256 hash at rest.
    """
    device_id = session["device_id"]
    try:
        return billing_db.create_api_key(device_id=device_id, name=req.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"message": str(e), "code": "api_key_limit_reached"}},
        )

@app.get("/v1/developer/keys", summary="List Developer API Keys for Authenticated Session")
async def list_developer_keys(session: Dict[str, Any] = Depends(get_current_session)):
    """
    Lists active API keys for the authenticated session.
    CRITICAL FIX: Returns masked keys only (e.g. sk_live_...1234).
    Never contains plaintext keys or raw hashes.
    """
    device_id = session["device_id"]
    keys = billing_db.list_api_keys(device_id=device_id)
    quota = billing_db.get_device_quota(device_id=device_id)
    is_pro = quota.get("tier") == "pro"
    max_keys = 50 if is_pro else 1

    return {
        "device_id": device_id,
        "quota": quota,
        "keys": keys,
        "max_keys": max_keys,
        "can_create_key": is_pro or len(keys) < 1,
    }

@app.delete("/v1/developer/keys/{key_id}", summary="Revoke Developer API Key")
async def revoke_developer_key(key_id: str, session: Dict[str, Any] = Depends(get_current_session)):
    """Revokes an API key. Enforces session ownership."""
    device_id = session["device_id"]
    success = billing_db.revoke_api_key(device_id=device_id, key_id=key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found or already revoked")
    return {"success": True, "message": "API key revoked successfully"}


# ============================================================================
# Static Frontend SPA Mounting (Serves React 19 UI Bundle)
# ============================================================================

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")
    flags_dir = FRONTEND_DIST / "flags"
    if flags_dir.exists():
        app.mount("/flags", StaticFiles(directory=str(flags_dir)), name="static-flags")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static-root")


# ============================================================================
# Main Entry Point with Windows Freeze Support
# ============================================================================

if __name__ == "__main__":
    mp.freeze_support()

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("\n" + "=" * 62)
    print("   [*] Kokoro Voice Studio Pro - Hardened Backend Server")
    print(f"   [*] Server URL: http://127.0.0.1:{port} (LAN: http://0.0.0.0:{port})")
    print(f"   [*] Interactive Swagger Docs: http://127.0.0.1:{port}/docs")
    print("   [*] Dual Worker Architecture: ENABLED (Sync: 20, Batch: 50)")
    print("   [*] Anonymous Session Authorization: ENABLED")
    print("   [*] Masked Key & Hashed Rest Storage: ENABLED")
    print("=" * 62 + "\n")

    uvicorn.run(app, host=host, port=port, log_level="info")
