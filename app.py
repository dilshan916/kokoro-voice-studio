"""
Kokoro Voice Studio — Ultra-Pro DAW Studio Edition
==================================================
Commercial-Grade Desktop Audio Workstation Powered by Kokoro-82M ONNX.
Features: 3-Pane Glassmorphic Layout, Live Animated Waveform Visualizer,
Custom Voice Blender (Hybrid Embeddings), Master EQ Presets, and CapCut/Premiere Packaging.
"""

from __future__ import annotations

import json
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
from core.kokoro_engine import MASTERING_PRESETS, VOICE_CATALOG, KokoroStudioEngine
from core.srt_generator import SubtitleGenerator

# High-End Dark Modern Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Theme Palette Tokens (OLED Studio Grade)
BG_MAIN = "#090b10"
BG_PANEL = "#0f121a"
BG_CARD = "#161b26"
BG_CARD_HOVER = "#1f2637"
ACCENT_CYAN = "#00e5ff"
ACCENT_BLUE = "#3b82f6"
ACCENT_EMERALD = "#10b981"
ACCENT_PURPLE = "#8b5cf6"
ACCENT_ORANGE = "#f59e0b"
TEXT_MUTED = "#828fa3"
TEXT_LIGHT = "#f8fafc"
BORDER_COLOR = "#1f2637"


class KokoroStudioApp(ctk.CTk):
    """Ultra-Pro DAW Desktop Application Window for Kokoro Voice Studio."""

    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("🎙️ Kokoro Voice Studio Pro — AI Audio Workstation")
        self.geometry("1340x900")
        self.minsize(1150, 780)
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
        self.editor_font_size = 14
        self.playback_start_time = 0.0
        self.is_muted = False
        self.previous_volume = 1.0

        # Voice Blender State
        self.use_blended_voice = False
        self.current_blended_embedding = None

        # Build UI Architecture
        self._build_top_navbar()
        self._build_main_workspace()
        self._build_bottom_transport_dock()
        self._build_statusbar()

        # Load Recent History
        self._refresh_recent_history()

        # Engine background load
        threading.Thread(target=self._warmup_engine, daemon=True).start()

        # Start animation & timeline polling loop
        self.after(50, self._poll_playback_and_waveform)

    def _warmup_engine(self):
        try:
            self.set_status("Initializing Kokoro-82M ONNX neural weights...", 0.3)
            self.engine.load_model()
            self.set_status("Ready — Studio Master Engine Active (CPU Real-Time Inference)", 1.0)
            self.model_status_badge.configure(text="● Master Engine: Active", text_color=ACCENT_EMERALD)
        except Exception as e:
            self.set_status(f"Error loading model: {e}", 0.0)
            self.model_status_badge.configure(text="● Engine: Error", text_color="#ef4444")

    # ------------------------------------------------------------------
    # Top Modern Navigation Bar
    # ------------------------------------------------------------------

    def _build_top_navbar(self):
        nav = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=BG_PANEL, border_width=1, border_color=BORDER_COLOR)
        nav.pack(fill="x", side="top", padx=0, pady=0)

        # Brand Container
        brand_frame = ctk.CTkFrame(nav, fg_color="transparent")
        brand_frame.pack(side="left", padx=20, pady=10)

        logo_title = ctk.CTkLabel(
            brand_frame,
            text="🎙️ KOKORO STUDIO",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color=ACCENT_CYAN,
        )
        logo_title.pack(side="left", padx=(0, 8))

        pro_badge = ctk.CTkLabel(
            brand_frame,
            text="ULTRA-PRO DAW",
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color="#1e293b",
            text_color="#38bdf8",
            corner_radius=6,
            padx=7,
            pady=2,
        )
        pro_badge.pack(side="left", padx=2)

        self.model_status_badge = ctk.CTkLabel(
            nav,
            text="● Master Engine: Loading...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ACCENT_ORANGE,
        )
        self.model_status_badge.pack(side="left", padx=20)

        # Right Action Buttons
        right_actions = ctk.CTkFrame(nav, fg_color="transparent")
        right_actions.pack(side="right", padx=15, pady=12)

        btn_save_proj = ctk.CTkButton(
            right_actions,
            text="💾 Save Project",
            width=110,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._save_project_file,
        )
        btn_save_proj.pack(side="left", padx=4)

        btn_open_proj = ctk.CTkButton(
            right_actions,
            text="📂 Open Project",
            width=110,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._load_project_file,
        )
        btn_open_proj.pack(side="left", padx=4)

        btn_capcut = ctk.CTkButton(
            right_actions,
            text="🎬 CapCut Package",
            width=135,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            command=self._export_capcut_package,
        )
        btn_capcut.pack(side="left", padx=4)

        open_folder_btn = ctk.CTkButton(
            right_actions,
            text="📁 Output Folder",
            width=115,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._open_output_folder,
        )
        open_folder_btn.pack(side="left", padx=4)

    # ------------------------------------------------------------------
    # Main 3-Pane Studio Workspace
    # ------------------------------------------------------------------

    def _build_main_workspace(self):
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=12, pady=(6, 4))

        # 1. Left Panel: Voice Library & Voice Blender
        self._build_left_voice_panel()

        # 2. Center Panel: Master Script Stage & Tabs
        self._build_center_stage()

        # 3. Right Panel: Audio Master Inspector & EQ
        self._build_right_inspector()

    # ------------------------------------------------------------------
    # LEFT PANEL: Voice Library & Custom Voice Blender
    # ------------------------------------------------------------------

    def _build_left_voice_panel(self):
        left_box = ctk.CTkFrame(self.workspace, width=320, corner_radius=12, fg_color=BG_PANEL, border_width=1, border_color=BORDER_COLOR)
        left_box.pack(side="left", fill="y", padx=(0, 6), pady=0)
        left_box.pack_propagate(False)

        # Header
        hdr = ctk.CTkFrame(left_box, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(hdr, text="🧬 Voice Browser & Blender", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        # Voice Blender Card
        blend_card = ctk.CTkFrame(left_box, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        blend_card.pack(fill="x", padx=10, pady=6)

        b_header = ctk.CTkFrame(blend_card, fg_color="transparent")
        b_header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(b_header, text="Custom Voice Blender", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN).pack(side="left")

        self.blend_switch = ctk.CTkSwitch(
            b_header,
            text="Blend",
            font=ctk.CTkFont(size=11),
            progress_color=ACCENT_CYAN,
            command=self._on_blend_switch_toggled,
        )
        self.blend_switch.pack(side="right")

        voice_keys = list(VOICE_CATALOG.keys())
        voice_names = [f"{VOICE_CATALOG[k]['flag']} {VOICE_CATALOG[k]['name']}" for k in voice_keys]

        # Primary Voice A
        ctk.CTkLabel(blend_card, text="Voice A (Base):", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 0))
        self.blend_v1_var = ctk.StringVar(value=voice_names[0])
        self.blend_v1_menu = ctk.CTkOptionMenu(blend_card, values=voice_names, variable=self.blend_v1_var, height=28, fg_color="#232a3b")
        self.blend_v1_menu.pack(fill="x", padx=10, pady=(2, 4))

        # Secondary Voice B
        ctk.CTkLabel(blend_card, text="Voice B (Blend):", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(2, 0))
        self.blend_v2_var = ctk.StringVar(value=voice_names[1])
        self.blend_v2_menu = ctk.CTkOptionMenu(blend_card, values=voice_names, variable=self.blend_v2_var, height=28, fg_color="#232a3b")
        self.blend_v2_menu.pack(fill="x", padx=10, pady=(2, 4))

        # Blend Ratio Slider
        ratio_frame = ctk.CTkFrame(blend_card, fg_color="transparent")
        ratio_frame.pack(fill="x", padx=10, pady=(4, 8))
        ctk.CTkLabel(ratio_frame, text="Mix Ratio:", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
        self.blend_ratio_label = ctk.CTkLabel(ratio_frame, text="50% A / 50% B", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_CYAN)
        self.blend_ratio_label.pack(side="right")

        self.blend_ratio_slider = ctk.CTkSlider(
            blend_card,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            progress_color=ACCENT_CYAN,
            command=self._on_blend_ratio_change,
        )
        self.blend_ratio_slider.set(0.5)
        self.blend_ratio_slider.pack(fill="x", padx=10, pady=(0, 6))

        btn_test_blend = ctk.CTkButton(
            blend_card,
            text="🔊 Test Blended Voice",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#242b3d",
            hover_color=BG_CARD_HOVER,
            command=self._test_blended_voice,
        )
        btn_test_blend.pack(fill="x", padx=10, pady=(0, 8))

        # Character Catalog List
        ctk.CTkLabel(left_box, text="Studio Voice Library (11 Voices)", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(
            anchor="w", padx=14, pady=(10, 4)
        )

        scroll_voices = ctk.CTkScrollableFrame(left_box, fg_color="transparent")
        scroll_voices.pack(fill="both", expand=True, padx=6, pady=4)

        for key, info in VOICE_CATALOG.items():
            card = ctk.CTkFrame(scroll_voices, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", padx=4, pady=3)

            col = ctk.CTkFrame(card, fg_color="transparent")
            col.pack(side="left", padx=8, pady=6)

            flag = info.get("flag", "🌐")
            ctk.CTkLabel(col, text=f"{flag} {info['name']} ({info['gender']})", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(col, text=info["description"][:28] + "...", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w")

            btn_play = ctk.CTkButton(
                card,
                text="🔊",
                width=32,
                height=26,
                font=ctk.CTkFont(size=11),
                fg_color="#242b3d",
                hover_color=BG_CARD_HOVER,
                command=lambda v=key: self._play_single_voice_sample(v),
            )
            btn_play.pack(side="right", padx=6, pady=6)

    def _on_blend_switch_toggled(self):
        self.use_blended_voice = self.blend_switch.get() == 1
        if self.use_blended_voice:
            self.set_status("Custom Voice Blender activated!", 1.0)
            self.single_voice_menu.configure(state="disabled")
        else:
            self.single_voice_menu.configure(state="normal")

    def _on_blend_ratio_change(self, val):
        pct_b = int(val * 100)
        pct_a = 100 - pct_b
        self.blend_ratio_label.configure(text=f"{pct_a}% A / {pct_b}% B")

    def _test_blended_voice(self):
        v1_name = self.blend_v1_var.get().split()[-1]
        v2_name = self.blend_v2_var.get().split()[-1]
        k1 = next((k for k, v in VOICE_CATALOG.items() if v["name"] == v1_name), "af_bella")
        k2 = next((k for k, v in VOICE_CATALOG.items() if v["name"] == v2_name), "af_nicole")
        ratio = self.blend_ratio_slider.get()

        def _worker():
            try:
                self.set_status(f"Generating blended sample ({v1_name} + {v2_name})...", 0.4)
                blended = self.engine.blend_voices(k1, k2, ratio)
                samples, sr = self.engine._kokoro.create(
                    f"Hello! I am a custom blended voice created from {v1_name} and {v2_name}.",
                    voice=blended,
                    lang="en-us",
                )
                seg = self.engine.numpy_to_audiosegment(samples, sr)
                self.player.play_segment(seg)
                self.set_status("Ready", 1.0)
            except Exception as e:
                self.set_status(f"Blender failed: {e}", 0.0)

        threading.Thread(target=_worker, daemon=True).start()

    def _play_single_voice_sample(self, voice_key: str):
        info = VOICE_CATALOG[voice_key]

        def _worker():
            try:
                self.set_status(f"Testing {info['name']}...", 0.4)
                samples, sr = self.engine.synthesize_text(
                    f"Hello, I am {info['name']}. This is my natural voice.",
                    voice=voice_key,
                    speed=1.0,
                )
                seg = self.engine.numpy_to_audiosegment(samples, sr)
                self.player.play_segment(seg)
                self.set_status("Ready", 1.0)
            except Exception as e:
                self.set_status(f"Sample failed: {e}", 0.0)

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------
    # CENTER STAGE: Script Studio & Multi-Speaker Tabs
    # ------------------------------------------------------------------

    def _build_center_stage(self):
        center_box = ctk.CTkFrame(self.workspace, corner_radius=12, fg_color=BG_PANEL, border_width=1, border_color=BORDER_COLOR)
        center_box.pack(side="left", fill="both", expand=True, padx=4, pady=0)

        self.tabview = ctk.CTkTabview(
            center_box,
            corner_radius=10,
            fg_color="transparent",
            segmented_button_selected_color=ACCENT_BLUE,
            segmented_button_selected_hover_color="#2563eb",
            segmented_button_unselected_color=BG_CARD,
            segmented_button_unselected_hover_color=BG_CARD_HOVER,
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=8)

        self.tab_single = self.tabview.add("  🎙️ Narrator Script  ")
        self.tab_multi = self.tabview.add("  🎭 Multi-Speaker Drama  ")
        self.tab_batch = self.tabview.add("  📂 Batch Queue  ")
        self.tab_history = self.tabview.add("  📜 Recent Audio Library  ")

        self._build_single_script_tab()
        self._build_multi_drama_tab()
        self._build_batch_queue_tab()
        self._build_history_library_tab()

    def _build_single_script_tab(self):
        tab = self.tab_single

        # SSML & Quick Insert Toolbar
        ssml_bar = ctk.CTkFrame(tab, fg_color="transparent", height=32)
        ssml_bar.pack(fill="x", padx=6, pady=(4, 4))

        ctk.CTkLabel(ssml_bar, text="Insert Tags:", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(4, 6))

        for pause_sec in ["0.5s", "1.0s", "2.0s"]:
            btn_p = ctk.CTkButton(
                ssml_bar,
                text=f"⏱️ +{pause_sec}",
                width=68,
                height=24,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=BG_CARD,
                hover_color=BG_CARD_HOVER,
                command=lambda p=pause_sec: self.single_text.insert("insert", f" [pause {p}] "),
            )
            btn_p.pack(side="left", padx=2)

        # Quick Actions Right
        btn_paste = ctk.CTkButton(
            ssml_bar,
            text="📋 Paste",
            width=65,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._paste_single_text,
        )
        btn_paste.pack(side="right", padx=2)

        btn_sample = ctk.CTkButton(
            ssml_bar,
            text="💡 Sample",
            width=65,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._load_sample_story,
        )
        btn_sample.pack(side="right", padx=2)

        btn_clear = ctk.CTkButton(
            ssml_bar,
            text="🗑️ Clear",
            width=60,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="#3a2222",
            hover_color="#5a2e2e",
            command=lambda: self.single_text.delete("1.0", "end"),
        )
        btn_clear.pack(side="right", padx=2)

        # Script Editor Box
        self.single_text = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Segoe UI", size=self.editor_font_size),
            wrap="word",
            corner_radius=10,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.single_text.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        self.single_text.insert(
            "1.0",
            "Welcome to Kokoro Voice Studio Pro. This is an ultra-premium offline text to speech workstation. [pause 0.5s] Experience zero cloud latency, custom hybrid voice blending, and studio-grade audio mastering presets.",
        )
        self.single_text.bind("<KeyRelease>", self._update_single_stats)

        # Analytics Bar
        self.stats_label = ctk.CTkLabel(
            tab,
            text="📊 32 Words | 231 Characters | Est. 0:13 Duration",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        )
        self.stats_label.pack(anchor="w", padx=10, pady=(0, 4))

    def _build_multi_drama_tab(self):
        tab = self.tab_multi

        top_bar = ctk.CTkFrame(tab, fg_color="transparent", height=32)
        top_bar.pack(fill="x", padx=6, pady=(4, 4))

        ctk.CTkLabel(top_bar, text="Format: [SpeakerName]: Line...", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(side="left")

        btn_tmpl1 = ctk.CTkButton(
            top_bar,
            text="🎭 Drama Scene",
            width=100,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._load_multi_template_drama,
        )
        btn_tmpl1.pack(side="right", padx=2)

        btn_tmpl2 = ctk.CTkButton(
            top_bar,
            text="🎙️ Podcast Show",
            width=110,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._load_multi_template_podcast,
        )
        btn_tmpl2.pack(side="right", padx=2)

        split_frame = ctk.CTkFrame(tab, fg_color="transparent")
        split_frame.pack(fill="both", expand=True, padx=6, pady=2)

        self.multi_text = ctk.CTkTextbox(
            split_frame,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            wrap="word",
            corner_radius=10,
            fg_color=BG_CARD,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.multi_text.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.multi_text.insert(
            "1.0",
            "[Adam]: Have you tried the new audio mastering presets in Kokoro Studio?\n"
            "[Bella]: Yes! The Warm Podcast EQ gives voices incredible broadcast depth.\n"
            "[George]: Indeed. And the custom voice blender lets you create completely unique characters.\n"
            "[Adam]: Let's generate and export our dialogue scene right away!",
        )

        right_container = ctk.CTkFrame(split_frame, width=280, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        right_container.pack(side="right", fill="both", expand=False)

        rp_header = ctk.CTkFrame(right_container, fg_color="transparent")
        rp_header.pack(fill="x", padx=8, pady=6)
        ctk.CTkLabel(rp_header, text="👥 Cast Members", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        detect_btn = ctk.CTkButton(
            rp_header,
            text="🔍 Refresh",
            width=70,
            height=22,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._detect_speakers,
        )
        detect_btn.pack(side="right")

        self.speaker_panel = ctk.CTkScrollableFrame(right_container, fg_color="transparent")
        self.speaker_panel.pack(fill="both", expand=True, padx=4, pady=4)

        self._detect_speakers()

    def _build_batch_queue_tab(self):
        tab = self.tab_batch
        card = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="both", expand=True, padx=6, pady=6)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(hdr, text="Batch File Processing Queue", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_add = ctk.CTkButton(
            hdr,
            text="➕ Add .txt Files",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._select_batch_files,
        )
        btn_add.pack(side="right", padx=4)

        self.batch_files_listbox = ctk.CTkTextbox(
            card,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.batch_files_listbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _build_history_library_tab(self):
        tab = self.tab_history
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=6)
        ctk.CTkLabel(hdr, text="Exported Audio Library", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        btn_refresh = ctk.CTkButton(
            hdr,
            text="🔄 Refresh",
            width=90,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._refresh_recent_history,
        )
        btn_refresh.pack(side="right")

        self.history_scroll = ctk.CTkScrollableFrame(tab, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.history_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    # ------------------------------------------------------------------
    # RIGHT PANEL: Audio Master Inspector & Acoustics
    # ------------------------------------------------------------------

    def _build_right_inspector(self):
        right_box = ctk.CTkFrame(self.workspace, width=310, corner_radius=12, fg_color=BG_PANEL, border_width=1, border_color=BORDER_COLOR)
        right_box.pack(side="right", fill="y", padx=(6, 0), pady=0)
        right_box.pack_propagate(False)

        hdr = ctk.CTkFrame(right_box, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(hdr, text="🎛️ Audio Master Inspector", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        # 1. Primary Narrator Voice Selection
        v_card = ctk.CTkFrame(right_box, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        v_card.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(v_card, text="Active Studio Voice:", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(8, 2))

        voice_options = [f"{info['flag']} {info['name']} ({info['gender']})" for key, info in VOICE_CATALOG.items()]
        self.single_voice_var = ctk.StringVar(value=voice_options[0])
        self.single_voice_menu = ctk.CTkOptionMenu(
            v_card,
            values=voice_options,
            variable=self.single_voice_var,
            height=32,
            fg_color="#242b3d",
            button_color=ACCENT_BLUE,
            button_hover_color="#2563eb",
        )
        self.single_voice_menu.pack(fill="x", padx=10, pady=(0, 10))

        # 2. Playback Speed & Cadence
        s_card = ctk.CTkFrame(right_box, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        s_card.pack(fill="x", padx=10, pady=6)

        s_head = ctk.CTkFrame(s_card, fg_color="transparent")
        s_head.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(s_head, text="Playback Speed:", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(side="left")
        self.single_speed_val_label = ctk.CTkLabel(s_head, text="1.00x", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN)
        self.single_speed_val_label.pack(side="right")

        self.single_speed_slider = ctk.CTkSlider(
            s_card,
            from_=0.5,
            to=2.0,
            number_of_steps=30,
            progress_color=ACCENT_BLUE,
            command=lambda v: self.single_speed_val_label.configure(text=f"{v:.2f}x"),
        )
        self.single_speed_slider.set(1.0)
        self.single_speed_slider.pack(fill="x", padx=10, pady=(2, 6))

        # Quick speed step buttons
        step_box = ctk.CTkFrame(s_card, fg_color="transparent")
        step_box.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(
            step_box,
            text="0.9x",
            width=45,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#232a3b",
            command=lambda: self._set_speed(0.9),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            step_box,
            text="1.0x",
            width=45,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#232a3b",
            command=lambda: self._set_speed(1.0),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            step_box,
            text="1.15x",
            width=50,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#232a3b",
            command=lambda: self._set_speed(1.15),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            step_box,
            text="1.25x",
            width=50,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#232a3b",
            command=lambda: self._set_speed(1.25),
        ).pack(side="left", padx=2)

        # 3. Studio Audio Master EQ Presets
        eq_card = ctk.CTkFrame(right_box, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        eq_card.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(eq_card, text="Studio Mastering EQ:", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(8, 2))

        self.master_eq_var = ctk.StringVar(value=MASTERING_PRESETS[0])
        self.master_eq_menu = ctk.CTkOptionMenu(
            eq_card,
            values=MASTERING_PRESETS,
            variable=self.master_eq_var,
            height=30,
            fg_color="#242b3d",
        )
        self.master_eq_menu.pack(fill="x", padx=10, pady=(0, 10))

        # 4. Big Render Action Button
        render_frame = ctk.CTkFrame(right_box, fg_color="transparent")
        render_frame.pack(fill="x", padx=10, pady=(12, 6))

        self.btn_render = ctk.CTkButton(
            render_frame,
            text="⚡ Render Studio Master",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            corner_radius=8,
            command=self._generate_active_speech,
        )
        self.btn_render.pack(fill="x", pady=4)

        btn_save_audio = ctk.CTkButton(
            render_frame,
            text="💾 Save Audio File...",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            corner_radius=8,
            command=self._save_single_audio_as,
        )
        btn_save_audio.pack(fill="x", pady=2)

        btn_export_srt = ctk.CTkButton(
            render_frame,
            text="📜 Export Subtitles (.SRT)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            corner_radius=8,
            command=self._export_single_srt,
        )
        btn_export_srt.pack(fill="x", pady=2)

    def _set_speed(self, val: float):
        self.single_speed_slider.set(val)
        self.single_speed_val_label.configure(text=f"{val:.2f}x")

    # ------------------------------------------------------------------
    # BOTTOM MASTER TRANSPORT DOCK WITH ANIMATED WAVEFORM
    # ------------------------------------------------------------------

    def _build_bottom_transport_dock(self):
        dock = ctk.CTkFrame(self, height=95, corner_radius=12, fg_color=BG_PANEL, border_width=1, border_color=BORDER_COLOR)
        dock.pack(fill="x", side="bottom", padx=12, pady=(2, 6))
        dock.pack_propagate(False)

        # 1. Left Transport Buttons
        t_left = ctk.CTkFrame(dock, fg_color="transparent")
        t_left.pack(side="left", padx=14, pady=12)

        btn_back = ctk.CTkButton(
            t_left,
            text="⏪ 5s",
            width=48,
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=lambda: self._seek_relative(-5.0),
        )
        btn_back.pack(side="left", padx=2)

        self.btn_play_pause = ctk.CTkButton(
            t_left,
            text="▶ Play",
            width=78,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT_BLUE,
            hover_color="#2563eb",
            command=self._toggle_playback,
        )
        self.btn_play_pause.pack(side="left", padx=4)

        self.btn_stop = ctk.CTkButton(
            t_left,
            text="⏹ Stop",
            width=65,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._stop_playback,
        )
        self.btn_stop.pack(side="left", padx=2)

        btn_fwd = ctk.CTkButton(
            t_left,
            text="5s ⏩",
            width=48,
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=lambda: self._seek_relative(5.0),
        )
        btn_fwd.pack(side="left", padx=2)

        self.btn_loop = ctk.CTkButton(
            t_left,
            text="🔁 Loop",
            width=60,
            height=36,
            font=ctk.CTkFont(size=11),
            fg_color=BG_CARD,
            hover_color=BG_CARD_HOVER,
            command=self._toggle_loop,
        )
        self.btn_loop.pack(side="left", padx=4)

        # 2. Center Live Waveform Visualizer & Track Timeline
        t_center = ctk.CTkFrame(dock, fg_color="transparent")
        t_center.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        meta_line = ctk.CTkFrame(t_center, fg_color="transparent")
        meta_line.pack(fill="x")

        self.track_label = ctk.CTkLabel(
            meta_line,
            text="🎵 No master audio loaded. Click 'Render Studio Master' to generate speech.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_LIGHT,
        )
        self.track_label.pack(side="left")

        self.time_label = ctk.CTkLabel(
            meta_line,
            text="00:00 / 00:00",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=ACCENT_CYAN,
        )
        self.time_label.pack(side="right")

        # Animated Audio Waveform Spectrum Canvas
        self.wave_canvas = Canvas(t_center, height=28, bg=BG_CARD, highlightthickness=0)
        self.wave_canvas.pack(fill="x", pady=(4, 2))

        # Progress Slider
        self.playback_slider = ctk.CTkProgressBar(t_center, height=6, progress_color=ACCENT_CYAN, fg_color="#10141d")
        self.playback_slider.set(0.0)
        self.playback_slider.pack(fill="x")

        # 3. Right Volume Control
        t_right = ctk.CTkFrame(dock, fg_color="transparent")
        t_right.pack(side="right", padx=16, pady=12)

        self.btn_mute = ctk.CTkButton(
            t_right,
            text="🔊",
            width=32,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            hover_color=BG_CARD_HOVER,
            command=self._toggle_mute,
        )
        self.btn_mute.pack(side="left", padx=(0, 2))

        self.vol_slider = ctk.CTkSlider(
            t_right,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            width=100,
            progress_color=ACCENT_BLUE,
            command=lambda v: self.player.set_volume(v),
        )
        self.vol_slider.set(1.0)
        self.vol_slider.pack(side="left")

    def _build_statusbar(self):
        status_frame = ctk.CTkFrame(self, height=24, corner_radius=0, fg_color="transparent")
        status_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 2))

        self.status_label = ctk.CTkLabel(status_frame, text="Ready", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.status_label.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=220, height=6, progress_color=ACCENT_BLUE)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right")

    def set_status(self, text: str, progress: float = 0.0):
        self.status_label.configure(text=text)
        self.progress_bar.set(progress)
        self.update_idletasks()

    # ------------------------------------------------------------------
    # Playback, Seeking & Animated Waveform Spectrum
    # ------------------------------------------------------------------

    def _poll_playback_and_waveform(self):
        is_playing = self.player.is_playing()

        # Update Timeline Scrubber
        if is_playing and self.current_duration_sec > 0:
            elapsed = time.time() - self.playback_start_time
            if elapsed > self.current_duration_sec:
                if self.player.is_looping:
                    self.playback_start_time = time.time()
                else:
                    self.player.stop()
                    self.btn_play_pause.configure(text="▶ Play")
                    self.playback_slider.set(0.0)
                    self.time_label.configure(text=f"00:00 / {self._format_sec(self.current_duration_sec)}")
            else:
                fraction = min(1.0, elapsed / self.current_duration_sec)
                self.playback_slider.set(fraction)
                self.time_label.configure(text=f"{self._format_sec(elapsed)} / {self._format_sec(self.current_duration_sec)}")
        elif not is_playing and not self.player.is_paused():
            self.btn_play_pause.configure(text="▶ Play")

        # Draw Animated Audio Spectrum Bars
        self._draw_waveform_bars(is_playing)

        self.after(50, self._poll_playback_and_waveform)

    def _draw_waveform_bars(self, is_playing: bool):
        self.wave_canvas.delete("all")
        width = self.wave_canvas.winfo_width()
        height = self.wave_canvas.winfo_height()
        if width <= 1:
            return

        num_bars = 52
        bar_width = width / num_bars
        t = time.time() * 8.0

        for i in range(num_bars):
            if is_playing:
                # Dynamic pulsing frequency simulation
                sine_val = (math.sin(t + i * 0.4) + 1.0) / 2.0
                bar_h = 4 + (height - 8) * sine_val * random.uniform(0.6, 1.0)
            else:
                bar_h = 3

            x0 = i * bar_width + 1
            x1 = (i + 1) * bar_width - 1
            y0 = (height - bar_h) / 2.0
            y1 = y0 + bar_h

            color = ACCENT_CYAN if is_playing else "#242c3d"
            self.wave_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

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

    def _seek_relative(self, delta_sec: float):
        if self.current_duration_sec <= 0:
            return
        curr_elapsed = time.time() - self.playback_start_time
        new_elapsed = max(0.0, min(self.current_duration_sec, curr_elapsed + delta_sec))
        self.playback_start_time = time.time() - new_elapsed
        fraction = new_elapsed / self.current_duration_sec
        self.playback_slider.set(fraction)
        self.time_label.configure(text=f"{self._format_sec(new_elapsed)} / {self._format_sec(self.current_duration_sec)}")

    def _toggle_loop(self):
        is_loop = self.player.toggle_loop()
        self.btn_loop.configure(fg_color=ACCENT_BLUE if is_loop else BG_CARD)

    def _toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.previous_volume = self.vol_slider.get()
            self.player.set_volume(0.0)
            self.btn_mute.configure(text="🔇")
        else:
            self.player.set_volume(self.previous_volume)
            self.btn_mute.configure(text="🔊")

    # ------------------------------------------------------------------
    # Project Save / Load (.kokoro) & CapCut Export
    # ------------------------------------------------------------------

    def _save_project_file(self):
        data = {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "single_script": self.single_text.get("1.0", "end"),
            "multi_script": self.multi_text.get("1.0", "end"),
            "active_voice": self.single_voice_var.get(),
            "speed": self.single_speed_slider.get(),
            "master_eq": self.master_eq_var.get(),
            "use_blended": self.use_blended_voice,
            "blend_v1": self.blend_v1_var.get(),
            "blend_v2": self.blend_v2_var.get(),
            "blend_ratio": self.blend_ratio_slider.get(),
        }

        save_path = filedialog.asksaveasfilename(
            title="Save Kokoro Studio Project",
            defaultextension=".kokoro",
            filetypes=[("Kokoro Project File", "*.kokoro"), ("JSON", "*.json")],
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Project Saved", f"Project saved successfully:\n{save_path}")

    def _load_project_file(self):
        file_path = filedialog.askopenfilename(
            title="Open Kokoro Studio Project",
            filetypes=[("Kokoro Project File", "*.kokoro"), ("JSON", "*.json")],
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "single_script" in data:
                self.single_text.delete("1.0", "end")
                self.single_text.insert("1.0", data["single_script"])
                self._update_single_stats()
            if "multi_script" in data:
                self.multi_text.delete("1.0", "end")
                self.multi_text.insert("1.0", data["multi_script"])
                self._detect_speakers()
            if "speed" in data:
                self._set_speed(float(data["speed"]))
            if "master_eq" in data:
                self.master_eq_var.set(data["master_eq"])

            messagebox.showinfo("Project Loaded", f"Successfully loaded project from:\n{file_path}")

    def _export_capcut_package(self):
        if self.current_audio_seg is None:
            messagebox.showwarning("No Audio", "Please render speech audio first before exporting CapCut package.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pkg_dir = self.output_dir / f"CapCut_Project_{timestamp}"
        pkg_dir.mkdir(parents=True, exist_ok=True)

        audio_path = pkg_dir / "voiceover.mp3"
        srt_path = pkg_dir / "subtitles.srt"

        self.engine.export_audio(self.current_audio_seg, audio_path, format="mp3", bitrate="320k")

        text = self.single_text.get("1.0", "end").strip()
        total_sec = len(self.current_audio_seg) / 1000.0
        segments = [{"start_sec": 0.0, "end_sec": total_sec, "text": text}]
        SubtitleGenerator.generate_srt(segments, srt_path)

        messagebox.showinfo("CapCut Package Exported", f"Successfully exported CapCut/Premiere package:\n\n📂 {pkg_dir}")
        self._open_output_folder()

    # ------------------------------------------------------------------
    # Master Synthesis & Multi-Speaker Execution
    # ------------------------------------------------------------------

    def _generate_active_speech(self):
        current_tab = self.tabview.get().strip()
        if "Drama" in current_tab:
            self._generate_multi_speech()
        elif "Batch" in current_tab:
            self._run_batch_conversion()
        else:
            self._generate_single_speech()

    def _generate_single_speech(self):
        if self.is_synthesizing:
            return

        text = self.single_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Input", "Please enter some text in the script editor.")
            return

        speed = self.single_speed_slider.get()
        eq_preset = self.master_eq_var.get()

        # Check if using custom blended voice
        if self.use_blended_voice:
            v1_name = self.blend_v1_var.get().split()[-1]
            v2_name = self.blend_v2_var.get().split()[-1]
            k1 = next((k for k, v in VOICE_CATALOG.items() if v["name"] == v1_name), "af_bella")
            k2 = next((k for k, v in VOICE_CATALOG.items() if v["name"] == v2_name), "af_nicole")
            ratio = self.blend_ratio_slider.get()
            voice_target = self.engine.blend_voices(k1, k2, ratio)
            voice_name_tag = f"blend_{k1}_{k2}"
        else:
            voice_display = self.single_voice_var.get()
            voice_target = self._get_selected_voice_key(voice_display)
            voice_name_tag = voice_target

        def _worker():
            self.is_synthesizing = True
            self.btn_render.configure(state="disabled", text="⏳ Mastering Audio...")
            try:
                self.set_status(f"Rendering {voice_name_tag} with EQ [{eq_preset}]...", 0.3)
                samples, sr = self.engine.synthesize_text(
                    text,
                    voice=voice_target,
                    speed=speed,
                    master_preset=eq_preset,
                )

                raw_seg = self.engine.numpy_to_audiosegment(samples, sr)
                self.current_audio_seg = self.engine.apply_studio_mastering(raw_seg, preset=eq_preset)
                self.current_duration_sec = len(self.current_audio_seg) / 1000.0

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"master_{voice_name_tag}_{timestamp}.mp3"
                save_path = self.output_dir / filename
                self.engine.export_audio(self.current_audio_seg, save_path, format="mp3", bitrate="320k")
                self.current_audio_path = save_path

                self.track_label.configure(text=f"🎵 {filename}  [{eq_preset}]")
                self.time_label.configure(text=f"00:00 / {self._format_sec(self.current_duration_sec)}")
                self.set_status("✓ Studio Master successfully rendered and saved!", 1.0)

                self.player.play_segment(self.current_audio_seg)
                self.playback_start_time = time.time()
                self.btn_play_pause.configure(text="⏸ Pause")

                self._refresh_recent_history()
            except Exception as e:
                messagebox.showerror("Synthesis Error", str(e))
                self.set_status(f"Error: {e}", 0.0)
            finally:
                self.is_synthesizing = False
                self.btn_render.configure(state="normal", text="⚡ Render Studio Master")

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
            messagebox.showwarning("Invalid Script", "No character turns detected.")
            return

        speaker_map = {}
        for speaker, var in self.multi_speaker_map.items():
            speaker_map[speaker] = self._get_selected_voice_key(var.get())

        eq_preset = self.master_eq_var.get()

        def _worker():
            self.is_synthesizing = True
            self.btn_render.configure(state="disabled", text="⏳ Mastering Drama...")
            try:
                self.current_audio_seg = self.engine.synthesize_dialogue(
                    dialogue_blocks=blocks,
                    speaker_voice_map=speaker_map,
                    pause_ms=350,
                    master_preset=eq_preset,
                    progress_callback=lambda f, msg: self.set_status(msg, f),
                )
                self.current_duration_sec = len(self.current_audio_seg) / 1000.0

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"drama_master_{timestamp}.mp3"
                save_path = self.output_dir / filename
                self.engine.export_audio(self.current_audio_seg, save_path, format="mp3", bitrate="320k")
                self.current_audio_path = save_path

                self.track_label.configure(text=f"🎭 {filename}  [{eq_preset}]")
                self.time_label.configure(text=f"00:00 / {self._format_sec(self.current_duration_sec)}")
                self.set_status("✓ Multi-Speaker Drama Master synthesized!", 1.0)

                self.player.play_segment(self.current_audio_seg)
                self.playback_start_time = time.time()
                self.btn_play_pause.configure(text="⏸ Pause")

                self._refresh_recent_history()
            except Exception as e:
                messagebox.showerror("Multi-Speaker Error", str(e))
                self.set_status(f"Error: {e}", 0.0)
            finally:
                self.is_synthesizing = False
                self.btn_render.configure(state="normal", text="⚡ Render Studio Master")

        threading.Thread(target=_worker, daemon=True).start()

    def _run_batch_conversion(self):
        file_paths = [p.strip() for p in self.batch_files_listbox.get("1.0", "end").splitlines() if p.strip()]
        if not file_paths:
            messagebox.showwarning("No Files", "Please select at least one .txt file.")
            return

        voice_key = self._get_selected_voice_key(self.single_voice_var.get())
        eq_preset = self.master_eq_var.get()

        def _worker():
            self.btn_render.configure(state="disabled", text="⏳ Processing Queue...")
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
                    raw_seg = self.engine.numpy_to_audiosegment(samples, sr)
                    mastered_seg = self.engine.apply_studio_mastering(raw_seg, preset=eq_preset)

                    out_name = f_path.stem + f"_{voice_key}_master.mp3"
                    out_path = self.output_dir / out_name
                    self.engine.export_audio(mastered_seg, out_path, format="mp3", bitrate="320k")
                except Exception as e:
                    print(f"Batch item failed: {e}")

            self.set_status(f"✓ Batch conversion complete ({total} files).", 1.0)
            self.btn_render.configure(state="normal", text="⚡ Render Studio Master")
            self._refresh_recent_history()
            messagebox.showinfo("Batch Complete", f"Successfully converted {total} files into:\n{self.output_dir}")

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

        voice_options = [f"{info['flag']} {info['name']}" for key, info in VOICE_CATALOG.items()]
        defaults = ["am_adam", "af_bella", "bm_george", "af_nicole", "af_sky", "am_michael"]
        palette = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4"]

        self.multi_speaker_map = {}
        for idx, speaker in enumerate(speakers):
            color = palette[idx % len(palette)]
            card = ctk.CTkFrame(self.speaker_panel, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", padx=2, pady=4)

            badge = ctk.CTkLabel(
                card,
                text=f"  {speaker}  ",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=color,
                text_color="#ffffff",
                corner_radius=6,
            )
            badge.pack(anchor="w", padx=6, pady=(6, 2))

            def_key = defaults[idx % len(defaults)]
            def_name = VOICE_CATALOG.get(def_key, {}).get("name", "Bella")
            def_opt = next((o for o in voice_options if def_name in o), voice_options[0])

            var = ctk.StringVar(value=def_opt)
            menu = ctk.CTkOptionMenu(card, values=voice_options, variable=var, height=26, font=ctk.CTkFont(size=11), fg_color="#242b3d")
            menu.pack(fill="x", padx=6, pady=(2, 6))

            self.multi_speaker_map[speaker] = var

    def _get_selected_voice_key(self, display_label: str) -> str:
        for key, info in VOICE_CATALOG.items():
            if info["name"] in display_label or display_label.startswith(key):
                return key
        return "af_bella"

    def _update_single_stats(self, event=None):
        text = self.single_text.get("1.0", "end").strip()
        words = len(text.split()) if text else 0
        chars = len(text)
        est_sec = int((words / 150) * 60)
        mins = est_sec // 60
        secs = est_sec % 60
        self.stats_label.configure(text=f"📊 {words} Words | {chars} Characters | Est. {mins}:{secs:02d} Duration")

    def _paste_single_text(self):
        try:
            clipboard = self.clipboard_get()
            self.single_text.insert("insert", clipboard)
            self._update_single_stats()
        except Exception:
            pass

    def _load_sample_story(self):
        sample = (
            "I never expected a routine morning walk to turn into something extraordinary. [pause 0.5s] "
            "As the golden sunrise broke through the mist, an old bookstore that had been locked for years suddenly opened its wooden doors. "
            "[pause 0.8s] Inside, hundreds of forgotten manuscripts rested on velvet shelves, whispering stories of an ancient era."
        )
        self.single_text.delete("1.0", "end")
        self.single_text.insert("1.0", sample)
        self._update_single_stats()

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

    def _select_batch_files(self):
        files = filedialog.askopenfilenames(
            title="Select Text Files for TTS",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if files:
            for f in files:
                self.batch_files_listbox.insert("end", f + "\n")

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
                text="No generated audio files found.\nRender speech above to build your audio master library!",
                font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED,
            )
            empty_lbl.pack(pady=30)
            return

        for f in audio_files[:30]:
            card = ctk.CTkFrame(self.history_scroll, fg_color=BG_PANEL, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", padx=4, pady=3)

            size_mb = f.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M")

            info_col = ctk.CTkFrame(card, fg_color="transparent")
            info_col.pack(side="left", padx=10, pady=6)

            ctk.CTkLabel(info_col, text=f"🎵 {f.name[:32]}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_col, text=f"{mtime} • {size_mb:.2f} MB", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w")

            btn_play = ctk.CTkButton(
                card,
                text="▶ Play",
                width=65,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=ACCENT_BLUE,
                hover_color="#2563eb",
                command=lambda path=f: self._play_history_file(path),
            )
            btn_play.pack(side="right", padx=8, pady=6)

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

    def _save_single_audio_as(self):
        if self.current_audio_seg is None:
            messagebox.showwarning("No Audio", "Please render speech first before saving.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Master Audio File",
            initialdir=str(self.output_dir),
            defaultextension=".mp3",
            filetypes=[("MP3 Master (320kbps)", "*.mp3"), ("WAV Audio", "*.wav"), ("OGG Audio", "*.ogg")],
        )
        if save_path:
            fmt = Path(save_path).suffix.replace(".", "") or "mp3"
            self.engine.export_audio(self.current_audio_seg, Path(save_path), format=fmt, bitrate="320k")
            messagebox.showinfo("File Saved", f"Audio exported successfully to:\n{save_path}")

    def _export_single_srt(self):
        if self.current_audio_seg is None:
            messagebox.showwarning("No Audio", "Please render speech first before exporting subtitles.")
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
