import React, { useState } from 'react';
import { SlidersHorizontal, ExternalLink, Info, X, Heart, Cpu, Code2, Sparkles, User } from 'lucide-react';
import { HealthData } from '../types';

interface NavbarProps {
  health: HealthData | null;
  isLoading: boolean;
  onRefreshHealth: () => void;
  onToggleInspector: () => void;
  isInspectorOpen: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  isLoading,
  onRefreshHealth,
  onToggleInspector,
  isInspectorOpen,
}) => {
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const isOnline = health?.status === 'ready';
  const isModelLoading = health?.status === 'loading';

  return (
    <>
      <header className="h-16 bg-studio-bg/80 backdrop-blur-md border-b border-white/[0.06] px-6 flex items-center justify-between shrink-0 select-none z-30">
        {/* Brand & Studio Title + Info Button */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg tracking-tight text-white font-sans">
              Kokoro <span className="font-light text-gray-400">Studio</span>
            </span>
          </div>

          {/* Info & Credits Button */}
          <button
            onClick={() => setShowCreditsModal(true)}
            className="w-7 h-7 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-gray-400 hover:text-white flex items-center justify-center transition-all border border-white/[0.06] hover:border-white/[0.15]"
            title="About Kokoro Studio & Credits"
          >
            <Info className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Right Actions: Live Engine Status & Settings */}
        <div className="flex items-center space-x-3">
          {/* Minimalist Engine Status Indicator */}
          <button
            onClick={onRefreshHealth}
            title="Engine Status (click to refresh)"
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
              isOnline
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : isModelLoading
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/20 animate-pulse'
                : 'bg-rose-500/10 text-rose-300 border-rose-500/20'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isOnline
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  : isModelLoading
                  ? 'bg-amber-400'
                  : 'bg-rose-400'
              }`}
            />
            <span>
              {isLoading
                ? 'Checking...'
                : isOnline
                ? 'Ready'
                : isModelLoading
                ? 'Loading Model...'
                : 'Offline'}
            </span>
          </button>

          {/* Audio Fine-Tuning / Master Settings Toggle Button */}
          <button
            onClick={onToggleInspector}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
              isInspectorOpen
                ? 'bg-brand-primary text-white border-brand-primary shadow-glow-primary'
                : 'bg-studio-surface/80 hover:bg-studio-card text-gray-300 hover:text-white border-white/[0.08]'
            }`}
            title="Audio Settings & Acoustic Mastering EQ"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Audio Settings</span>
          </button>

          {/* API Docs Link */}
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="p-2 rounded-xl text-studio-muted hover:text-white hover:bg-studio-surface/80 border border-transparent hover:border-white/[0.06] transition-all"
            title="FastAPI Swagger Documentation"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </header>

      {/* Credits & About Modal */}
      {showCreditsModal && (
        <div
          className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-in fade-in duration-150"
          onClick={() => setShowCreditsModal(false)}
        >
          <div
            className="w-full max-w-lg bg-studio-surface border border-white/[0.12] rounded-3xl p-6 shadow-2xl space-y-5 select-none"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  Kokoro Voice Studio
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-primary/20 text-brand-primary font-mono">
                    v2.5.0 PRO
                  </span>
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Ultra-Fast Neural Speech Synthesis & Audio Workstation
                </p>
              </div>

              <button
                onClick={() => setShowCreditsModal(false)}
                className="p-1.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/[0.06] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Credits List */}
            <div className="space-y-3.5 text-xs text-gray-300">
              {/* Lead Developer */}
              <a
                href="https://github.com/dilshan916/"
                target="_blank"
                rel="noopener noreferrer"
                className="p-3.5 rounded-2xl bg-brand-primary/[0.06] hover:bg-brand-primary/[0.12] border border-brand-primary/20 hover:border-brand-primary/40 flex items-center justify-between transition-all group cursor-pointer shadow-sm hover:shadow-glow-primary"
                title="Visit Dilshan Chandrarathne on GitHub"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-brand-primary/20 text-brand-primary group-hover:scale-105 transition-transform flex items-center justify-center shrink-0">
                    <User className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-[11px] text-brand-primary uppercase tracking-wider font-bold">
                      Lead Developer & Architect
                    </div>
                    <div className="text-sm font-semibold text-white mt-0.5 group-hover:text-brand-primary transition-colors flex items-center gap-1.5">
                      <span>Dilshan Chandrarathne</span>
                      <span className="text-[10px] text-gray-400 font-mono font-normal">@dilshan916</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-white/[0.06] group-hover:bg-white/[0.1] text-gray-400 group-hover:text-white transition-all text-[11px]">
                  <span>GitHub</span>
                  <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </a>

              {/* Core TTS Model */}
              <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-brand-accent" /> Kokoro-82M ONNX
                  </span>
                  <span className="text-[10px] font-mono text-gray-400">@hexgrad</span>
                </div>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Open-weights state-of-the-art 82M parameter neural speech model with 60 studio voices across 9+ languages.
                </p>
              </div>

              {/* G2P & Phonemizers */}
              <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Code2 className="w-3.5 h-3.5 text-brand-secondary" /> Multilingual G2P Engines
                  </span>
                  <span className="text-[10px] font-mono text-gray-400">Open Source</span>
                </div>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Misaki (Japanese/English G2P), PyOpenJTalk, Janome Morphological POS Analyzer, and eSpeak-NG.
                </p>
              </div>

              {/* CapCut Subtitles & Audio Player */}
              <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-brand-success" /> Studio DAW & Subtitle Engine
                  </span>
                  <span className="text-[10px] font-mono text-gray-400">WaveSurfer.js + FastAPI</span>
                </div>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Real-time waveform visualization, acoustic DSP mastering presets, and frame-accurate CapCut/Premiere SRT exporter.
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-gray-500">
              <span className="flex items-center gap-1">
                Built with <Heart className="w-3 h-3 text-rose-500 fill-rose-500" /> for creators & developers
              </span>
              <button
                onClick={() => setShowCreditsModal(false)}
                className="px-4 py-1.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-xs font-semibold text-white transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
