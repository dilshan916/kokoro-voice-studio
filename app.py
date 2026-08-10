"""
Kokoro Voice Studio — Modern Desktop AI Text-to-Speech Application
==================================================================
Studio-grade, 100% offline TTS powered by Kokoro-82M ONNX.
"""

from __future__ import annotations

import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image
from pydub import AudioSegment

from core.audio_player import AudioPlayer
from core.kokoro_engine import VOICE_CATALOG, KokoroStudioEngine
from core.srt_generator import SubtitleGenerator

# Setup theme & styling
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class KokoroStudioApp(ctk.CTk):
    """Main Desktop Application Window for Kokoro Studio."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("🎙️ Kokoro Voice Studio — Offline AI Text-to-Speech")
        self.geometry("1180x820")
        self.minsize(1050, 720)

        # Core components
        self.base_dir = Path(__file__).resolve().parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.engine = KokoroStudioEngine()
        self.player = AudioPlayer()

        # State variables
        self.current_audio_seg: AudioSegment | None = None
        self.current_audio_path: Path | None = None
        self.is_synthesizing = False
        self.multi_speaker_map = {}

        # Build UI layout
        self._build_header()
        self._build_tabview()
        self._build_player_dock()
        self._build_statusbar()

        # Warm up engine in background thread
        threading.Thread(target=self._warmup_engine, daemon=True).start()

    def _warmup_engine(self):
        try:
            self.set_status("Loading Kokoro-82M ONNX model weights...", 0.3)
            self.engine.load_model()
            self.set_status("Ready — Kokoro-82M Model Active (CPU Engine)", 1.0)
        except Exception as e:
            self.set_status(f"Error loading model: {e}", 0.0)

    # ------------------------------------------------------------------
    # UI Building Blocks
    # ------------------------------------------------------------------

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color=("#1f232a", "#15181e"))
        header_frame.pack(fill="x", side="top", padx=0, pady=0)

        title_label = ctk.CTkLabel(
            header_frame,
            text="🎙️ KOKORO VOICE STUDIO",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#3b8ed0", "#60cdff"),
        )
        title_label.pack(side="left", padx=25, pady=15)

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Studio-Grade 82M Offline Text-to-Speech",
            font=ctk.CTkFont(size=13, weight="normal"),
            text_color="#8a99a8",
        )
        subtitle_label.pack(side="left", padx=5, pady=18)

        # Quick Open Folder Button
        open_folder_btn = ctk.CTkButton(
            header_frame,
            text="📂 Open Output Folder",
            width=160,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2b303c",
            hover_color="#3c4354",
            command=self._open_output_folder,
        )
        open_folder_btn.pack(side="right", padx=25, pady=15)

    def _build_tabview(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(10, 5))

        # Create tabs
        self.tab_single = self.tabview.add("  🎙️ Single Narrator  ")
        self.tab_multi = self.tabview.add("  🎭 Multi-Speaker Drama  ")
        self.tab_batch = self.tabview.add("  📂 Batch File Converter  ")
        self.tab_settings = self.tabview.add("  ⚙️ Settings & Info  ")

        self._build_single_tab()
        self._build_multi_tab()
        self._build_batch_tab()
        self._build_settings_tab()

    # ------------------------------------------------------------------
    # TAB 1: Single Narrator Studio
    # ------------------------------------------------------------------

    def _build_single_tab(self):
        tab = self.tab_single

        # Left/Top: Text Input
        input_label = ctk.CTkLabel(tab, text="Script / Text Content:", font=ctk.CTkFont(size=14, weight="bold"))
        input_label.pack(anchor="w", padx=15, pady=(5, 5))

        self.single_text = ctk.CTkTextbox(tab, height=220, font=ctk.CTkFont(size=14), wrap="word")
        self.single_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.single_text.insert(
            "1.0",
            "Welcome to Kokoro Voice Studio! This is a state of the art, offline text to speech engine running entirely on your computer with zero cloud latency. Enjoy natural, studio-quality narration for your videos, audiobooks, and podcasts.",
        )

        # Controls Container
        controls_frame = ctk.CTkFrame(tab, fg_color=("#232730", "#1c2027"), corner_radius=10)
        controls_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Voice Selector
        v_label = ctk.CTkLabel(controls_frame, text="Select Voice:", font=ctk.CTkFont(size=13, weight="bold"))
        v_label.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        voice_options = [label for _, label in self.engine.get_available_voices()]
        self.single_voice_var = ctk.StringVar(value=voice_options[0])
        self.single_voice_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=voice_options,
            variable=self.single_voice_var,
            width=360,
            height=34,
        )
        self.single_voice_menu.grid(row=0, column=1, padx=10, pady=12, sticky="w")

        # Speed Slider
        s_label = ctk.CTkLabel(controls_frame, text="Speed Rate:", font=ctk.CTkFont(size=13, weight="bold"))
        s_label.grid(row=0, column=2, padx=(20, 10), pady=12, sticky="w")

        self.single_speed_val_label = ctk.CTkLabel(controls_frame, text="1.00x", font=ctk.CTkFont(size=13, weight="bold"), text_color="#60cdff")
        self.single_speed_val_label.grid(row=0, column=4, padx=(5, 15), pady=12, sticky="w")

        self.single_speed_slider = ctk.CTkSlider(
            controls_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=30,
            width=160,
            command=self._on_single_speed_change,
        )
        self.single_speed_slider.set(1.0)
        self.single_speed_slider.grid(row=0, column=3, padx=5, pady=12, sticky="w")

        # Action Buttons Row
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.pack(fill="x", padx=15, pady=5)

        self.btn_single_generate = ctk.CTkButton(
            action_frame,
            text="⚡ Generate Speech",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#1f6aa5",
            hover_color="#144d75",
            command=self._generate_single_speech,
        )
        self.btn_single_generate.pack(side="left", padx=(0, 10), expand=True, fill="x")

        self.btn_single_save = ctk.CTkButton(
            action_frame,
            text="💾 Save Audio As...",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#2b303c",
            hover_color="#3c4354",
            command=self._save_single_audio_as,
        )
        self.btn_single_save.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_single_srt = ctk.CTkButton(
            action_frame,
            text="📜 Export Subtitles (.SRT)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#2b303c",
            hover_color="#3c4354",
            command=self._export_single_srt,
        )
        self.btn_single_srt.pack(side="left", padx=(10, 0), expand=True, fill="x")

    def _on_single_speed_change(self, val):
        self.single_speed_val_label.configure(text=f"{val:.2f}x")

    def _get_selected_voice_key(self, display_label: str) -> str:
        for key, info in VOICE_CATALOG.items():
            if display_label.startswith(info["name"]):
                return key
        return "af_bella"

    # ------------------------------------------------------------------
    # TAB 2: Multi-Speaker Drama Studio
    # ------------------------------------------------------------------

    def _build_multi_tab(self):
        tab = self.tab_multi

        # Explanation
        info_label = ctk.CTkLabel(
            tab,
            text="Format: [SpeakerName]: Dialogue text... (e.g. [Adam]: Hello! \n [Bella]: Hi Adam!)",
            font=ctk.CTkFont(size=13),
            text_color="#8a99a8",
        )
        info_label.pack(anchor="w", padx=15, pady=(5, 5))

        # Main horizontal split
        split_frame = ctk.CTkFrame(tab, fg_color="transparent")
        split_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Left: Script Textbox
        self.multi_text = ctk.CTkTextbox(split_frame, font=ctk.CTkFont(size=14), wrap="word")
        self.multi_text.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.multi_text.insert(
            "1.0",
            "[Adam]: Have you seen the latest project update?\n"
            "[Bella]: Yes! The voice generation speed is incredible on CPU.\n"
            "[George]: Indeed. It sounds remarkably natural and expressive.\n"
            "[Adam]: Let's export the full conversation right now!",
        )

        # Right: Speaker Voice Mapping Panel
        self.speaker_panel = ctk.CTkScrollableFrame(split_frame, width=380, label_text="🎭 Character Voice Assignments")
        self.speaker_panel.pack(side="right", fill="both", expand=False)

        # Detect Speakers Button
        detect_btn = ctk.CTkButton(
            self.speaker_panel,
            text="🔍 Auto-Detect Characters",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._detect_speakers,
        )
        detect_btn.pack(fill="x", padx=5, pady=8)

        self.speaker_widgets_container = ctk.CTkFrame(self.speaker_panel, fg_color="transparent")
        self.speaker_widgets_container.pack(fill="both", expand=True)

        # Multi Options Row
        multi_opt_frame = ctk.CTkFrame(tab, fg_color=("#232730", "#1c2027"), corner_radius=10)
        multi_opt_frame.pack(fill="x", padx=15, pady=(5, 10))

        p_label = ctk.CTkLabel(multi_opt_frame, text="Pause Between Speakers:", font=ctk.CTkFont(size=13, weight="bold"))
        p_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.multi_pause_val_label = ctk.CTkLabel(multi_opt_frame, text="400 ms", font=ctk.CTkFont(size=13, weight="bold"), text_color="#60cdff")
        self.multi_pause_val_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.multi_pause_slider = ctk.CTkSlider(
            multi_opt_frame,
            from_=100,
            to=1500,
            number_of_steps=28,
            width=200,
            command=lambda v: self.multi_pause_val_label.configure(text=f"{int(v)} ms"),
        )
        self.multi_pause_slider.set(400)
        self.multi_pause_slider.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        # Multi Action Buttons
        m_action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        m_action_frame.pack(fill="x", padx=15, pady=5)

        self.btn_multi_generate = ctk.CTkButton(
            m_action_frame,
            text="🎭 Generate Multi-Speaker Drama",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#1f6aa5",
            hover_color="#144d75",
            command=self._generate_multi_speech,
        )
        self.btn_multi_generate.pack(side="left", padx=(0, 10), expand=True, fill="x")

        self.btn_multi_save = ctk.CTkButton(
            m_action_frame,
            text="💾 Save Combined Audio...",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#2b303c",
            hover_color="#3c4354",
            command=self._save_single_audio_as,
        )
        self.btn_multi_save.pack(side="left", padx=5, expand=True, fill="x")

        self._detect_speakers()

    def _detect_speakers(self):
        """Parse character names from the dialogue text area."""
        for child in self.speaker_widgets_container.winfo_children():
            child.destroy()

        text = self.multi_text.get("1.0", "end")
        speakers = sorted(list(set(re.findall(r"\[([a-zA-Z0-9_\s]+)\]\s*:", text))))

        if not speakers:
            speakers = ["Narrator"]

        voice_options = [label for _, label in self.engine.get_available_voices()]
        defaults = ["am_adam", "af_bella", "bm_george", "af_nicole", "af_sky", "am_michael"]

        self.multi_speaker_map = {}
        for idx, speaker in enumerate(speakers):
            row_frame = ctk.CTkFrame(self.speaker_widgets_container, fg_color=("#282d37", "#22262f"), corner_radius=6)
            row_frame.pack(fill="x", padx=2, pady=4)

            name_lbl = ctk.CTkLabel(row_frame, text=f"👤 {speaker}:", font=ctk.CTkFont(size=12, weight="bold"))
            name_lbl.pack(side="top", anchor="w", padx=8, pady=(4, 2))

            default_voice_key = defaults[idx % len(defaults)]
            default_label = next(
                (lbl for key, lbl in self.engine.get_available_voices() if key == default_voice_key),
                voice_options[0],
            )

            var = ctk.StringVar(value=default_label)
            menu = ctk.CTkOptionMenu(row_frame, values=voice_options, variable=var, height=28, font=ctk.CTkFont(size=11))
            menu.pack(side="top", fill="x", padx=8, pady=(0, 6))

            self.multi_speaker_map[speaker] = var

    # ------------------------------------------------------------------
    # TAB 3: Batch File Converter
    # ------------------------------------------------------------------

    def _build_batch_tab(self):
        tab = self.tab_batch

        b_label = ctk.CTkLabel(
            tab,
            text="Convert multiple text files (.txt) into individual audio files:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        b_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.batch_files_listbox = ctk.CTkTextbox(tab, height=220, font=ctk.CTkFont(size=13))
        self.batch_files_listbox.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=5)

        add_files_btn = ctk.CTkButton(
            btn_row,
            text="➕ Select .txt Files...",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            command=self._select_batch_files,
        )
        add_files_btn.pack(side="left", padx=(0, 10))

        clear_files_btn = ctk.CTkButton(
            btn_row,
            text="🗑️ Clear List",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#3a2525",
            hover_color="#5a3535",
            command=lambda: self.batch_files_listbox.delete("1.0", "end"),
        )
        clear_files_btn.pack(side="left", padx=5)

        self.btn_start_batch = ctk.CTkButton(
            btn_row,
            text="🚀 Start Batch Conversion",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#1f6aa5",
            hover_color="#144d75",
            command=self._run_batch_conversion,
        )
        self.btn_start_batch.pack(side="right", padx=(10, 0))

    def _select_batch_files(self):
        files = filedialog.askopenfilenames(
            title="Select Text Files",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if files:
            for f in files:
                self.batch_files_listbox.insert("end", f + "\n")

    # ------------------------------------------------------------------
    # TAB 4: Settings & Info
    # ------------------------------------------------------------------

    def _build_settings_tab(self):
        tab = self.tab_settings

        card = ctk.CTkFrame(tab, fg_color=("#232730", "#1c2027"), corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=15)

        s_title = ctk.CTkLabel(card, text="⚙️ Application Configuration & System Info", font=ctk.CTkFont(size=16, weight="bold"))
        s_title.pack(anchor="w", padx=20, pady=(20, 15))

        # Model Info
        model_info_text = (
            f"• Model Name: Kokoro-82M ONNX (v0.19)\n"
            f"• Model Path: {self.engine.model_path}\n"
            f"• Voices File: {self.engine.voices_path}\n"
            f"• Output Directory: {self.output_dir}\n"
            f"• Audio Sample Rate: 24,000 Hz (Studio Grade)\n"
            f"• Hardware Mode: CPU Execution Provider (Zero GPU Required)"
        )
        info_lbl = ctk.CTkLabel(card, text=model_info_text, justify="left", font=ctk.CTkFont(size=13), text_color="#a1b0cb")
        info_lbl.pack(anchor="w", padx=20, pady=10)

        # Output folder changer
        btn_change_output = ctk.CTkButton(
            card,
            text="Change Output Directory...",
            width=220,
            height=34,
            command=self._change_output_directory,
        )
        btn_change_output.pack(anchor="w", padx=20, pady=15)

    def _change_output_directory(self):
        new_dir = filedialog.askdirectory(title="Select Output Directory", initialdir=str(self.output_dir))
        if new_dir:
            self.output_dir = Path(new_dir)
            messagebox.showinfo("Output Directory Updated", f"Audio will now be saved to:\n{self.output_dir}")

    # ------------------------------------------------------------------
    # Bottom In-App Audio Player Dock
    # ------------------------------------------------------------------

    def _build_player_dock(self):
        player_frame = ctk.CTkFrame(self, height=75, corner_radius=10, fg_color=("#181b22", "#13161c"))
        player_frame.pack(fill="x", side="bottom", padx=20, pady=(5, 10))

        # Play / Pause Toggle Button
        self.btn_play_pause = ctk.CTkButton(
            player_frame,
            text="▶ Play",
            width=90,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144d75",
            command=self._toggle_playback,
        )
        self.btn_play_pause.pack(side="left", padx=(15, 8), pady=18)

        # Stop Button
        self.btn_stop = ctk.CTkButton(
            player_frame,
            text="⏹ Stop",
            width=80,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2b303c",
            hover_color="#3c4354",
            command=self._stop_playback,
        )
        self.btn_stop.pack(side="left", padx=5, pady=18)

        # Audio Track Label
        self.track_label = ctk.CTkLabel(
            player_frame,
            text="No audio loaded. Generate or open a track.",
            font=ctk.CTkFont(size=13),
            text_color="#8a99a8",
        )
        self.track_label.pack(side="left", padx=20, pady=18)

        # Volume Slider
        vol_label = ctk.CTkLabel(player_frame, text="🔊 Volume:", font=ctk.CTkFont(size=12))
        vol_label.pack(side="right", padx=(10, 5), pady=18)

        self.vol_slider = ctk.CTkSlider(
            player_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            width=120,
            command=lambda v: self.player.set_volume(v),
        )
        self.vol_slider.set(1.0)
        self.vol_slider.pack(side="right", padx=(5, 20), pady=18)

    def _build_statusbar(self):
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="transparent")
        status_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 2))

        self.status_label = ctk.CTkLabel(status_frame, text="Ready", font=ctk.CTkFont(size=12), text_color="#8a99a8")
        self.status_label.pack(side="left", padx=5)

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=250, height=10)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", padx=5)

    def set_status(self, text: str, progress: float = 0.0):
        self.status_label.configure(text=text)
        self.progress_bar.set(progress)
        self.update_idletasks()

    # ------------------------------------------------------------------
    # Generation & Playback Handlers
    # ------------------------------------------------------------------

    def _generate_single_speech(self):
        if self.is_synthesizing:
            return

        text = self.single_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Text", "Please enter some text to synthesize.")
            return

        voice_display = self.single_voice_var.get()
        voice_key = self._get_selected_voice_key(voice_display)
        speed = self.single_speed_slider.get()

        def _worker():
            self.is_synthesizing = True
            self.btn_single_generate.configure(state="disabled", text="⏳ Synthesizing...")
            try:
                self.set_status(f"Synthesizing with {voice_key}...", 0.3)
                samples, sr = self.engine.synthesize_text(text, voice=voice_key, speed=speed)
                self.current_audio_seg = self.engine.numpy_to_audiosegment(samples, sr)

                # Save temporary preview file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tts_{voice_key}_{timestamp}.mp3"
                save_path = self.output_dir / filename
                self.engine.export_audio(self.current_audio_seg, save_path, format="mp3")
                self.current_audio_path = save_path

                # Update UI
                self.track_label.configure(text=f"🎵 {filename} ({len(self.current_audio_seg)/1000:.1f}s)")
                self.set_status("✓ Synthesis complete! Playing preview...", 1.0)

                # Play preview automatically
                self.player.play_segment(self.current_audio_seg)
                self.btn_play_pause.configure(text="⏸ Pause")
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
            messagebox.showwarning("Empty Dialogue", "Please enter a dialogue script.")
            return

        # Parse dialogue turns
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
            messagebox.showwarning("Invalid Format", "No dialogue turns detected. Use [SpeakerName]: format.")
            return

        # Build speaker-to-voice map
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

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"multi_drama_{timestamp}.mp3"
                save_path = self.output_dir / filename
                self.engine.export_audio(self.current_audio_seg, save_path, format="mp3")
                self.current_audio_path = save_path

                # Update UI
                self.track_label.configure(text=f"🎭 {filename} ({len(self.current_audio_seg)/1000:.1f}s)")
                self.set_status("✓ Drama synthesis complete! Playing audio...", 1.0)

                # Play audio
                self.player.play_segment(self.current_audio_seg)
                self.btn_play_pause.configure(text="⏸ Pause")
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

        def _worker():
            self.btn_start_batch.configure(state="disabled", text="⏳ Processing Batch...")
            total = len(file_paths)
            for idx, f_path_str in enumerate(file_paths):
                f_path = Path(f_path_str)
                if not f_path.exists():
                    continue
                try:
                    with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    self.set_status(f"Converting ({idx + 1}/{total}): {f_path.name}...", idx / total)
                    samples, sr = self.engine.synthesize_text(content, voice="am_adam")
                    seg = self.engine.numpy_to_audiosegment(samples, sr)

                    out_name = f_path.stem + ".mp3"
                    out_path = self.output_dir / out_name
                    self.engine.export_audio(seg, out_path, format="mp3")
                except Exception as e:
                    print(f"Batch item failed: {e}")

            self.set_status(f"✓ Batch complete! {total} files converted.", 1.0)
            self.btn_start_batch.configure(state="normal", text="🚀 Start Batch Conversion")
            messagebox.showinfo("Batch Complete", f"Successfully converted {total} files into {self.output_dir}")

        threading.Thread(target=_worker, daemon=True).start()

    def _save_single_audio_as(self):
        if self.current_audio_seg is None:
            messagebox.showwarning("No Audio", "Please generate speech first before saving.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Audio File",
            initialdir=str(self.output_dir),
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3"), ("WAV Audio", "*.wav"), ("OGG Audio", "*.ogg")],
        )
        if save_path:
            fmt = Path(save_path).suffix.replace(".", "") or "mp3"
            self.engine.export_audio(self.current_audio_seg, Path(save_path), format=fmt)
            messagebox.showinfo("File Saved", f"Audio saved successfully to:\n{save_path}")

    def _export_single_srt(self):
        if self.current_audio_seg is None:
            messagebox.showwarning("No Audio", "Please generate speech first before exporting subtitles.")
            return

        text = self.single_text.get("1.0", "end").strip()
        save_path = filedialog.asksaveasfilename(
            title="Export Subtitle File",
            initialdir=str(self.output_dir),
            defaultextension=".srt",
            filetypes=[("SubRip Subtitle", "*.srt"), ("All files", "*.*")],
        )
        if save_path:
            total_sec = len(self.current_audio_seg) / 1000.0
            segments = [{"start_sec": 0.0, "end_sec": total_sec, "text": text}]
            SubtitleGenerator.generate_srt(segments, Path(save_path))
            messagebox.showinfo("Subtitles Exported", f"Subtitles exported successfully to:\n{save_path}")

    def _toggle_playback(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play_pause.configure(text="▶ Play")
        elif self.player.is_paused():
            self.player.unpause()
            self.btn_play_pause.configure(text="⏸ Pause")
        elif self.current_audio_seg is not None:
            self.player.play_segment(self.current_audio_seg)
            self.btn_play_pause.configure(text="⏸ Pause")

    def _stop_playback(self):
        self.player.stop()
        self.btn_play_pause.configure(text="▶ Play")

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
