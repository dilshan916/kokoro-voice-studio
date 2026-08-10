"""
Kokoro Voice Studio — Pro Edition Desktop Application
=====================================================
Studio-Grade, 100% Offline Text-to-Speech Desktop Application
Powered by Kokoro-82M ONNX
"""

from __future__ import annotations

import math
import os
import random
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import Canvas, filedialog, messagebox

import customtkinter as ctk
from PIL import Image
from pydub import AudioSegment

from core.audio_player import AudioPlayer
from core.kokoro_engine import VOICE_CATALOG, KokoroStudioEngine
from core.srt_generator import SubtitleGenerator

# High-End Dark Modern Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Theme Palette Tokens
BG_MAIN = "#0d1017"
BG_PANEL = "#131722"
BG_CARD = "#1a1f2c"
BG_CARD_HOVER = "#232a3b"
ACCENT_CYAN = "#00d2ff"
ACCENT_BLUE = "#3b82f6"
ACCENT_EMERALD = "#10b981"
ACCENT_PURPLE = "#8b5cf6"
TEXT_MUTED = "#8e9bb0"
TEXT_LIGHT = "#f1f5f9"
BORDER_COLOR = "#232a3b"


class KokoroStudioApp(ctk.CTk):
    """Main Pro Desktop Application Window for Kokoro Voice Studio."""

    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("🎙️ Kokoro Voice Studio Pro — Offline AI Audio Engine")
        self.geometry("1240x860")
        self.minsize(1100, 750)
        self.configure(fg_color=BG_MAIN)

        # Core Components
        self.base_dir = Path(__file__).resolve().parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.engine = KokoroStudioEngine()
        self.player = AudioPlayer()

        # Application State
        self.current_audio_seg: AudioSegment | None = None
        self.current_audio_path: Path | None = None
        self.current_duration_sec: float = 0.0
        self.is_synthesizing = False
        self.multi_speaker_map = {}
        self.recent_files = []
        self.editor_font_size = 14

        # Waveform animation timer
        self.is_animating_wave = False
        self.playback_start_time = 0.0
        self.seek_offset = 0.0

        # Build UI Architecture
        self._build_top_navbar()
        self._build_main_content()
        self._build_player_dock()
        self._build_statusbar()

        # Load Recent History
        self._refresh_recent_history()

        # Engine background load
        threading.Thread(target=self._warmup_engine, daemon=True).start()

        # Start playback progress polling loop
        self.after(100, self._poll_playback_progress)

    def _warmup_engine(self):
        try:
            self.set_status("Initializing Kokoro-82M ONNX weights...", 0.3)
            self.engine.load_model()
            self.set_status("Ready — Kokoro-82M Engine Active (CPU Real-Time Inference)", 1.0)
            self.model_status_badge.configure(text="● Engine: Ready (CPU)", text_color=ACCENT_EMERALD)
        except Exception as e:
            self.set_status(f"Error loading model: {e}", 0.0)
            self.model_status_badge.configure(text="● Engine: Error", text_color="#ef4444")

    # ------------------------------------------------------------------
    # Top Modern Navigation Bar
    # ------------------------------------------------------------------

    def _build_top_navbar(self):
        nav = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=BG_PANEL, border_width=1, border_color=BORDER_COLOR)
        nav.pack(fill="x", side="top", padx=0, pady=0)

        # Brand Container
        brand_frame = ctk.CTkFrame(nav, fg_color="transparent")
        brand_frame.pack(side="left", padx=25, pady=12)

        logo_title = ctk.CTkLabel(
            brand_frame,
            text="🎙️ KOKORO STUDIO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT_CYAN,
        )
        logo_title.pack(side="left", padx=(0, 10))

        pro_badge = ctk.CTkLabel(
            brand_frame,
            text="PRO v2.0",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1e293b",
            text_color="#94a3b8",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        pro_badge.pack(side="left", padx=2)

        # Model Status Badge
        self.model_status_badge = ctk.CTkLabel(
            nav,
            text="● Engine: Loading...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f59e0b",
        )
        self.model_status_badge.pack(side="left", padx=30)

        # Right Action Buttons
        right_actions = ctk.CTkFrame(nav, fg_color="transparent")
        right_actions.pack(side="right", padx=20, pady=14)

        sample_lib_btn = ctk.CTkButton(
            right_actions,
            text="🔊 Test Voices",
            width=120,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._open_voice_library_modal,
        )
        sample_lib_btn.pack(side="left", padx=6)

        open_folder_btn = ctk.CTkButton(
            right_actions,
            text="📂 Output Folder",
            width=130,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._open_output_folder,
        )
        open_folder_btn.pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Main Body & Tabview
    # ------------------------------------------------------------------

    def _build_main_content(self):
        # Master Tabview
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=14,
            fg_color=BG_PANEL,
            segmented_button_selected_color=ACCENT_BLUE,
            segmented_button_selected_hover_color="#2563eb",
            segmented_button_unselected_color=BG_CARD,
            segmented_button_unselected_hover_color=BG_CARD_HOVER,
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(12, 6))

        self.tab_single = self.tabview.add("  🎙️ Single Narrator Studio  ")
        self.tab_multi = self.tabview.add("  🎭 Multi-Speaker Drama  ")
        self.tab_batch = self.tabview.add("  📂 Batch File Queue  ")
        self.tab_history = self.tabview.add("  📜 Recent Audio Library  ")

        self._build_single_tab()
        self._build_multi_tab()
        self._build_batch_tab()
        self._build_history_tab()

    # ------------------------------------------------------------------
    # TAB 1: Single Narrator Studio
    # ------------------------------------------------------------------

    def _build_single_tab(self):
        tab = self.tab_single

        # Top Toolbar for Single Tab
        toolbar = ctk.CTkFrame(tab, fg_color="transparent", height=35)
        toolbar.pack(fill="x", padx=15, pady=(5, 5))

        lbl = ctk.CTkLabel(toolbar, text="Script Editor", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(side="left")

        # Quick Script Actions
        btn_paste = ctk.CTkButton(
            toolbar,
            text="📋 Paste",
            width=75,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._paste_single_text,
        )
        btn_paste.pack(side="right", padx=4)

        btn_sample = ctk.CTkButton(
            toolbar,
            text="💡 Sample Story",
            width=110,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._load_sample_story,
        )
        btn_sample.pack(side="right", padx=4)

        btn_clear = ctk.CTkButton(
            toolbar,
            text="🗑️ Clear",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#3c1d1d",
            hover_color="#5a2b2b",
            command=lambda: self.single_text.delete("1.0", "end"),
        )
        btn_clear.pack(side="right", padx=4)

        # Editor Box
        self.single_text = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Segoe UI", size=self.editor_font_size),
            wrap="word",
            corner_radius=10,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.single_text.pack(fill="both", expand=True, padx=15, pady=(0, 6))
        self.single_text.insert(
            "1.0",
            "Welcome to Kokoro Voice Studio Pro. This is a studio-grade offline text to speech engine running entirely on your computer with zero cloud latency. Enjoy hyper-realistic narration, custom speed control, and multi-character dialogue generation for your videos and podcasts.",
        )
        self.single_text.bind("<KeyRelease>", self._update_single_stats)

        # Stats Bar below editor
        self.stats_label = ctk.CTkLabel(
            tab,
            text="📊 46 Words | 312 Characters | Est. 0:18 Duration",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )
        self.stats_label.pack(anchor="w", padx=20, pady=(0, 8))

        # Controls Card
        controls_card = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        controls_card.pack(fill="x", padx=15, pady=(0, 10))

        # Grid config
        controls_card.columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Voice Selector
        v_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        v_frame.grid(row=0, column=0, columnspan=2, padx=15, pady=12, sticky="w")

        ctk.CTkLabel(v_frame, text="Narrator Voice:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))

        voice_options = [label for _, label in self.engine.get_available_voices()]
        self.single_voice_var = ctk.StringVar(value=voice_options[0])
        self.single_voice_menu = ctk.CTkOptionMenu(
            v_frame,
            values=voice_options,
            variable=self.single_voice_var,
            width=340,
            height=34,
            fg_color="#242b3d",
            button_color="#3b82f6",
            button_hover_color="#2563eb",
        )
        self.single_voice_menu.pack(side="left", padx=(0, 8))

        btn_preview_curr = ctk.CTkButton(
            v_frame,
            text="🔊",
            width=38,
            height=34,
            font=ctk.CTkFont(size=14),
            fg_color="#242b3d",
            hover_color=BG_CARD_HOVER,
            command=self._preview_current_voice,
        )
        btn_preview_curr.pack(side="left")

        # Speed Slider
        s_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        s_frame.grid(row=0, column=2, padx=15, pady=12, sticky="w")

        s_header = ctk.CTkFrame(s_frame, fg_color="transparent")
        s_header.pack(fill="x")
        ctk.CTkLabel(s_header, text="Playback Speed:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(side="left")
        self.single_speed_val_label = ctk.CTkLabel(s_header, text="1.00x", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN)
        self.single_speed_val_label.pack(side="right")

        self.single_speed_slider = ctk.CTkSlider(
            s_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=30,
            width=180,
            progress_color=ACCENT_BLUE,
            command=self._on_single_speed_change,
        )
        self.single_speed_slider.set(1.0)
        self.single_speed_slider.pack(pady=(4, 0))

        # Format Selector
        fmt_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        fmt_frame.grid(row=0, column=3, padx=15, pady=12, sticky="w")
        ctk.CTkLabel(fmt_frame, text="Audio Format:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        self.single_fmt_var = ctk.StringVar(value="MP3 (192kbps)")
        self.single_fmt_menu = ctk.CTkOptionMenu(
            fmt_frame,
            values=["MP3 (192kbps)", "WAV (Uncompressed)", "OGG (Vorbis)"],
            variable=self.single_fmt_var,
            width=160,
            height=34,
            fg_color="#242b3d",
        )
        self.single_fmt_menu.pack()

        # Action Buttons Row
        action_row = ctk.CTkFrame(tab, fg_color="transparent")
        action_row.pack(fill="x", padx=15, pady=(0, 8))

        self.btn_single_generate = ctk.CTkButton(
            action_row,
            text="⚡ Generate Speech",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            corner_radius=8,
            command=self._generate_single_speech,
        )
        self.btn_single_generate.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_single_save = ctk.CTkButton(
            action_row,
            text="💾 Save Audio File...",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            corner_radius=8,
            border_width=1,
            border_color=BORDER_COLOR,
            command=self._save_single_audio_as,
        )
        self.btn_single_save.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_single_srt = ctk.CTkButton(
            action_row,
            text="📜 Export Subtitles (.SRT)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            corner_radius=8,
            border_width=1,
            border_color=BORDER_COLOR,
            command=self._export_single_srt,
        )
        self.btn_single_srt.pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _update_single_stats(self, event=None):
        text = self.single_text.get("1.0", "end").strip()
        words = len(text.split()) if text else 0
        chars = len(text)
        # Average reading speed ~ 150 words per minute
        est_sec = int((words / 150) * 60)
        mins = est_sec // 60
        secs = est_sec % 60
        self.stats_label.configure(text=f"📊 {words} Words | {chars} Characters | Est. {mins}:{secs:02d} Duration")

    def _on_single_speed_change(self, val):
        self.single_speed_val_label.configure(text=f"{val:.2f}x")

    def _paste_single_text(self):
        try:
            clipboard = self.clipboard_get()
            self.single_text.insert("insert", clipboard)
            self._update_single_stats()
        except Exception:
            pass

    def _load_sample_story(self):
        sample = (
            "I never expected a routine trip to the grocery store to turn into a life-changing encounter. "
            "As I walked down the quiet aisle, an elderly man was struggling to reach a box of cereal on the top shelf. "
            "I stepped in to help him, and his warm smile instantly reminded me of my grandfather. "
            "We ended up talking for nearly thirty minutes about history, family, and the power of simple kindness."
        )
        self.single_text.delete("1.0", "end")
        self.single_text.insert("1.0", sample)
        self._update_single_stats()

    def _preview_current_voice(self):
        voice_label = self.single_voice_var.get()
        voice_key = self._get_selected_voice_key(voice_label)
        self._play_voice_sample(voice_key)

    # ------------------------------------------------------------------
    # TAB 2: Multi-Speaker Drama Studio
    # ------------------------------------------------------------------

    def _build_multi_tab(self):
        tab = self.tab_multi

        # Header Helper
        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(5, 5))

        info_lbl = ctk.CTkLabel(
            top_bar,
            text="Dialogue Script Format: [CharacterName]: Speech line...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_MUTED,
        )
        info_lbl.pack(side="left")

        btn_tmpl1 = ctk.CTkButton(
            top_bar,
            text="🎭 Drama Template",
            width=130,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._load_multi_template_drama,
        )
        btn_tmpl1.pack(side="right", padx=4)

        btn_tmpl2 = ctk.CTkButton(
            top_bar,
            text="🎙️ Podcast Template",
            width=135,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._load_multi_template_podcast,
        )
        btn_tmpl2.pack(side="right", padx=4)

        # Main Split Frame
        split_frame = ctk.CTkFrame(tab, fg_color="transparent")
        split_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Left: Script Text Editor
        self.multi_text = ctk.CTkTextbox(
            split_frame,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            wrap="word",
            corner_radius=10,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.multi_text.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.multi_text.insert(
            "1.0",
            "[Adam]: Have you tested the new multi-character synthesizer yet?\n"
            "[Bella]: Yes! The voice transitions are seamless and it runs 100% offline.\n"
            "[George]: Indeed. The cadence and emotional depth sound exceptionally natural.\n"
            "[Adam]: Let's generate and export the full conversation right away!",
        )

        # Right: Speaker Voice Mapping Container
        right_container = ctk.CTkFrame(split_frame, width=400, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        right_container.pack(side="right", fill="both", expand=False)

        rp_header = ctk.CTkFrame(right_container, fg_color="transparent")
        rp_header.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(rp_header, text="👥 Character Cast", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        detect_btn = ctk.CTkButton(
            rp_header,
            text="🔍 Refresh Cast",
            width=110,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._detect_speakers,
        )
        detect_btn.pack(side="right")

        self.speaker_panel = ctk.CTkScrollableFrame(right_container, fg_color="transparent")
        self.speaker_panel.pack(fill="both", expand=True, padx=6, pady=5)

        # Multi Options Row
        multi_opt_frame = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        multi_opt_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(multi_opt_frame, text="Pause Between Characters:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).grid(
            row=0, column=0, padx=15, pady=10, sticky="w"
        )

        self.multi_pause_val_label = ctk.CTkLabel(multi_opt_frame, text="350 ms", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN)
        self.multi_pause_val_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.multi_pause_slider = ctk.CTkSlider(
            multi_opt_frame,
            from_=100,
            to=1500,
            number_of_steps=28,
            width=220,
            progress_color=ACCENT_BLUE,
            command=lambda v: self.multi_pause_val_label.configure(text=f"{int(v)} ms"),
        )
        self.multi_pause_slider.set(350)
        self.multi_pause_slider.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        # Multi Action Buttons Row
        m_action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        m_action_frame.pack(fill="x", padx=15, pady=5)

        self.btn_multi_generate = ctk.CTkButton(
            m_action_frame,
            text="🎭 Generate Multi-Speaker Drama",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._generate_multi_speech,
        )
        self.btn_multi_generate.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_multi_save = ctk.CTkButton(
            m_action_frame,
            text="💾 Save Combined Audio...",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            border_width=1,
            border_color=BORDER_COLOR,
            command=self._save_single_audio_as,
        )
        self.btn_multi_save.pack(side="left", fill="x", expand=True, padx=4)

        self._detect_speakers()

    def _load_multi_template_drama(self):
        text = (
            "[Adam]: I can't believe she actually showed up after everything that happened.\n"
            "[Bella]: Keep your voice down! She might hear you across the room.\n"
            "[George]: Quiet, both of you. We need to handle this with dignity and respect.\n"
            "[Bella]: Easy for you to say, George. You weren't the one who lost everything."
        )
        self.multi_text.delete("1.0", "end")
        self.multi_text.insert("1.0", text)
        self._detect_speakers()

    def _load_multi_template_podcast(self):
        text = (
            "[Host]: Welcome back to The Daily Deep Dive podcast. Today we're exploring local offline AI.\n"
            "[Guest]: Thanks for having me! The leap in performance without GPU dependence is astonishing.\n"
            "[Host]: Exactly. People can now voice entire audiobooks from their home computers."
        )
        self.multi_text.delete("1.0", "end")
        self.multi_text.insert("1.0", text)
        self._detect_speakers()

    def _detect_speakers(self):
        for child in self.speaker_panel.winfo_children():
            child.destroy()

        text = self.multi_text.get("1.0", "end")
        speakers = []
        for line in text.splitlines():
            match = re.match(r"^\[([a-zA-Z0-9_\s]+)\]\s*:", line.strip())
            if match:
                s = match.group(1).strip()
                if s not in speakers:
                    speakers.append(s)

        if not speakers:
            speakers = ["Narrator"]

        voice_options = [label for _, label in self.engine.get_available_voices()]
        palette_colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4"]
        defaults = ["am_adam", "af_bella", "bm_george", "af_nicole", "af_sky", "am_michael"]

        self.multi_speaker_map = {}
        for idx, speaker in enumerate(speakers):
            color = palette_colors[idx % len(palette_colors)]
            card = ctk.CTkFrame(self.speaker_panel, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", padx=4, pady=5)

            badge_frame = ctk.CTkFrame(card, fg_color="transparent")
            badge_frame.pack(fill="x", padx=8, pady=(6, 2))

            color_pill = ctk.CTkLabel(
                badge_frame,
                text=f"  {speaker}  ",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=color,
                text_color="#ffffff",
                corner_radius=6,
            )
            color_pill.pack(side="left")

            default_voice_key = defaults[idx % len(defaults)]
            default_label = next(
                (lbl for key, lbl in self.engine.get_available_voices() if key == default_voice_key),
                voice_options[0],
            )

            var = ctk.StringVar(value=default_label)
            menu = ctk.CTkOptionMenu(
                card,
                values=voice_options,
                variable=var,
                height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#242b3d",
            )
            menu.pack(fill="x", padx=8, pady=(4, 8))

            self.multi_speaker_map[speaker] = var

    # ------------------------------------------------------------------
    # TAB 3: Batch File Queue
    # ------------------------------------------------------------------

    def _build_batch_tab(self):
        tab = self.tab_batch

        card = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True, padx=15, pady=10)

        b_header = ctk.CTkFrame(card, fg_color="transparent")
        b_header.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(b_header, text="📂 Batch Text-to-Speech Queue", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        btn_add = ctk.CTkButton(
            b_header,
            text="➕ Add .txt Files...",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._select_batch_files,
        )
        btn_add.pack(side="right", padx=4)

        btn_clear = ctk.CTkButton(
            b_header,
            text="🗑️ Clear Queue",
            font=ctk.CTkFont(size=12),
            fg_color="#3a2525",
            hover_color="#5a3535",
            command=lambda: self.batch_files_listbox.delete("1.0", "end"),
        )
        btn_clear.pack(side="right", padx=4)

        self.batch_files_listbox = ctk.CTkTextbox(
            card,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.batch_files_listbox.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        # Batch Settings Bottom Bar
        b_bottom = ctk.CTkFrame(card, fg_color="transparent")
        b_bottom.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(b_bottom, text="Default Voice for Queue:", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(
            side="left", padx=(0, 8)
        )

        voice_options = [label for _, label in self.engine.get_available_voices()]
        self.batch_voice_var = ctk.StringVar(value=voice_options[0])
        batch_voice_menu = ctk.CTkOptionMenu(
            b_bottom,
            values=voice_options,
            variable=self.batch_voice_var,
            width=280,
            height=32,
            fg_color="#242b3d",
        )
        batch_voice_menu.pack(side="left", padx=5)

        self.btn_start_batch = ctk.CTkButton(
            b_bottom,
            text="🚀 Process All Files",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color=ACCENT_EMERALD,
            hover_color="#059669",
            command=self._run_batch_conversion,
        )
        self.btn_start_batch.pack(side="right", padx=5)

    def _select_batch_files(self):
        files = filedialog.askopenfilenames(
            title="Select Text Files for TTS",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if files:
            for f in files:
                self.batch_files_listbox.insert("end", f + "\n")

    # ------------------------------------------------------------------
    # TAB 4: Recent Audio Library
    # ------------------------------------------------------------------

    def _build_history_tab(self):
        tab = self.tab_history

        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(header, text="📜 Recently Exported Audio Files", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        btn_refresh = ctk.CTkButton(
            header,
            text="🔄 Refresh Library",
            width=130,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._refresh_recent_history,
        )
        btn_refresh.pack(side="right")

        self.history_scroll = ctk.CTkScrollableFrame(tab, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        self.history_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _refresh_recent_history(self):
        for child in self.history_scroll.winfo_children():
            child.destroy()

        audio_files = sorted(
            list(self.output_dir.glob("*.mp3")) + list(self.output_dir.glob("*.wav")),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if not audio_files:
            empty_lbl = ctk.CTkLabel(
                self.history_scroll,
                text="No generated audio files found in output directory.\nGenerate speech above to populate your library!",
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
            )
            empty_lbl.pack(pady=40)
            return

        for f in audio_files[:30]:
            card = ctk.CTkFrame(self.history_scroll, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", padx=6, pady=4)

            size_mb = f.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")

            info_col = ctk.CTkFrame(card, fg_color="transparent")
            info_col.pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(info_col, text=f"🎵 {f.name}", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_col, text=f"{mtime}  •  {size_mb:.2f} MB", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w")

            btn_play = ctk.CTkButton(
                card,
                text="▶ Play",
                width=75,
                height=28,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=ACCENT_BLUE,
                hover_color="#2563eb",
                command=lambda path=f: self._play_history_file(path),
            )
            btn_play.pack(side="right", padx=10, pady=8)

    def _play_history_file(self, path: Path):
        self.player.play_file(path)
        self.current_audio_path = path
        try:
            seg = AudioSegment.from_file(str(path))
            self.current_audio_seg = seg
            self.current_duration_sec = len(seg) / 1000.0
        except Exception:
            self.current_duration_sec = 60.0
        self.playback_start_time = time.time()
        self.track_label.configure(text=f"🎵 {path.name}")
        self.btn_play_pause.configure(text="⏸ Pause")

    # ------------------------------------------------------------------
    # Bottom Studio Audio Player Dock with Waveform
    # ------------------------------------------------------------------

    def _build_player_dock(self):
        dock = ctk.CTkFrame(self, height=85, corner_radius=12, fg_color=BG_PANEL, border_width=1, border_color=BORDER_COLOR)
        dock.pack(fill="x", side="bottom", padx=20, pady=(4, 10))

        # Controls Left
        ctrl_frame = ctk.CTkFrame(dock, fg_color="transparent")
        ctrl_frame.pack(side="left", padx=15, pady=12)

        self.btn_play_pause = ctk.CTkButton(
            ctrl_frame,
            text="▶ Play",
            width=85,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._toggle_playback,
        )
        self.btn_play_pause.pack(side="left", padx=(0, 6))

        self.btn_stop = ctk.CTkButton(
            ctrl_frame,
            text="⏹ Stop",
            width=70,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._stop_playback,
        )
        self.btn_stop.pack(side="left", padx=4)

        # Center Track Info & Waveform Simulator Canvas
        center_frame = ctk.CTkFrame(dock, fg_color="transparent")
        center_frame.pack(side="left", fill="both", expand=True, padx=15, pady=8)

        info_line = ctk.CTkFrame(center_frame, fg_color="transparent")
        info_line.pack(fill="x")

        self.track_label = ctk.CTkLabel(
            info_line,
            text="No audio loaded. Generate speech above to start listening.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_LIGHT,
        )
        self.track_label.pack(side="left")

        self.time_label = ctk.CTkLabel(
            info_line,
            text="00:00 / 00:00",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=ACCENT_CYAN,
        )
        self.time_label.pack(side="right")

        # Playback Progress Slider
        self.playback_slider = ctk.CTkProgressBar(center_frame, height=8, progress_color=ACCENT_CYAN, fg_color=BG_CARD)
        self.playback_slider.set(0.0)
        self.playback_slider.pack(fill="x", pady=(4, 0))

        # Volume Controls Right
        vol_frame = ctk.CTkFrame(dock, fg_color="transparent")
        vol_frame.pack(side="right", padx=20, pady=12)

        ctk.CTkLabel(vol_frame, text="🔊", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 4))

        self.vol_slider = ctk.CTkSlider(
            vol_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            width=110,
            progress_color=ACCENT_BLUE,
            command=lambda v: self.player.set_volume(v),
        )
        self.vol_slider.set(1.0)
        self.vol_slider.pack(side="left")

    def _build_statusbar(self):
        status_frame = ctk.CTkFrame(self, height=26, corner_radius=0, fg_color="transparent")
        status_frame.pack(fill="x", side="bottom", padx=25, pady=(0, 2))

        self.status_label = ctk.CTkLabel(status_frame, text="Ready", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.status_label.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=220, height=8, progress_color=ACCENT_BLUE)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right")

    def set_status(self, text: str, progress: float = 0.0):
        self.status_label.configure(text=text)
        self.progress_bar.set(progress)
        self.update_idletasks()

    # ------------------------------------------------------------------
    # Playback Logic & Timeline Polling
    # ------------------------------------------------------------------

    def _poll_playback_progress(self):
        if self.player.is_playing() and self.current_duration_sec > 0:
            elapsed = time.time() - self.playback_start_time
            if elapsed > self.current_duration_sec:
                self.player.stop()
                self.btn_play_pause.configure(text="▶ Play")
                self.playback_slider.set(0.0)
                self.time_label.configure(text=f"00:00 / {self._format_sec(self.current_duration_sec)}")
            else:
                fraction = min(1.0, elapsed / self.current_duration_sec)
                self.playback_slider.set(fraction)
                self.time_label.configure(text=f"{self._format_sec(elapsed)} / {self._format_sec(self.current_duration_sec)}")
        elif not self.player.is_playing() and not self.player.is_paused():
            self.btn_play_pause.configure(text="▶ Play")

        self.after(150, self._poll_playback_progress)

    def _format_sec(self, s: float) -> str:
        mins = int(s // 60)
        secs = int(s % 60)
        return f"{mins:02d}:{secs:02d}"

    def _toggle_playback(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play_pause.configure(text="▶ Play")
        elif self.player.is_paused():
            self.player.unpause()
            self.playback_start_time = time.time() - (self.playback_slider.get() * self.current_duration_sec)
            self.btn_play_pause.configure(text="⏸ Pause")
        elif self.current_audio_seg is not None:
            self.player.play_segment(self.current_audio_seg)
            self.playback_start_time = time.time()
            self.btn_play_pause.configure(text="⏸ Pause")

    def _stop_playback(self):
        self.player.stop()
        self.btn_play_pause.configure(text="▶ Play")
        self.playback_slider.set(0.0)

    # ------------------------------------------------------------------
    # Voice Library Modal
    # ------------------------------------------------------------------

    def _open_voice_library_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("🎙️ Kokoro Voice Library & Sample Tester")
        win.geometry("680x580")
        win.transient(self)
        win.configure(fg_color=BG_MAIN)

        lbl = ctk.CTkLabel(win, text="🌟 Kokoro-82M Voice Catalog", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN)
        lbl.pack(pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(win, fg_color=BG_PANEL, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for key, info in VOICE_CATALOG.items():
            row = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            row.pack(fill="x", padx=6, pady=4)

            icon = "👩" if info["gender"] == "Female" else "👨"
            accent_pill = "🇺🇸 " if info["accent"] == "American" else "🇬🇧 "

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(left, text=f"{icon} {info['name']} ({accent_pill}{info['accent']})", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=info["description"], font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w")

            btn_test = ctk.CTkButton(
                row,
                text="🔊 Listen Sample",
                width=120,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=ACCENT_BLUE,
                hover_color="#2563eb",
                command=lambda v=key: self._play_voice_sample(v),
            )
            btn_test.pack(side="right", padx=12, pady=8)

    def _play_voice_sample(self, voice_key: str):
        sample_text = f"Hello! I am {VOICE_CATALOG[voice_key]['name']}. This is a live demonstration of my speech quality."

        def _worker():
            try:
                self.set_status(f"Synthesizing preview for {voice_key}...", 0.4)
                samples, sr = self.engine.synthesize_text(sample_text, voice=voice_key, speed=1.0)
                seg = self.engine.numpy_to_audiosegment(samples, sr)
                self.player.play_segment(seg)
                self.set_status("Ready", 1.0)
            except Exception as e:
                self.set_status(f"Preview failed: {e}", 0.0)

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Synthesis & Export Handlers
    # ------------------------------------------------------------------

    def _generate_single_speech(self):
        if self.is_synthesizing:
            return

        text = self.single_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Input", "Please enter some text in the script editor.")
            return

        voice_display = self.single_voice_var.get()
        voice_key = self._get_selected_voice_key(voice_display)
        speed = self.single_speed_slider.get()

        def _worker():
            self.is_synthesizing = True
            self.btn_single_generate.configure(state="disabled", text="⏳ Synthesizing Speech...")
            try:
                self.set_status(f"Generating audio with {voice_key} ({speed:.2f}x)...", 0.3)
                samples, sr = self.engine.synthesize_text(text, voice=voice_key, speed=speed)
                self.current_audio_seg = self.engine.numpy_to_audiosegment(samples, sr)
                self.current_duration_sec = len(self.current_audio_seg) / 1000.0

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"kokoro_{voice_key}_{timestamp}.mp3"
                save_path = self.output_dir / filename
                self.engine.export_audio(self.current_audio_seg, save_path, format="mp3")
                self.current_audio_path = save_path

                # Update UI
                self.track_label.configure(text=f"🎵 {filename}")
                self.time_label.configure(text=f"00:00 / {self._format_sec(self.current_duration_sec)}")
                self.set_status("✓ Speech successfully synthesized and saved!", 1.0)

                # Play audio
                self.player.play_segment(self.current_audio_seg)
                self.playback_start_time = time.time()
                self.btn_play_pause.configure(text="⏸ Pause")

                self._refresh_recent_history()
            except Exception as e:
                messagebox.showerror("Synthesis Error", str(e))
                self.set_status(f"Error: {e}", 0.0)
            finally:
                self.is_synthesizing = False
                self.btn_single_generate.configure(state="normal", text="⚡ Generate Speech")

        threading.Thread(target=_worker, daemon=True).start()

    def _generate_multi_speech(self):
        if self.is_synthesizing:
            return

        text = self.multi_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Script", "Please enter a dialogue script.")
            return

        blocks = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^\[([a-zA-Z0-9_\s]+)\]\s*:\s*(.+)$", line)
            if match:
                speaker = match.group(1).strip()
                dialogue = match.group(2).strip()
                blocks.append({"speaker": speaker, "text": dialogue})
            else:
                blocks.append({"speaker": "Narrator", "text": line})

        if not blocks:
            messagebox.showwarning("Invalid Script", "No character turns detected. Use [SpeakerName]: format.")
            return

        speaker_map = {}
        for speaker, var in self.multi_speaker_map.items():
            speaker_map[speaker] = self._get_selected_voice_key(var.get())

        pause_ms = int(self.multi_pause_slider.get())

        def _worker():
            self.is_synthesizing = True
            self.btn_multi_generate.configure(state="disabled", text="⏳ Synthesizing Drama...")
            try:
                self.current_audio_seg = self.engine.synthesize_dialogue(
                    dialogue_blocks=blocks,
                    speaker_voice_map=speaker_map,
                    pause_ms=pause_ms,
                    progress_callback=lambda f, msg: self.set_status(msg, f),
                )
                self.current_duration_sec = len(self.current_audio_seg) / 1000.0

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"drama_dialogue_{timestamp}.mp3"
                save_path = self.output_dir / filename
                self.engine.export_audio(self.current_audio_seg, save_path, format="mp3")
                self.current_audio_path = save_path

                self.track_label.configure(text=f"🎭 {filename}")
                self.time_label.configure(text=f"00:00 / {self._format_sec(self.current_duration_sec)}")
                self.set_status("✓ Multi-Speaker Drama synthesized!", 1.0)

                self.player.play_segment(self.current_audio_seg)
                self.playback_start_time = time.time()
                self.btn_play_pause.configure(text="⏸ Pause")

                self._refresh_recent_history()
            except Exception as e:
                messagebox.showerror("Multi-Speaker Error", str(e))
                self.set_status(f"Error: {e}", 0.0)
            finally:
                self.is_synthesizing = False
                self.btn_multi_generate.configure(state="normal", text="🎭 Generate Multi-Speaker Drama")

        threading.Thread(target=_worker, daemon=True).start()

    def _run_batch_conversion(self):
        file_paths = [p.strip() for p in self.batch_files_listbox.get("1.0", "end").splitlines() if p.strip()]
        if not file_paths:
            messagebox.showwarning("No Files", "Please select at least one .txt file.")
            return

        voice_key = self._get_selected_voice_key(self.batch_voice_var.get())

        def _worker():
            self.btn_start_batch.configure(state="disabled", text="⏳ Processing Queue...")
            total = len(file_paths)
            for idx, f_path_str in enumerate(file_paths):
                f_path = Path(f_path_str)
                if not f_path.exists():
                    continue
                try:
                    with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    self.set_status(f"Synthesizing ({idx + 1}/{total}): {f_path.name}...", idx / total)
                    samples, sr = self.engine.synthesize_text(content, voice=voice_key)
                    seg = self.engine.numpy_to_audiosegment(samples, sr)

                    out_name = f_path.stem + f"_{voice_key}.mp3"
                    out_path = self.output_dir / out_name
                    self.engine.export_audio(seg, out_path, format="mp3")
                except Exception as e:
                    print(f"Batch item failed: {e}")

            self.set_status(f"✓ Batch conversion complete ({total} files).", 1.0)
            self.btn_start_batch.configure(state="normal", text="🚀 Process All Files")
            self._refresh_recent_history()
            messagebox.showinfo("Batch Complete", f"Successfully converted {total} files into:\n{self.output_dir}")

        threading.Thread(target=_worker, daemon=True).start()

    def _save_single_audio_as(self):
        if self.current_audio_seg is None:
            messagebox.showwarning("No Audio", "Please generate speech first before saving.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Rendered Audio",
            initialdir=str(self.output_dir),
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3"), ("WAV Audio", "*.wav"), ("OGG Audio", "*.ogg")],
        )
        if save_path:
            fmt = Path(save_path).suffix.replace(".", "") or "mp3"
            self.engine.export_audio(self.current_audio_seg, Path(save_path), format=fmt)
            messagebox.showinfo("File Saved", f"Audio exported successfully to:\n{save_path}")

    def _export_single_srt(self):
        if self.current_audio_seg is None:
            messagebox.showwarning("No Audio", "Please generate speech first before exporting subtitles.")
            return

        text = self.single_text.get("1.0", "end").strip()
        save_path = filedialog.asksaveasfilename(
            title="Export Synchronized Subtitles",
            initialdir=str(self.output_dir),
            defaultextension=".srt",
            filetypes=[("SubRip Subtitle (.srt)", "*.srt"), ("All files", "*.*")],
        )
        if save_path:
            total_sec = len(self.current_audio_seg) / 1000.0
            segments = [{"start_sec": 0.0, "end_sec": total_sec, "text": text}]
            SubtitleGenerator.generate_srt(segments, Path(save_path))
            messagebox.showinfo("Subtitles Exported", f"Subtitles exported successfully to:\n{save_path}")

    def _get_selected_voice_key(self, display_label: str) -> str:
        for key, info in VOICE_CATALOG.items():
            if display_label.startswith(info["name"]):
                return key
        return "af_bella"

    def _open_output_folder(self):
        if sys.platform == "win32":
            os.startfile(str(self.output_dir))
        else:
            os.system(f"xdg-open '{self.output_dir}'")


def main():
    app = KokoroStudioApp()
    app.mainloop()


if __name__ == "__main__":
    main()
