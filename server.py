"""
Kokoro Voice Studio Pro — Standalone FastAPI Backend Server
============================================================
High-performance, async-isolated REST backend exposing Kokoro-82M TTS,
Multilingual G2P phonemization (9+ languages), acoustic EQ mastering presets,
and audio rendering over standard HTTP APIs.

Features:
  - Asynchronous background model loading in an isolated process.
  - Non-blocking GET /health endpoint reporting status & 60-voice catalog.
  - POST /render endpoint with timeout protection, G2P routing & master EQ.
  - GET /audio/{filename} static audio file streaming with CORS support.
  - Windows multiprocessing safe with freeze_support().
"""

from __future__ import annotations

import asyncio
import base64
import logging
import multiprocessing as mp
import os
import re
import json
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Guard against None stdout/stderr in windowless PyInstaller execution
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="ignore")
    except Exception:
        pass

if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="ignore")
    except Exception:
        pass

# Configure UTF-8 encoding for Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("kokoro.server")

# Base directory paths (supports both standard execution and PyInstaller sys._MEIPASS bundle)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
    OUTPUT_DIR = Path(os.getcwd()) / "output"
else:
    BASE_DIR = Path(__file__).resolve().parent
    OUTPUT_DIR = BASE_DIR / "output"

ASSETS_DIR = BASE_DIR / "assets" / "kokoro"
MODEL_PATH = str(ASSETS_DIR / "kokoro-v1.0.onnx")
VOICES_PATH = str(ASSETS_DIR / "voices-v1.0.bin")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Import voice catalog and presets metadata (pure data structures, no heavy loading)
from core.kokoro_engine import MASTERING_PRESETS, VOICE_CATALOG
from core.multilingual_g2p import CANONICAL_LANG_MAP


# ============================================================================
# Pydantic Request / Response Schemas
# ============================================================================

class RenderRequest(BaseModel):
    text: str = Field(..., description="Input text to synthesize", min_length=1)
    voice_id: str = Field(default="af_bella", description="Voice ID from catalog (e.g. af_bella, jf_alpha, ff_camille)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier (0.5 to 2.0)")
    eq_preset: str = Field(default="Clean Studio (Default)", description="Acoustic mastering EQ preset name")
    lang: str = Field(default="auto", description="Language code (e.g. 'auto', 'en-us', 'ja', 'fr-fr', 'ko', 'cmn', 'es', 'hi')")
    output_format: str = Field(default="wav", description="Audio output format ('wav' or 'mp3')")
    pause_punctuation_ms: int = Field(default=150, ge=0, le=1000, description="Pause duration after commas/colons in milliseconds")
    pause_paragraph_ms: int = Field(default=400, ge=0, le=2000, description="Pause duration between paragraphs/periods in milliseconds")


class RenderResponse(BaseModel):
    success: bool
    audio_path: str = Field(..., description="Absolute local path to generated audio file")
    audio_url: str = Field(..., description="Relative HTTP endpoint URL to stream/download audio")
    filename: str = Field(..., description="Audio file name")
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(default=24000, description="Audio sample rate (Hz)")
    file_size_bytes: int = Field(..., description="Audio file size in bytes")
    voice_id: str
    voice_name: str
    lang_resolved: str
    eq_preset: str
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded in-memory audio data for zero-interception streaming")
    srt_content: Optional[str] = Field(default=None, description="Synchronized CapCut/Premiere SubRip (.srt) subtitle content")
    srt_filename: Optional[str] = Field(default=None, description="Subtitle file name (.srt)")


class VoiceMetadata(BaseModel):
    id: str
    name: str
    gender: str
    lang: str
    lang_name: str
    flag: str
    description: str


class HealthResponse(BaseModel):
    status: str = Field(..., description="Engine status: 'ready', 'loading', or 'error'")
    version: str = "2.5.0"
    model_loaded: bool
    voices_count: int
    output_directory: str
    supported_languages: List[Dict[str, str]]
    mastering_presets: List[str]
    voices: List[VoiceMetadata]


# ============================================================================
# Smart Punchy SRT Subtitle Builder (CapCut / Premiere / Reels / TikTok)
# ============================================================================

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


def is_cjk_text(text: str) -> bool:
    """Detect whether string contains CJK characters (Japanese Kana/Kanji, Chinese Hanzi, Korean Hangul)."""
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\uac00-\ud7af]", text))


def split_cjk_clause(clause: str, max_chars: int = 18) -> List[str]:
    """
    Split a CJK clause without spaces into 12-18 character readable subtitle chunks.
    Preserves whole Latin words (e.g. 'Kokoro Voice Studio') while partitioning on particles or commas.
    """
    if len(clause) <= max_chars:
        return [clause]

    # If clause contains spaces (mixed Latin/CJK), split along space boundaries first
    if " " in clause:
        tokens = clause.split(" ")
        chunks = []
        current = ""
        for t in tokens:
            if not current:
                current = t
            elif len(current) + len(t) + 1 <= max_chars + 4:
                current += " " + t
            else:
                chunks.append(current)
                current = t
        if current:
            chunks.append(current)
        return [c for c in chunks if c.strip()]

    # Pure CJK character stream splitting
    chunks = []
    current = ""
    for char in clause:
        current += char
        if len(current) >= max_chars - 3 and char in "はがをにでもへとたらば、，":
            chunks.append(current)
            current = ""
        elif len(current) >= max_chars:
            chunks.append(current)
            current = ""

    if current:
        if chunks and len(current) <= 3:
            chunks[-1] += current
        else:
            chunks.append(current)

    return [c for c in chunks if c.strip()]


def split_clause_into_balanced_chunks(clause: str, max_words: int = 8, max_chars: int = 40) -> List[str]:
    """Split a single Latin/spaced clause into balanced chunks of 5-8 words (<= 40 chars)."""
    words = clause.split()
    if len(words) <= max_words and len(clause) <= max_chars:
        return [clause]

    import math
    n_chunks = max(math.ceil(len(words) / 7), math.ceil(len(clause) / max_chars))
    words_per_chunk = math.ceil(len(words) / max(n_chunks, 1))

    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk_str = " ".join(words[i:i + words_per_chunk])
        if chunk_str:
            chunks.append(chunk_str)
    return chunks


def split_text_into_punchy_srt_chunks(
    text: str,
    max_words: int = 8,
    max_chars_latin: int = 40,
    max_chars_cjk: int = 18,
) -> List[str]:
    """
    Split narrative text into short, punchy subtitle chunks based on sentence and clause boundaries.
    Fully supports Latin (English/French/Spanish/Hindi) and CJK (Japanese/Chinese/Korean).
    """
    clean = re.sub(r"\[pause\s+[0-9.]+s?\]", "", text, flags=re.IGNORECASE).strip()
    if not clean:
        return []

    # 1. Split on major sentence delimiters (. ! ? 。 ！？ \n ; :)
    major_clauses = [c.strip() for c in re.split(r"(?<=[.!?。！？\n;:])\s*", clean) if c.strip()]

    final_chunks = []
    for clause in major_clauses:
        # 2. Split on comma / secondary clause delimiters (, 、 ， — –)
        sub_parts = [p.strip() for p in re.split(r"(?<=[,、，—–])\s*", clause) if p.strip()]
        for part in sub_parts:
            if is_cjk_text(part):
                # CJK mode: 12-18 characters per subtitle block
                cjk_parts = split_cjk_clause(part, max_chars=max_chars_cjk)
                final_chunks.extend(cjk_parts)
            else:
                # Latin mode: 5-8 words per subtitle block
                latin_parts = split_clause_into_balanced_chunks(part, max_words=max_words, max_chars=max_chars_latin)
                final_chunks.extend(latin_parts)

    return [c for c in final_chunks if c.strip()]


def calculate_chunk_acoustic_weight(chunk: str) -> float:
    """
    Calculate duration weight including acoustic pauses for punctuation:
    - Major sentence endings (。 ！ ？ ! ? . \n): +4.5 char units (breath pause ~350-450ms)
    - Comma/clause delimiters (、 ， , ; — –): +2.2 char units (clause pause ~150-200ms)
    """
    base_w = float(max(len(chunk), 4))
    if re.search(r"[。！？!?.\n]$", chunk.strip()):
        base_w += 4.5
    elif re.search(r"[、，,;—–]$", chunk.strip()):
        base_w += 2.2
    return base_w


def build_srt_subtitles(
    text: str,
    total_duration: float,
    max_words: int = 8,
    max_chars: int = 40,
    max_chunk_dur: float = 3.5,
) -> str:
    """
    Generate short, punchy, CapCut-compliant SRT subtitles.
    - Latin: 5-8 words (or ~35-40 characters) per subtitle block.
    - CJK (Japanese/Chinese): 12-18 characters per subtitle block.
    - Acoustic pause weighting for natural sentence and clause pauses (。 ！ ？ 、).
    - 100ms anti-flicker overlap padding between cards for smooth CapCut playback.
    """
    from core.multilingual_g2p import MultilingualG2P
    g2p = MultilingualG2P()
    raw_lines = [l.strip() for l in text.strip().split("\n") if l.strip()]

    # Check for multi-speaker dialogue lines
    dialogue_entries = []
    has_tags = False
    for line in raw_lines:
        spk, l_lang, clean_txt = g2p.parse_dialogue_line(line)
        if spk is not None and clean_txt:
            has_tags = True
            dialogue_entries.append(clean_txt)
        elif line:
            dialogue_entries.append(line)

    source_lines = dialogue_entries if has_tags else [text]

    all_chunks = []
    for s_line in source_lines:
        line_chunks = split_text_into_punchy_srt_chunks(
            s_line,
            max_words=max_words,
            max_chars_latin=max_chars,
            max_chars_cjk=18,
        )
        all_chunks.extend(line_chunks)

    if not all_chunks:
        return ""

    weights = [calculate_chunk_acoustic_weight(c) for c in all_chunks]
    total_weight = sum(weights)

    srt_lines = []
    current_time = 0.0

    for idx, (chunk, w) in enumerate(zip(all_chunks, weights), start=1):
        raw_dur = (w / total_weight) * total_duration
        dur = min(max(raw_dur, 0.6), max_chunk_dur)

        start_ts = format_srt_timestamp(current_time)

        # 100ms anti-flicker overlap padding prevents subtitle flicker between cuts in CapCut
        overlap_padding = 0.100 if idx < len(all_chunks) else 0.0
        end_time = min(current_time + dur + overlap_padding, total_duration)
        end_ts = format_srt_timestamp(end_time)

        srt_lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{chunk}\n")
        current_time = min(current_time + dur, total_duration)

    return "\n".join(srt_lines).strip() + "\n"


# ============================================================================
# Background Worker Process (Runs in separate OS Process)
# ============================================================================

def _engine_worker_loop(
    task_queue: mp.Queue,
    response_queue: mp.Queue,
    model_dir: str,
    output_dir: str,
) -> None:
    """
    Worker process entry point.
    Loads ONNX weights & G2P models without blocking the main FastAPI process,
    then continuously listens for rendering tasks over IPC queues.
    """
    # Configure UTF-8 encoding for Windows child processes
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        # Import and initialize heavy engine inside the worker process
        from core.kokoro_engine import KokoroStudioEngine
        engine = KokoroStudioEngine(model_dir=Path(model_dir))
        engine.load_model()

        # Signal ready state to main process
        response_queue.put({"type": "INIT_DONE", "success": True})
    except Exception as e:
        err_msg = f"{type(e).__name__}: {str(e) or repr(e)}"
        response_queue.put({"type": "INIT_DONE", "success": False, "error": err_msg})
        return

    # Main IPC task loop
    while True:
        try:
            task = task_queue.get()
            if not isinstance(task, dict):
                continue

            msg_type = task.get("type", "RENDER")

            # Check shutdown signal
            if msg_type == "STOP":
                break

            req_id = task.get("id")
            text = task.get("text", "")
            voice_id = task.get("voice_id", "af_bella")
            speed = float(task.get("speed", 1.0))
            lang = task.get("lang", "auto")
            eq_preset = task.get("eq_preset", "Clean Studio (Default)")
            out_format = task.get("output_format", "wav").lower().strip()
            punc_ms = int(task.get("pause_punctuation_ms", 150))
            para_ms = int(task.get("pause_paragraph_ms", 400))

            # 1. Synthesize audio with multilingual G2P
            samples, sr = engine.synthesize_text(
                text=text,
                voice=voice_id,
                speed=speed,
                lang=lang,
                master_preset="Raw Unprocessed",
            )

            # Master audio with selected EQ preset
            audio_seg = engine.numpy_to_audiosegment(samples, sr)
            if eq_preset != "Raw Unprocessed":
                audio_seg = engine.apply_studio_mastering(audio_seg, preset=eq_preset)

            dur = float(len(audio_seg) / 1000.0)

            # 2. Build smart, punchy SRT subtitles (hard limit of 7-9 words / <= 40 chars / <= 3.5s per line)
            srt_content = build_srt_subtitles(
                text=text,
                total_duration=dur,
                max_words=8,
                max_chars=40,
                max_chunk_dur=3.5,
            )

            # 3. Save audio file to output directory
            file_ext = "mp3" if out_format == "mp3" else "wav"
            safe_voice = re.sub(r"[^\w\-]", "_", voice_id)
            base_name = f"kokoro_{safe_voice}_{uuid.uuid4().hex[:8]}"
            filename = f"{base_name}.{file_ext}"
            file_dest = out_path / filename

            # Export mastered audio
            engine.export_audio(audio_seg, output_path=file_dest, format=file_ext)

            # Save synchronized SRT subtitle file
            srt_filename = f"{base_name}.srt"
            srt_dest = out_path / srt_filename
            with open(srt_dest, "w", encoding="utf-8") as f:
                f.write(srt_content)

            file_size = os.path.getsize(file_dest)

            # Read audio file to base64 for instant in-memory browser playback without IDM interception
            with open(file_dest, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("ascii")

            # Determine voice name and resolved language
            v_meta = VOICE_CATALOG.get(voice_id, {})
            voice_name = v_meta.get("name", voice_id)
            resolved_lang = lang if lang != "auto" else v_meta.get("lang", "en-us")

            # Send successful response with SRT data
            response_queue.put({
                "type": "RENDER_DONE",
                "id": req_id,
                "success": True,
                "audio_path": str(file_dest.resolve()),
                "filename": filename,
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

        except Exception as err:
            response_queue.put({
                "type": "RENDER_DONE",
                "id": task.get("id") if isinstance(task, dict) else None,
                "success": False,
                "error": str(err),
            })


# ============================================================================
# Process Manager (Async Bridge in FastAPI)
# ============================================================================

class EngineProcessManager:
    """
    Manages the lifecycle of the isolated background worker process,
    tracks pending asynchronous render requests with Futures, and enforces timeouts.
    """

    def __init__(self):
        self.task_queue: Optional[mp.Queue] = None
        self.response_queue: Optional[mp.Queue] = None
        self.worker_process: Optional[mp.Process] = None
        self.is_ready: bool = False
        self.init_error: Optional[str] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listener_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start the isolated background process and response listener."""
        self._loop = loop
        self.task_queue = mp.Queue()
        self.response_queue = mp.Queue()

        self.worker_process = mp.Process(
            target=_engine_worker_loop,
            args=(
                self.task_queue,
                self.response_queue,
                str(ASSETS_DIR),
                str(OUTPUT_DIR),
            ),
            daemon=True,
        )
        self.worker_process.start()
        logger.info(f"Spawned Kokoro Engine background worker process (PID: {self.worker_process.pid})")

        # Start response listener thread
        self._listener_thread = threading.Thread(target=self._response_listener, daemon=True)
        self._listener_thread.start()

    def _response_listener(self) -> None:
        """Reads responses from child process and resolves asyncio Futures in the main event loop."""
        while True:
            try:
                if self.response_queue is None:
                    break
                msg = self.response_queue.get()
                if not isinstance(msg, dict):
                    continue

                msg_type = msg.get("type")

                # Initial loading state update
                if msg_type == "INIT_DONE":
                    if msg.get("success"):
                        self.is_ready = True
                        logger.info("Kokoro ONNX Model & Voices loaded successfully in background worker!")
                    else:
                        self.init_error = msg.get("error", "Unknown initialization failure")
                        logger.error(f"Kokoro Engine worker initialization failed: {self.init_error}")
                    continue

                # Rendering task completion
                if msg_type == "RENDER_DONE":
                    req_id = msg.get("id")
                    if req_id and req_id in self._pending_requests:
                        future = self._pending_requests.pop(req_id)
                        if not future.done() and self._loop:
                            self._loop.call_soon_threadsafe(future.set_result, msg)

            except Exception as e:
                logger.error(f"Error in response listener thread: {e}")
                break

    async def render_async(self, payload: Dict[str, Any], timeout_sec: float = 600.0) -> Dict[str, Any]:
        """
        Submits a rendering task to the background process and awaits result with dynamic timeout.
        """
        if self.init_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Engine worker failed to initialize: {self.init_error}",
            )

        if not self.is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kokoro model is currently loading in background process. Please retry in a few seconds.",
            )

        req_id = str(uuid.uuid4())
        payload["id"] = req_id
        payload["type"] = "RENDER"

        future = self._loop.create_future()
        self._pending_requests[req_id] = future

        # Send task to child process queue
        self.task_queue.put(payload)

        try:
            result = await asyncio.wait_for(future, timeout=timeout_sec)
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Speech rendering failed inside engine worker"),
                )
            return result

        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Audio rendering timed out after {timeout_sec} seconds. Try shorter text or faster speech speed.",
            )

    def shutdown(self) -> None:
        """Gracefully terminate background process on server shutdown."""
        logger.info("Shutting down Kokoro Engine worker process...")
        if self.task_queue:
            try:
                self.task_queue.put({"type": "STOP"})
            except Exception:
                pass
        if self.worker_process and self.worker_process.is_alive():
            self.worker_process.terminate()
            self.worker_process.join(timeout=2.0)


# Global process manager instance
engine_manager = EngineProcessManager()


# ============================================================================
# FastAPI Application & Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background process on server startup and shut down on exit."""
    loop = asyncio.get_running_loop()
    engine_manager.start(loop)
    yield
    engine_manager.shutdown()


app = FastAPI(
    title="Kokoro Voice Studio Pro — Backend API",
    description="Standalone, high-performance multilingual TTS & mastering backend powered by Kokoro-82M ONNX.",
    version="2.5.0",
    lifespan=lifespan,
)

# 1. Enable Universal CORS Middleware (Tauri, React, Localhost, Mobile, Extensions)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REST API Endpoints & Static SPA Delivery
# ============================================================================

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path(sys.executable).parent / "frontend" / "dist"


@app.get("/", summary="Kokoro Voice Studio Web Application")
async def root_spa():
    """Serves the production React 19 Studio application UI."""
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(
            path=str(index_file),
            media_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )
    return {
        "app": "Kokoro Voice Studio Pro API",
        "version": "2.5.0",
        "status": "ready" if engine_manager.is_ready else ("error" if engine_manager.init_error else "loading"),
        "docs_url": "/docs",
        "health_url": "/health",
        "render_url": "/render",
    }


@app.get("/api", summary="API Overview")
async def api_overview():
    """Returns basic server information and status."""
    return {
        "app": "Kokoro Voice Studio Pro API",
        "version": "2.5.0",
        "status": "ready" if engine_manager.is_ready else ("error" if engine_manager.init_error else "loading"),
        "docs_url": "/docs",
        "health_url": "/health",
        "render_url": "/render",
    }


@app.get("/icon.png", summary="Application Icon (PNG)")
async def serve_icon_png():
    for p in [BASE_DIR / "icon.png", FRONTEND_DIST / "icon.png", Path("icon.png")]:
        if p.exists():
            return FileResponse(p, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")


@app.get("/icon.ico", summary="Application Favicon (ICO)")
async def serve_icon_ico():
    for p in [BASE_DIR / "icon.ico", FRONTEND_DIST / "icon.ico", Path("icon.ico")]:
        if p.exists():
            return FileResponse(p, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="Icon not found")


@app.get("/health", response_model=HealthResponse, summary="Engine Health & Voice Catalog")
async def health_check():
    """
    Non-blocking endpoint returning engine initialization state,
    supported languages, mastering presets, and all 60 catalog voices.
    """
    engine_status = "ready" if engine_manager.is_ready else ("error" if engine_manager.init_error else "loading")

    # Format 60 voices catalog metadata
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

    # Distinct supported languages
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
        version="2.5.0",
        model_loaded=engine_manager.is_ready,
        voices_count=len(VOICE_CATALOG),
        output_directory=str(OUTPUT_DIR.resolve()),
        supported_languages=languages,
        mastering_presets=MASTERING_PRESETS,
        voices=voices_list,
    )


@app.post("/render", response_model=RenderResponse, summary="Synthesize Text to Mastered Audio")
async def render_audio(req: RenderRequest, request: Request):
    """
    Synthesize input text into speech with selected voice, speed, language, and EQ mastering preset.
    Returns the local file path, duration, file size, and direct streaming audio_url.
    """
    # Validate voice ID
    if req.voice_id not in VOICE_CATALOG:
        # Fallback to af_bella if unknown
        logger.warning(f"Requested voice '{req.voice_id}' not found in catalog, using 'af_bella'")
        req.voice_id = "af_bella"

    # Validate EQ preset
    if req.eq_preset not in MASTERING_PRESETS:
        req.eq_preset = "Clean Studio (Default)"

    # Dispatch to background process with generous dynamic timeout (10-20 minutes for long scripts)
    text_len = len(req.text or "")
    dynamic_timeout = max(600.0, float(text_len * 4.0))
    result = await engine_manager.render_async(req.model_dump(), timeout_sec=dynamic_timeout)

    filename = result["filename"]
    # Build relative / absolute audio URL
    base_url = str(request.base_url).rstrip("/")
    audio_url = f"{base_url}/audio/{filename}"

    return RenderResponse(
        success=True,
        audio_path=result["audio_path"],
        audio_url=audio_url,
        filename=filename,
        duration=result["duration"],
        sample_rate=result["sample_rate"],
        file_size_bytes=result["file_size_bytes"],
        voice_id=result["voice_id"],
        voice_name=result["voice_name"],
        lang_resolved=result["lang_resolved"],
        eq_preset=result["eq_preset"],
        audio_base64=result.get("audio_base64"),
        srt_content=result.get("srt_content"),
        srt_filename=result.get("srt_filename"),
    )


@app.get("/audio/{filename}", summary="Stream or Download Rendered Audio File")
async def get_audio_file(filename: str):
    """
    Stream or download generated audio file from the output directory with CORS headers.
    """
    # Sanitize filename against path traversal
    safe_filename = Path(filename).name
    file_path = OUTPUT_DIR / safe_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file '{safe_filename}' not found on server",
        )

    media_type = "audio/mpeg" if safe_filename.endswith(".mp3") else "audio/wav"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        content_disposition_type="inline",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f'inline; filename="{safe_filename}"',
        },
    )


@app.get("/voices", summary="List All 60 Available Voices")
async def list_voices():
    """Returns the full dictionary catalog of all 60 supported international voices."""
    return {
        "count": len(VOICE_CATALOG),
        "voices": VOICE_CATALOG,
    }


@app.get("/presets", summary="List Mastering EQ Presets")
async def list_presets():
    """Returns all acoustic EQ and compression mastering presets."""
    return {
        "count": len(MASTERING_PRESETS),
        "presets": MASTERING_PRESETS,
    }


# ============================================================================
# Static Frontend SPA Mounting (Serves React 19 UI Bundle)
# ============================================================================

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static-root")


# ============================================================================
# Main Entry Point with Windows Freeze Support
# ============================================================================

if __name__ == "__main__":
    # Required for Windows multiprocessing support and PyInstaller compilation
    mp.freeze_support()

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("\n" + "=" * 62)
    print("   [*] Kokoro Voice Studio Pro - FastAPI Backend Server")
    print(f"   [*] Server URL: http://127.0.0.1:{port} (LAN: http://0.0.0.0:{port})")
    print(f"   [*] Interactive Swagger Docs: http://127.0.0.1:{port}/docs")
    print("   [*] Async Process Isolation: ENABLED")
    print("   [*] CORS Allowed Origins: ['*']")
    print("=" * 62 + "\n")

    uvicorn.run(app, host=host, port=port, log_level="info")
